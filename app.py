"""MVP веб-приложения для водителя такси.

Запуск:
    python3 app.py

Приложение поднимается на http://127.0.0.1:5000
Текущее состояние хранится в driver_state.json, завершённые смены —
в shift_history.json (оба файла создаются автоматически).
"""

from __future__ import annotations

import json
import math
import os
import threading
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "driver_state.json")
HISTORY_FILE = os.path.join(BASE_DIR, "shift_history.json")

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


def _read_state() -> dict:
    state = _empty_state()
    data = _read_json(DATA_FILE, None)
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
# Маршруты
# ---------------------------------------------------------------------------


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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
