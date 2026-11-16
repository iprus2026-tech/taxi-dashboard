"""MVP веб-приложения для водителя такси.

Запуск:
    python3 app.py

Приложение поднимается на http://127.0.0.1:5000
Текущее состояние хранится в driver_state.json, завершённые смены —
в shift_history.json (оба файла создаются автоматически). Дневные итоги
из Яндекс Про, введённые вручную, хранятся отдельно в yandex_day.json и
со сменами не смешиваются.
"""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
import threading
import uuid
from datetime import date, datetime, timedelta, timezone

from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "driver_state.json")
HISTORY_FILE = os.path.join(BASE_DIR, "shift_history.json")
YANDEX_DAY_FILE = os.path.join(BASE_DIR, "yandex_day.json")

app = Flask(__name__)

ALLOWED_STATUSES = ("free", "busy", "offline")

STATUS_LABELS = {
    "free": "Свободен",
    "busy": "На заказе",
    "offline": "Не на линии",
}

EXPENSE_CATEGORIES = {
    "fuel": "Бензин",
    "wash": "Мойка",
    "food": "Еда",
    "fine": "Штраф",
}

MAX_AMOUNT = 10_000_000.0
EARTH_RADIUS_M = 6_371_000.0

_state_lock = threading.RLock()
# Отдельная блокировка дневных итогов: они не связаны с состоянием смены.
_yandex_day_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Время и числа
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _to_float(value) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _now_from_iso(value: str | None) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Расстояние по прямой между двумя точками, в метрах."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(a)))


# ---------------------------------------------------------------------------
# Состояние смены
# ---------------------------------------------------------------------------


def _new_shift() -> dict:
    return {
        "started_at": _now_iso(),
        "total_meters": 0.0,
        "markers": [],
        "revenue": 0.0,
        "orders": [],
        "expenses": [],
    }


def _normalise_marker(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None

    lat = _to_float(raw.get("lat"))
    lng = _to_float(raw.get("lng"))
    if lat is None or lng is None:
        return None
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
        return None

    segment = _to_float(raw.get("segment_m"))
    if segment is None or segment < 0:
        segment = 0.0

    marker = {
        "lat": round(lat, 6),
        "lng": round(lng, 6),
        "segment_m": round(min(segment, 100_000.0), 1),
    }
    if raw.get("break") is True:
        # Разрыв маршрута: новая сессия трека, расстояние не начисляется.
        marker["break"] = True
        marker["segment_m"] = 0.0

    return marker


def _normalise_operation(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None

    amount = _to_float(raw.get("amount"))
    if amount is None or amount <= 0 or amount > MAX_AMOUNT:
        return None

    created_at = raw.get("created_at")
    if not isinstance(created_at, str) or not created_at:
        created_at = _now_iso()

    return {
        "id": str(raw.get("id") or uuid.uuid4().hex[:12]),
        "amount": round(amount, 2),
        "created_at": created_at,
    }


def _normalise_expense(raw) -> dict | None:
    operation = _normalise_operation(raw)
    if operation is None:
        return None

    category = raw.get("category")
    if category not in EXPENSE_CATEGORIES:
        return None

    operation["category"] = category
    return operation


def _normalise_shift(raw) -> dict:
    shift = _new_shift()
    if not isinstance(raw, dict):
        return shift

    started_at = raw.get("started_at")
    if isinstance(started_at, str) and started_at:
        shift["started_at"] = started_at

    markers = []
    if isinstance(raw.get("markers"), list):
        for item in raw["markers"]:
            marker = _normalise_marker(item)
            if marker is not None:
                markers.append(marker)

    shift["markers"] = markers
    shift["total_meters"] = round(sum(marker["segment_m"] for marker in markers), 1)

    orders = []
    if isinstance(raw.get("orders"), list):
        for item in raw["orders"]:
            order = _normalise_operation(item)
            if order is not None:
                orders.append(order)
    shift["orders"] = orders

    expenses = []
    if isinstance(raw.get("expenses"), list):
        for item in raw["expenses"]:
            expense = _normalise_expense(item)
            if expense is not None:
                expenses.append(expense)
    shift["expenses"] = expenses

    if orders:
        # Выручка всегда пересчитывается по списку заказов.
        shift["revenue"] = round(sum(order["amount"] for order in orders), 2)
    else:
        revenue = _to_float(raw.get("revenue"))
        if revenue is not None and revenue >= 0:
            shift["revenue"] = round(revenue, 2)

    return shift


def _empty_state() -> dict:
    return {
        "car_brand": "",
        "car_plate": "",
        "status": "offline",
        "shift": _new_shift(),
    }


def _read_json(path: str, fallback):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, OSError, ValueError):
        return fallback


def _write_json(path: str, data) -> None:
    """Атомарная запись JSON, чтобы файл не остался битым."""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


class StateReadError(Exception):
    """Файл состояния есть, но прочитать его как JSON-объект не удалось."""


def _load_state_file() -> dict | None:
    """Читает DATA_FILE строго.

    None — только если файла нет (первый запуск). Любая другая ошибка
    чтения, битый JSON или корень не-объект — StateReadError: подменять
    такой файл пустым состоянием и перезаписывать его нельзя.
    """
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise StateReadError(f"{type(exc).__name__}: {exc}") from exc

    if not isinstance(data, dict):
        raise StateReadError(f"JSON root is {type(data).__name__}, expected object")
    return data


def _read_state() -> dict:
    state = _empty_state()
    data = _load_state_file()
    needs_persist = True

    if isinstance(data, dict):
        brand = data.get("car_brand")
        if isinstance(brand, str):
            state["car_brand"] = brand[:80]

        plate = data.get("car_plate")
        if isinstance(plate, str):
            state["car_plate"] = plate[:20]

        if data.get("status") in ALLOWED_STATUSES:
            state["status"] = data["status"]

        raw_shift = data.get("shift")
        needs_persist = (
            not isinstance(raw_shift, dict)
            or not isinstance(raw_shift.get("started_at"), str)
            or not raw_shift.get("started_at")
        )
        state["shift"] = _normalise_shift(raw_shift)

    if needs_persist:
        # Первый запуск или старый формат файла: фиксируем смену на диске,
        # чтобы время её начала не менялось от запроса к запросу.
        try:
            _write_state(state)
        except OSError:
            pass

    return state


def _write_state(state: dict) -> None:
    _write_json(DATA_FILE, state)


def _shift_totals(shift: dict) -> dict:
    revenue = round(sum(order["amount"] for order in shift["orders"]), 2)
    if shift["orders"]:
        # Держим поле revenue согласованным с заказами.
        shift["revenue"] = revenue
    else:
        revenue = round(shift.get("revenue", 0.0), 2)

    expenses_total = round(sum(expense["amount"] for expense in shift["expenses"]), 2)
    return {
        "revenue": revenue,
        "expenses_total": expenses_total,
        "profit": round(revenue - expenses_total, 2),
    }


def _archive_shift(shift: dict, car_brand: str = "", car_plate: str = "") -> dict:
    """Собирает подробную запись смены для shift_history.json."""
    finished_at = _now_iso()
    started = _now_from_iso(shift.get("started_at"))
    finished = _now_from_iso(finished_at)

    duration_minutes = None
    if started is not None and finished is not None:
        duration_minutes = round(max(0.0, (finished - started).total_seconds()) / 60.0, 1)

    totals = _shift_totals(shift)

    expenses_by_category = {key: 0.0 for key in EXPENSE_CATEGORIES}
    for expense in shift["expenses"]:
        expenses_by_category[expense["category"]] = round(
            expenses_by_category[expense["category"]] + expense["amount"], 2
        )

    return {
        "id": uuid.uuid4().hex[:12],
        "started_at": shift.get("started_at"),
        "finished_at": finished_at,
        "duration_minutes": duration_minutes,
        "distance_km": round(shift["total_meters"] / 1000.0, 2),
        "markers": len(shift["markers"]),
        "orders_count": len(shift["orders"]),
        "revenue": totals["revenue"],
        "expenses_total": totals["expenses_total"],
        "profit": totals["profit"],
        "expenses_by_category": expenses_by_category,
        "car_brand": car_brand,
        "car_plate": car_plate,
        # Детальный журнал: каждая операция с точным временем.
        "orders": [dict(order) for order in shift["orders"]],
        "expenses": [dict(expense) for expense in shift["expenses"]],
    }


def _append_history(record: dict) -> None:
    history = _read_json(HISTORY_FILE, [])
    if not isinstance(history, list):
        history = []
    history.append(record)
    _write_json(HISTORY_FILE, history)


def _normalise_history_record(raw) -> dict | None:
    """Приводит старую или частично повреждённую запись к безопасному виду."""
    if not isinstance(raw, dict):
        return None

    record = dict(raw)
    record["orders"] = (
        [item for item in raw["orders"] if isinstance(item, dict)]
        if isinstance(raw.get("orders"), list)
        else []
    )
    record["expenses"] = (
        [item for item in raw["expenses"] if isinstance(item, dict)]
        if isinstance(raw.get("expenses"), list)
        else []
    )

    for key in ("distance_km", "revenue", "expenses_total", "profit", "duration_minutes"):
        value = _to_float(record.get(key))
        record[key] = round(value, 2) if value is not None else 0.0

    for key in ("markers", "orders_count"):
        value = record.get(key)
        record[key] = int(value) if isinstance(value, int) and value >= 0 else 0

    return record


def _parse_amount(payload: dict) -> float | None:
    amount = _to_float(payload.get("amount"))
    if amount is None or amount <= 0 or amount > MAX_AMOUNT:
        return None
    return round(amount, 2)


# ---------------------------------------------------------------------------
# Итог дня из Яндекс Про: ручная сверка, отдельное хранилище
# ---------------------------------------------------------------------------
#
# Водитель переписывает дневной отчёт Яндекс Про с планшета. Снимок хранится
# по календарной дате Москвы в yandex_day.json и никак не связан со сменой:
# он не добавляет заказов, не меняет выручку смены и не попадает в историю.
# Все суммы хранятся и считаются в целых копейках.

# Москва живёт по UTC+3 без перехода на летнее время с 2014 года.
MOSCOW_TZ = timezone(timedelta(hours=3), "MSK")

YANDEX_DAY_STORE_VERSION = 1
YANDEX_DAY_MIN_DATE = date(2000, 1, 1)

YANDEX_DAY_KINDS = {
    "partial": "Промежуточный срез",
    "final": "Итог дня",
}

# Поступления: прибавляются к выручке дня.
YANDEX_DAY_INCOME_FIELDS = ("card", "cash", "bonuses", "tips")
# Удержания сервиса: вычитаются из выручки дня.
YANDEX_DAY_DEDUCTION_FIELDS = ("commission", "extra_services")
YANDEX_DAY_FIELDS = YANDEX_DAY_INCOME_FIELDS + YANDEX_DAY_DEDUCTION_FIELDS

YANDEX_DAY_FIELD_LABELS = {
    "card": "Картой",
    "cash": "Наличными",
    "bonuses": "Бонусы",
    "tips": "Чаевые",
    "commission": "Комиссия сервиса с НДС",
    "extra_services": "Дополнительные услуги",
}

# Не больше 10 млн ₽ в одном поле, как и у заказов и расходов (MAX_AMOUNT).
YANDEX_DAY_MAX_KOPECKS = 1_000_000_000

_DAY_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_AMOUNT_RE = re.compile(r"([0-9]{1,8})(?:[.,]([0-9]{1,2}))?")


class YandexDayInputError(ValueError):
    """Некорректная дата или сумма во входных данных; ничего не пишется."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field


class YandexDayStoreError(Exception):
    """Файл дневных итогов есть, но прочитать или разобрать его нельзя."""


class YandexDayWriteError(Exception):
    """Новый файл дневных итогов записать не удалось; старый не тронут."""


def _moscow_today() -> date:
    return datetime.now(MOSCOW_TZ).date()


def _parse_yandex_day(value) -> str:
    """Проверяет календарную дату вида ГГГГ-ММ-ДД, не позже сегодня по Москве."""
    if not isinstance(value, str) or not _DAY_RE.fullmatch(value):
        raise YandexDayInputError("Дата должна быть в формате ГГГГ-ММ-ДД.", "date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise YandexDayInputError("Такой календарной даты нет.", "date") from None
    if parsed < YANDEX_DAY_MIN_DATE:
        raise YandexDayInputError("Дата слишком ранняя.", "date")
    if parsed > _moscow_today():
        raise YandexDayInputError("Дата ещё не наступила по московскому времени.", "date")
    return value


def _parse_kopecks(value, field: str) -> int:
    """Неотрицательная сумма в рублях, до двух знаков после запятой или точки.

    Возвращает точное число копеек без float-арифметики.
    """
    label = YANDEX_DAY_FIELD_LABELS[field]
    if isinstance(value, bool) or value is None:
        text = None
    elif isinstance(value, int):
        text = str(value) if value >= 0 else None
    elif isinstance(value, float):
        # repr даёт кратчайшую запись числа: 10.5 → "10.5", 0.1 + 0.2 → длинная
        # дробь, которая не пройдёт проверку двух знаков.
        text = repr(value) if math.isfinite(value) and value >= 0 else None
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = None

    match = _AMOUNT_RE.fullmatch(text) if text is not None else None
    if match is None:
        raise YandexDayInputError(
            f"«{label}»: нужна неотрицательная сумма, не больше двух знаков после запятой.",
            field,
        )

    rubles, fraction = match.group(1), match.group(2) or ""
    kopecks = int(rubles) * 100 + int(fraction.ljust(2, "0"))
    if kopecks > YANDEX_DAY_MAX_KOPECKS:
        raise YandexDayInputError(f"«{label}»: сумма больше 10 000 000 ₽.", field)
    return kopecks


def _parse_yandex_day_payload(payload) -> tuple[str, dict]:
    """Проверяет тело запроса целиком до любого обращения к хранилищу."""
    if not isinstance(payload, dict):
        raise YandexDayInputError("Нужен JSON-объект с полями kind и amounts.")

    kind = payload.get("kind")
    if kind not in YANDEX_DAY_KINDS:
        raise YandexDayInputError(
            "Укажите, это промежуточный срез (partial) или итог дня (final).", "kind"
        )

    raw_amounts = payload.get("amounts")
    if not isinstance(raw_amounts, dict):
        raise YandexDayInputError("Нужен объект amounts со всеми суммами.", "amounts")

    unknown = sorted(key for key in raw_amounts if key not in YANDEX_DAY_FIELDS)
    if unknown:
        raise YandexDayInputError(f"Неизвестные поля сумм: {', '.join(map(str, unknown))}.", "amounts")

    amounts = {}
    for field in YANDEX_DAY_FIELDS:
        if field not in raw_amounts:
            raise YandexDayInputError(
                f"«{YANDEX_DAY_FIELD_LABELS[field]}»: сумма не указана.", field
            )
        amounts[field] = _parse_kopecks(raw_amounts[field], field)

    return kind, amounts


def _format_kopecks(kopecks: int) -> str:
    sign = "-" if kopecks < 0 else ""
    kopecks = abs(kopecks)
    return f"{sign}{kopecks // 100}.{kopecks % 100:02d}"


def _validate_yandex_entry(key, entry) -> None:
    if not isinstance(key, str) or not _DAY_RE.fullmatch(key):
        raise YandexDayStoreError(f"bad date key {key!r}")
    try:
        date.fromisoformat(key)
    except ValueError:
        raise YandexDayStoreError(f"bad date key {key!r}") from None
    if not isinstance(entry, dict):
        raise YandexDayStoreError(f"{key}: entry is {type(entry).__name__}, expected object")
    if entry.get("date") != key:
        raise YandexDayStoreError(f"{key}: date field does not match key")
    if entry.get("kind") not in YANDEX_DAY_KINDS:
        raise YandexDayStoreError(f"{key}: bad kind")
    if not isinstance(entry.get("updated_at"), str):
        raise YandexDayStoreError(f"{key}: bad updated_at")
    if "created_at" in entry and not isinstance(entry["created_at"], str):
        raise YandexDayStoreError(f"{key}: bad created_at")
    amounts = entry.get("amounts_kopecks")
    if not isinstance(amounts, dict):
        raise YandexDayStoreError(f"{key}: amounts_kopecks is not an object")
    for field in YANDEX_DAY_FIELDS:
        value = amounts.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= YANDEX_DAY_MAX_KOPECKS
        ):
            raise YandexDayStoreError(f"{key}: bad amount {field}")


def _load_yandex_store() -> dict | None:
    """Читает YANDEX_DAY_FILE строго.

    None — только если файла нет (ещё ничего не сохраняли). Ошибка чтения,
    битый JSON, чужая версия или неверная запись — YandexDayStoreError:
    такой файл нельзя подменять пустым и перезаписывать.
    """
    try:
        with open(YANDEX_DAY_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise YandexDayStoreError(f"{type(exc).__name__}: {exc}") from exc

    if not isinstance(data, dict):
        raise YandexDayStoreError(f"JSON root is {type(data).__name__}, expected object")
    version = data.get("version")
    if isinstance(version, bool) or version != YANDEX_DAY_STORE_VERSION:
        raise YandexDayStoreError(f"unsupported version {version!r}")
    days = data.get("days")
    if not isinstance(days, dict):
        raise YandexDayStoreError("days is not an object")
    for key, entry in days.items():
        _validate_yandex_entry(key, entry)
    return data


def _write_yandex_store(data: dict) -> None:
    """Атомарная замена: временный файл в том же каталоге, fsync, os.replace."""
    directory = os.path.dirname(YANDEX_DAY_FILE) or "."
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(prefix=".yandex_day.", suffix=".tmp", dir=directory)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, YANDEX_DAY_FILE)
        tmp_path = None
    except OSError as exc:
        raise YandexDayWriteError(f"{type(exc).__name__}: {exc}") from exc
    finally:
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def _yandex_snapshot_view(entry: dict) -> dict:
    """Ответ API по одной дате: суммы в копейках и строками, выручка дня."""
    kopecks = {field: entry["amounts_kopecks"][field] for field in YANDEX_DAY_FIELDS}
    income = sum(kopecks[field] for field in YANDEX_DAY_INCOME_FIELDS)
    deductions = sum(kopecks[field] for field in YANDEX_DAY_DEDUCTION_FIELDS)
    proceeds = income - deductions
    return {
        "date": entry["date"],
        "kind": entry["kind"],
        "kind_label": YANDEX_DAY_KINDS[entry["kind"]],
        "amounts_kopecks": kopecks,
        "amounts": {field: _format_kopecks(value) for field, value in kopecks.items()},
        "income_kopecks": income,
        "deductions_kopecks": deductions,
        "proceeds_kopecks": proceeds,
        "proceeds": _format_kopecks(proceeds),
        "created_at": entry.get("created_at") or entry["updated_at"],
        "updated_at": entry["updated_at"],
    }


# ---------------------------------------------------------------------------
# Маршруты
# ---------------------------------------------------------------------------


@app.errorhandler(StateReadError)
def handle_state_read_error(exc: StateReadError):
    """Файл состояния повреждён или недоступен: ничего не пишем, отвечаем 503."""
    app.logger.error("Состояние смены не прочитано (%s): %s", DATA_FILE, exc)
    return (
        jsonify(
            {
                "error": "Файл состояния смены повреждён или недоступен. "
                "Данные не изменены; нужна ручная проверка driver_state.json.",
            }
        ),
        503,
    )


@app.get("/")
def index():
    """Главная страница с картой, пробегом и деньгами."""
    with _state_lock:
        state = _read_state()
    return render_template(
        "index.html",
        state=state,
        status_labels=STATUS_LABELS,
        expense_categories=EXPENSE_CATEGORIES,
    )


@app.get("/api/state")
def api_state():
    """Текущее состояние: авто, статус, смена (пробег, метки, деньги)."""
    with _state_lock:
        state = _read_state()
    return jsonify(state)


@app.get("/api/history")
def api_history():
    """Завершённые смены с детальным журналом операций, новые сверху."""
    with _state_lock:
        records = _read_json(HISTORY_FILE, [])

    if not isinstance(records, list):
        records = []

    normalized = [
        record
        for record in (_normalise_history_record(item) for item in records)
        if record is not None
    ]
    normalized.reverse()

    return jsonify({"shifts": normalized})


@app.post("/api/car")
def api_car():
    """Сохраняет марку автомобиля и госномер."""
    payload = request.get_json(silent=True) or {}

    brand = str(payload.get("car_brand", "")).strip()
    plate = str(payload.get("car_plate", "")).strip()

    if len(brand) > 80:
        return jsonify({"error": "Марка автомобиля слишком длинная (максимум 80 символов)."}), 400
    if len(plate) > 20:
        return jsonify({"error": "Госномер слишком длинный (максимум 20 символов)."}), 400

    with _state_lock:
        state = _read_state()
        state["car_brand"] = brand
        state["car_plate"] = plate
        _write_state(state)

    return jsonify(state)


@app.post("/api/status")
def api_status():
    """Сохраняет статус водителя: free / busy / offline."""
    payload = request.get_json(silent=True) or {}
    status = payload.get("status")

    if status not in ALLOWED_STATUSES:
        return jsonify({"error": "Неизвестный статус. Допустимо: free, busy, offline."}), 400

    with _state_lock:
        state = _read_state()
        state["status"] = status
        _write_state(state)

    return jsonify(state)


@app.post("/api/track")
@app.post("/api/markers")
def api_add_marker():
    """Добавляет точку GPS-трека, считает отрезок и общий пробег."""
    payload = request.get_json(silent=True) or {}
    new_segment = payload.get("new_segment") is True

    lat = _to_float(payload.get("lat"))
    lng = _to_float(payload.get("lng"))

    if lat is None or lng is None:
        return jsonify({"error": "Нужны корректные координаты lat и lng."}), 400
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
        return jsonify({"error": "Координаты вне допустимого диапазона."}), 400

    with _state_lock:
        state = _read_state()
        shift = state["shift"]

        segment = 0.0
        if shift["markers"] and not new_segment:
            previous = shift["markers"][-1]
            segment = _haversine_meters(previous["lat"], previous["lng"], lat, lng)

        marker = {
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "segment_m": round(segment, 1),
        }
        if new_segment:
            marker["break"] = True

        shift["markers"].append(marker)
        shift["total_meters"] = round(
            sum(marker["segment_m"] for marker in shift["markers"]), 1
        )
        _write_state(state)

    return jsonify(
        {
            "state": state,
            "segment_m": (
                round(segment, 1)
                if len(state["shift"]["markers"]) > 1 and not new_segment
                else None
            ),
        }
    )


@app.post("/api/mileage/reset")
def api_reset_mileage():
    """Очищает трек и пробег, не трогая деньги и время начала смены."""
    with _state_lock:
        state = _read_state()
        state["shift"]["markers"] = []
        state["shift"]["total_meters"] = 0.0
        _write_state(state)

    return jsonify({"state": state})


@app.post("/api/orders")
def api_add_order():
    """Добавляет заказ и прибавляет сумму к выручке."""
    payload = request.get_json(silent=True) or {}
    amount = _parse_amount(payload)

    if amount is None:
        return jsonify({"error": "Сумма заказа должна быть положительным числом."}), 400

    with _state_lock:
        state = _read_state()
        shift = state["shift"]
        shift["orders"].append(
            {
                "id": uuid.uuid4().hex[:12],
                "amount": amount,
                "created_at": _now_iso(),
            }
        )
        shift["revenue"] = round(
            sum(order["amount"] for order in shift["orders"]), 2
        )
        _write_state(state)

    return jsonify({"state": state})


@app.post("/api/expenses")
def api_add_expense():
    """Добавляет расход с категорией: бензин, мойка, еда или штраф."""
    payload = request.get_json(silent=True) or {}
    amount = _parse_amount(payload)
    category = payload.get("category")

    if amount is None:
        return jsonify({"error": "Сумма расхода должна быть положительным числом."}), 400
    if category not in EXPENSE_CATEGORIES:
        return jsonify(
            {
                "error": "Неизвестная категория расхода. Допустимо: "
                + ", ".join(EXPENSE_CATEGORIES)
                + "."
            }
        ), 400

    with _state_lock:
        state = _read_state()
        state["shift"]["expenses"].append(
            {
                "id": uuid.uuid4().hex[:12],
                "amount": amount,
                "category": category,
                "created_at": _now_iso(),
            }
        )
        _write_state(state)

    return jsonify({"state": state})


@app.post("/api/shift/finish")
def api_finish_shift():
    """Архивирует текущую смену в историю и начинает новую."""
    with _state_lock:
        state = _read_state()
        archived = _archive_shift(
            state["shift"],
            car_brand=state.get("car_brand", ""),
            car_plate=state.get("car_plate", ""),
        )
        _append_history(archived)

        state["shift"] = _new_shift()
        _write_state(state)

    return jsonify({"state": state, "archived": archived})


# ---------------------------------------------------------------------------
# Маршруты: итог дня из Яндекс Про
# ---------------------------------------------------------------------------


@app.errorhandler(YandexDayInputError)
def handle_yandex_day_input_error(exc: YandexDayInputError):
    return jsonify({"error": str(exc), "field": exc.field}), 400


@app.errorhandler(YandexDayStoreError)
def handle_yandex_day_store_error(exc: YandexDayStoreError):
    """Файл дневных итогов повреждён или недоступен: ничего не пишем, 503."""
    app.logger.error("Дневные итоги не прочитаны (%s): %s", YANDEX_DAY_FILE, exc)
    return (
        jsonify(
            {
                "error": "Файл дневных итогов Яндекс Про повреждён или недоступен. "
                "Данные не изменены; нужна ручная проверка yandex_day.json.",
                "store_state": "damaged",
            }
        ),
        503,
    )


@app.errorhandler(YandexDayWriteError)
def handle_yandex_day_write_error(exc: YandexDayWriteError):
    app.logger.error("Дневной итог не сохранён (%s): %s", YANDEX_DAY_FILE, exc)
    return (
        jsonify(
            {
                "error": "Не удалось сохранить итог дня: ошибка записи на диск. "
                "Ранее сохранённые данные не изменены.",
                "store_state": "write_failed",
            }
        ),
        500,
    )


@app.get("/api/yandex-day")
def api_yandex_days():
    """Все сохранённые дневные итоги, новые даты сверху."""
    with _yandex_day_lock:
        store = _load_yandex_store()

    days = store["days"] if store is not None else {}
    snapshots = [_yandex_snapshot_view(days[key]) for key in sorted(days, reverse=True)]
    return jsonify(
        {
            "store_state": "ok" if store is not None else "missing",
            "today": _moscow_today().isoformat(),
            "days": snapshots,
        }
    )


@app.get("/api/yandex-day/<day>")
def api_yandex_day(day: str):
    """Дневной итог за одну дату или null, если за неё ещё ничего не сохраняли."""
    day = _parse_yandex_day(day)
    with _yandex_day_lock:
        store = _load_yandex_store()

    entry = store["days"].get(day) if store is not None else None
    return jsonify(
        {
            "store_state": "ok" if store is not None else "missing",
            "date": day,
            "snapshot": _yandex_snapshot_view(entry) if entry is not None else None,
        }
    )


@app.put("/api/yandex-day/<day>")
def api_save_yandex_day(day: str):
    """Сохраняет или заменяет дневной итог за одну дату; остальные даты не трогает."""
    day = _parse_yandex_day(day)
    kind, amounts = _parse_yandex_day_payload(request.get_json(silent=True))

    with _yandex_day_lock:
        store = _load_yandex_store()
        if store is None:
            store = {"version": YANDEX_DAY_STORE_VERSION, "days": {}}

        previous = store["days"].get(day)
        now = _now_iso()
        entry = {
            "date": day,
            "kind": kind,
            "amounts_kopecks": amounts,
            "created_at": (previous.get("created_at") or previous["updated_at"]) if previous else now,
            "updated_at": now,
        }
        store["days"][day] = entry
        _write_yandex_store(store)

    return jsonify(
        {
            "store_state": "ok",
            "replaced": previous is not None,
            "snapshot": _yandex_snapshot_view(entry),
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
