"""Регрессионные тесты TAXI-HISTORY-READ-GUARD-01.

Существующая, но нечитаемая или повреждённая история смен
(shift_history.json) не должна показываться пустой и перезаписываться при
завершении смены. Отсутствующая история — по-прежнему пустая история.

Все тесты работают через обычные маршруты Flask (test_client) в отдельном
временном каталоге хранилища и только на синтетических данных. Настоящие
driver_state.json, shift_history.json и yandex_day.json рядом с app.py не
читаются и не изменяются (это проверяется в конце модуля).

Чего эти тесты НЕ доказывают: защиту записи (fsync), межпроцессную
безопасность, повторное завершение смены, транзакционность, резервные копии.

Запуск из корня репозитория:
    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import builtins
import errno
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import date
from unittest import mock

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import app as taxi_app  # noqa: E402

# Синтетическая история из двух завершённых смен (старая первой).
HISTORY_RECORDS = [
    {
        "id": "synthhist001",
        "started_at": "2026-01-01T06:00:00+00:00",
        "finished_at": "2026-01-01T14:00:00+00:00",
        "duration_minutes": 480.0,
        "distance_km": 12.5,
        "markers": 3,
        "orders_count": 1,
        "revenue": 1000.0,
        "expenses_total": 200.0,
        "profit": 800.0,
        "expenses_by_category": {"fuel": 200.0, "wash": 0.0, "food": 0.0, "fine": 0.0},
        "car_brand": "Synthetic",
        "car_plate": "S000YN",
        "orders": [{"id": "o1", "amount": 1000.0, "created_at": "2026-01-01T07:00:00+00:00"}],
        "expenses": [{"id": "e1", "amount": 200.0, "category": "fuel", "created_at": "2026-01-01T08:00:00+00:00"}],
    },
    {
        "id": "synthhist002",
        "started_at": "2026-01-02T06:00:00+00:00",
        "finished_at": "2026-01-02T10:00:00+00:00",
        "duration_minutes": 240.0,
        "distance_km": 4.0,
        "markers": 2,
        "orders_count": 0,
        "revenue": 0.0,
        "expenses_total": 0.0,
        "profit": 0.0,
        "expenses_by_category": {"fuel": 0.0, "wash": 0.0, "food": 0.0, "fine": 0.0},
        "car_brand": "Synthetic",
        "car_plate": "S000YN",
        "orders": [],
        "expenses": [],
    },
]
HISTORY_BYTES = (json.dumps(HISTORY_RECORDS, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

# Синтетическое валидное состояние текущей смены (started_at есть: чтение не пишет).
VALID_STATE = {
    "car_brand": "Synthetic",
    "car_plate": "S000YN",
    "status": "free",
    "shift": {
        "started_at": "2026-01-03T06:00:00+00:00",
        "total_meters": 150.0,
        "markers": [
            {"lat": 55.75, "lng": 37.61, "segment_m": 0.0},
            {"lat": 55.7513, "lng": 37.61, "segment_m": 150.0},
        ],
        "revenue": 500.0,
        "orders": [{"id": "ord1", "amount": 500.0, "created_at": "2026-01-03T07:00:00+00:00"}],
        "expenses": [{"id": "exp1", "amount": 50.0, "category": "food", "created_at": "2026-01-03T08:00:00+00:00"}],
    },
}
STATE_BYTES = json.dumps(VALID_STATE, ensure_ascii=False, indent=2).encode("utf-8")

# Существующая история, которую нельзя разобрать как JSON.
MALFORMED_HISTORY = {
    "truncated_array": b'[{"id": "synthhist001", "revenue": 10',
    "garbage_text": b"not json at all\n",
    "empty_file": b"",
    "whitespace_only": b" \n\t\n",
    "invalid_utf8": b'[{"car_brand": "\xff\xfe"}]',
    "deeply_nested": b"[" * 100_000 + b"]" * 100_000,
}

# Валидный JSON, но корень — не массив.
NON_LIST_HISTORY = {
    "object_root": b'{"shifts": []}\n',
    "null_root": b"null\n",
    "number_root": b"42\n",
    "string_root": b'"history"\n',
    "bool_root": b"true\n",
}

HISTORY_ROUTES = [
    ("GET", "/api/history", None),
    ("POST", "/api/shift/finish", {}),
]

FIXED_TODAY = date(2026, 1, 15)
YANDEX_DAY = "2026-01-10"
YANDEX_PAYLOAD = {
    "kind": "final",
    "amounts": {"card": "100", "cash": "0", "bonuses": "0", "tips": "0", "commission": "10", "extra_services": "0"},
}

_REAL_FILES = tuple(
    os.path.join(taxi_app.BASE_DIR, name)
    for name in ("driver_state.json", "shift_history.json", "yandex_day.json")
)
_REAL_SNAPSHOT: dict[str, bytes | None] = {}


def _file_bytes(path: str) -> bytes | None:
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except FileNotFoundError:
        return None


def setUpModule():
    for path in _REAL_FILES:
        _REAL_SNAPSHOT[path] = _file_bytes(path)


def tearDownModule():
    for path in _REAL_FILES:
        if _file_bytes(path) != _REAL_SNAPSHOT[path]:
            raise AssertionError(f"Тесты изменили настоящий файл {path}")


class _IsolatedStorageCase(unittest.TestCase):
    """Перенаправляет DATA_FILE, HISTORY_FILE и YANDEX_DAY_FILE во временный каталог."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="taxi-history-guard-")
        self.addCleanup(shutil.rmtree, self.tmpdir, True)
        self.data_file = os.path.join(self.tmpdir, "driver_state.json")
        self.history_file = os.path.join(self.tmpdir, "shift_history.json")
        self.yday_file = os.path.join(self.tmpdir, "yandex_day.json")

        for name, value in (
            ("DATA_FILE", self.data_file),
            ("HISTORY_FILE", self.history_file),
            ("YANDEX_DAY_FILE", self.yday_file),
        ):
            patcher = mock.patch.object(taxi_app, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

        today = mock.patch.object(taxi_app, "_moscow_today", return_value=FIXED_TODAY)
        today.start()
        self.addCleanup(today.stop)

        taxi_app.app.config["TESTING"] = True
        self.client = taxi_app.app.test_client()

    # -- помощники ----------------------------------------------------------

    def write_bytes(self, path: str, data: bytes) -> None:
        with open(path, "wb") as fh:
            fh.write(data)

    def remove_path(self, path: str) -> None:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.exists(path):
            os.remove(path)

    def snapshot(self) -> dict[str, bytes | None]:
        """Побайтный снимок всего каталога хранилища (файлы и подкаталоги)."""
        result: dict[str, bytes | None] = {}
        for root, dirs, files in os.walk(self.tmpdir):
            for name in dirs:
                result[os.path.relpath(os.path.join(root, name), self.tmpdir) + "/"] = None
            for name in files:
                full = os.path.join(root, name)
                result[os.path.relpath(full, self.tmpdir)] = _file_bytes(full)
        return result

    def call(self, method: str, path: str, body):
        if method == "GET":
            return self.client.get(path)
        if method == "PUT":
            return self.client.put(path, json=body)
        return self.client.post(path, json=body)

    def assert_history_fail_closed(self, method: str, path: str, body, before, during=None):
        """Маршрут отвечает 503 с общим текстом ошибки и не меняет ни байта хранилища."""
        if during is None:
            response = self.call(method, path, body)
        else:
            with during():
                response = self.call(method, path, body)
        self.assertEqual(response.status_code, 503, f"{method} {path}: {response.status_code}")
        payload = response.get_json()
        self.assertIsInstance(payload, dict)
        self.assertEqual(set(payload), {"error"}, f"{method} {path}: лишние поля {payload}")
        self.assertIn("История смен", payload["error"])
        self.assert_not_sensitive(response.get_data(as_text=True))
        self.assertEqual(self.snapshot(), before, f"{method} {path} изменил хранилище")
        return payload

    def assert_not_sensitive(self, text: str) -> None:
        """В ответе нет путей, текста исключений и содержимого файла."""
        for marker in (
            self.tmpdir,
            os.path.basename(self.tmpdir),
            taxi_app.BASE_DIR,
            "Errno",
            "Traceback",
            "JSONDecodeError",
            "UnicodeDecodeError",
            "RecursionError",
            "expected array",
            "synthhist",
        ):
            self.assertNotIn(marker, text)

    def assert_current_shift_kept(self) -> None:
        """Текущая смена не сброшена: валидное состояние читается без изменений."""
        response = self.client.get("/api/state")
        self.assertEqual(response.status_code, 200)
        shift = response.get_json()["shift"]
        self.assertEqual(shift["started_at"], VALID_STATE["shift"]["started_at"])
        self.assertEqual([order["id"] for order in shift["orders"]], ["ord1"])
        self.assertEqual(shift["revenue"], 500.0)
        self.assertEqual(len(shift["markers"]), 2)


class CorruptHistoryFailsClosedTests(_IsolatedStorageCase):
    """AC-1 / AC-2 / AC-3 / AC-5: существующая история нечитаема или неверна."""

    def _check_history_routes(self, history_bytes: bytes):
        self.write_bytes(self.data_file, STATE_BYTES)
        self.write_bytes(self.history_file, history_bytes)
        before = self.snapshot()
        errors = set()
        for method, path, body in HISTORY_ROUTES:
            with self.subTest(route=f"{method} {path}"):
                payload = self.assert_history_fail_closed(method, path, body, before)
                errors.add(payload["error"])
        # Ответ одинаковый для всех маршрутов: без подробностей о причине.
        self.assertEqual(len(errors), 1)
        self.assert_current_shift_kept()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(_file_bytes(self.data_file), STATE_BYTES)
        self.assertEqual(_file_bytes(self.history_file), history_bytes)

    def test_malformed_history(self):
        for label, data in MALFORMED_HISTORY.items():
            with self.subTest(case=label):
                self._check_history_routes(data)

    def test_non_list_root(self):
        for label, data in NON_LIST_HISTORY.items():
            with self.subTest(case=label):
                self._check_history_routes(data)

    def test_simulated_os_read_error(self):
        """Ошибка ввода-вывода при чтении существующей истории (EIO, EACCES)."""
        self.write_bytes(self.data_file, STATE_BYTES)
        self.write_bytes(self.history_file, HISTORY_BYTES)
        before = self.snapshot()
        real_open = builtins.open

        for code in (errno.EIO, errno.EACCES):
            def failing_open(file, mode="r", *args, code=code, **kwargs):
                if file == self.history_file and "r" in mode:
                    raise OSError(code, os.strerror(code), file)
                return real_open(file, mode, *args, **kwargs)

            def during(failing_open=failing_open):
                return mock.patch("builtins.open", failing_open)

            for method, path, body in HISTORY_ROUTES:
                with self.subTest(errno=errno.errorcode[code], route=f"{method} {path}"):
                    self.assert_history_fail_closed(method, path, body, before, during=during)

        self.assert_current_shift_kept()
        self.assertEqual(_file_bytes(self.data_file), STATE_BYTES)
        self.assertEqual(_file_bytes(self.history_file), HISTORY_BYTES)

    def test_real_os_error_history_path_is_directory(self):
        """Настоящая ОС-ошибка без моков: на месте файла истории каталог."""
        self.write_bytes(self.data_file, STATE_BYTES)
        os.mkdir(self.history_file)
        before = self.snapshot()
        for method, path, body in HISTORY_ROUTES:
            with self.subTest(route=f"{method} {path}"):
                self.assert_history_fail_closed(method, path, body, before)
        self.assertTrue(os.path.isdir(self.history_file))
        self.assertEqual(os.listdir(self.history_file), [])
        self.assert_current_shift_kept()

    def test_finish_with_corrupt_history_and_missing_state_writes_nothing(self):
        """История проверяется раньше, чем первый запуск успел бы создать состояние."""
        self.write_bytes(self.history_file, b"{broken")
        before = self.snapshot()
        self.assert_history_fail_closed("POST", "/api/shift/finish", {}, before)
        self.assertFalse(os.path.exists(self.data_file))
        self.assertEqual(_file_bytes(self.history_file), b"{broken")

    def test_finish_with_corrupt_history_and_legacy_state_writes_nothing(self):
        """Legacy-состояние без started_at не мигрируется, если история повреждена."""
        legacy = json.dumps({"car_brand": "Legacy", "status": "busy"}).encode("utf-8")
        self.write_bytes(self.data_file, legacy)
        self.write_bytes(self.history_file, b'{"a": 1}')
        before = self.snapshot()
        self.assert_history_fail_closed("POST", "/api/shift/finish", {}, before)
        self.assertEqual(_file_bytes(self.data_file), legacy)

    def test_corrupt_state_and_corrupt_history_finish_writes_nothing(self):
        self.write_bytes(self.data_file, b"[]")
        self.write_bytes(self.history_file, b"{oops")
        before = self.snapshot()
        response = self.client.post("/api/shift/finish", json={})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("state", response.get_json())
        self.assertEqual(self.snapshot(), before)

    def test_repeated_finish_attempts_do_not_write(self):
        self.write_bytes(self.data_file, STATE_BYTES)
        self.write_bytes(self.history_file, b"null\n")
        before = self.snapshot()
        for attempt in range(3):
            with self.subTest(attempt=attempt):
                self.assert_history_fail_closed("POST", "/api/shift/finish", {}, before)
        self.assert_current_shift_kept()

    def test_recovers_after_history_is_repaired(self):
        self.write_bytes(self.data_file, STATE_BYTES)
        self.write_bytes(self.history_file, b"{broken")
        self.assertEqual(self.client.get("/api/history").status_code, 503)
        self.assertEqual(self.client.post("/api/shift/finish", json={}).status_code, 503)

        self.write_bytes(self.history_file, HISTORY_BYTES)
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.get_json()["shifts"]], ["synthhist002", "synthhist001"])

        finish = self.client.post("/api/shift/finish", json={})
        self.assertEqual(finish.status_code, 200)
        with open(self.history_file, encoding="utf-8") as fh:
            self.assertEqual(len(json.load(fh)), 3)


class PreservedHistoryBehaviourTests(_IsolatedStorageCase):
    """AC-2 / AC-4: отсутствующая, пустая, валидная и legacy-история."""

    def test_missing_history_is_empty_and_creates_nothing(self):
        before = self.snapshot()
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"shifts": []})
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(os.path.exists(self.history_file))

    def test_empty_list_history_is_valid(self):
        self.write_bytes(self.history_file, b"[]\n")
        before = self.snapshot()
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"shifts": []})
        self.assertEqual(self.snapshot(), before)

    def test_missing_history_accepts_first_finished_shift(self):
        self.write_bytes(self.data_file, STATE_BYTES)
        response = self.client.post("/api/shift/finish", json={})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        archived = payload["archived"]
        self.assertEqual(archived["revenue"], 500.0)
        self.assertEqual(archived["orders_count"], 1)
        self.assertEqual(payload["state"]["shift"]["orders"], [])

        with open(self.history_file, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), [archived])
        with open(self.data_file, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["shift"]["orders"], [])
        self.assertEqual(sorted(os.listdir(self.tmpdir)), ["driver_state.json", "shift_history.json"])

    def test_missing_history_and_missing_state_first_finish(self):
        response = self.client.post("/api/shift/finish", json={})
        self.assertEqual(response.status_code, 200)
        with open(self.history_file, encoding="utf-8") as fh:
            history = json.load(fh)
        self.assertEqual([item["id"] for item in history], [response.get_json()["archived"]["id"]])

    def test_valid_history_appends_exactly_one_shift(self):
        self.write_bytes(self.data_file, STATE_BYTES)
        self.write_bytes(self.history_file, HISTORY_BYTES)

        response = self.client.post("/api/shift/finish", json={})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(set(payload), {"state", "archived"})
        archived = payload["archived"]
        self.assertEqual(archived["car_plate"], "S000YN")
        self.assertEqual(archived["profit"], 450.0)

        with open(self.history_file, encoding="utf-8") as fh:
            history = json.load(fh)
        self.assertEqual(history, HISTORY_RECORDS + [archived])
        with open(self.data_file, encoding="utf-8") as fh:
            state = json.load(fh)
        self.assertEqual(state["shift"]["orders"], [])
        self.assertEqual(state["car_plate"], "S000YN")
        self.assertEqual(sorted(os.listdir(self.tmpdir)), ["driver_state.json", "shift_history.json"])

        listed = self.client.get("/api/history").get_json()["shifts"]
        self.assertEqual([item["id"] for item in listed], [archived["id"], "synthhist002", "synthhist001"])

    def test_valid_history_read_is_reverse_order_and_does_not_write(self):
        self.write_bytes(self.history_file, HISTORY_BYTES)
        before = self.snapshot()
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        shifts = response.get_json()["shifts"]
        self.assertEqual([item["id"] for item in shifts], ["synthhist002", "synthhist001"])
        self.assertEqual(shifts[1]["orders"], HISTORY_RECORDS[0]["orders"])
        self.assertEqual(self.snapshot(), before)

    def test_legacy_history_keeps_current_normalisation(self):
        legacy = [
            {"id": "legacy1", "revenue": "500", "orders": "bad", "markers": -1, "orders_count": 2},
            "not-a-record",
            {"id": "legacy2", "distance_km": 3.456, "expenses": [{"id": "e"}, 5], "duration_minutes": None},
        ]
        legacy_bytes = json.dumps(legacy).encode("utf-8")
        self.write_bytes(self.history_file, legacy_bytes)
        before = self.snapshot()

        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        zeros = {"distance_km": 0.0, "revenue": 0.0, "expenses_total": 0.0, "profit": 0.0, "duration_minutes": 0.0}
        self.assertEqual(
            response.get_json()["shifts"],
            [
                {**zeros, "id": "legacy2", "distance_km": 3.46, "orders": [], "expenses": [{"id": "e"}],
                 "markers": 0, "orders_count": 0},
                {**zeros, "id": "legacy1", "revenue": 500.0, "orders": [], "expenses": [],
                 "markers": 0, "orders_count": 2},
            ],
        )
        self.assertEqual(self.snapshot(), before)

        # Завершение смены дописывает ровно одну запись и не переписывает legacy-записи.
        self.write_bytes(self.data_file, STATE_BYTES)
        finish = self.client.post("/api/shift/finish", json={})
        self.assertEqual(finish.status_code, 200)
        with open(self.history_file, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), legacy + [finish.get_json()["archived"]])


class OtherRoutesUnaffectedTests(_IsolatedStorageCase):
    """AC-4: битая история не мешает состоянию, карте, GPS и итогам дня Яндекс Про."""

    def test_corrupt_history_does_not_block_other_routes(self):
        self.write_bytes(self.data_file, STATE_BYTES)
        corrupt = b"{broken"
        self.write_bytes(self.history_file, corrupt)

        for method, path, body in (
            ("GET", "/api/state", None),
            ("GET", "/", None),
            ("POST", "/api/car", {"car_brand": "Other", "car_plate": "X111XX"}),
            ("POST", "/api/status", {"status": "busy"}),
            ("POST", "/api/markers", {"lat": 55.76, "lng": 37.62}),
            ("POST", "/api/track", {"lat": 55.77, "lng": 37.63, "new_segment": True}),
            ("POST", "/api/orders", {"amount": 300}),
            ("POST", "/api/expenses", {"amount": 40, "category": "wash"}),
            ("POST", "/api/mileage/reset", {}),
            ("PUT", f"/api/yandex-day/{YANDEX_DAY}", YANDEX_PAYLOAD),
            ("GET", f"/api/yandex-day/{YANDEX_DAY}", None),
            ("GET", "/api/yandex-day", None),
        ):
            with self.subTest(route=f"{method} {path}"):
                response = self.call(method, path, body)
                self.assertEqual(response.status_code, 200, f"{method} {path}: {response.status_code}")
                self.assertEqual(_file_bytes(self.history_file), corrupt)

        with open(self.data_file, encoding="utf-8") as fh:
            state = json.load(fh)
        self.assertEqual(state["car_plate"], "X111XX")
        self.assertEqual(state["status"], "busy")
        self.assertEqual(state["shift"]["revenue"], 800.0)
        self.assertEqual(state["shift"]["markers"], [])
        self.assertEqual(state["shift"]["started_at"], VALID_STATE["shift"]["started_at"])

    def test_validation_errors_still_return_400(self):
        self.write_bytes(self.history_file, b"{broken")
        before = self.snapshot()
        response = self.client.post("/api/orders", json={"amount": -1})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
