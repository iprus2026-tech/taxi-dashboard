"""Регрессионные тесты TAXI-STATE-READ-GUARD-01.

Существующий, но нечитаемый или повреждённый файл состояния смены не должен
подменяться пустым состоянием и перезаписываться. Отсутствующий файл —
это по-прежнему первый запуск.

Все тесты работают через обычные маршруты Flask (test_client) в отдельном
временном каталоге хранилища и только на синтетических данных. Настоящие
driver_state.json и shift_history.json рядом с app.py не читаются и не
изменяются (это проверяется в конце модуля).

Запуск из корня репозитория:
    python3 -m unittest discover -s tests -v
    python3 -m pytest tests/test_state_read_guard.py
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
from unittest import mock

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import app as taxi_app  # noqa: E402


# Синтетическая история: одна завершённая смена.
HISTORY_BYTES = (
    json.dumps(
        [
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
                "expenses": [
                    {"id": "e1", "amount": 200.0, "category": "fuel", "created_at": "2026-01-01T08:00:00+00:00"}
                ],
            }
        ],
        ensure_ascii=False,
        indent=2,
    )
    + "\n"
).encode("utf-8")

# Синтетическое валидное состояние текущей смены.
VALID_STATE = {
    "car_brand": "Synthetic",
    "car_plate": "S000YN",
    "status": "free",
    "shift": {
        "started_at": "2026-01-02T06:00:00+00:00",
        "total_meters": 150.0,
        "markers": [
            {"lat": 55.75, "lng": 37.61, "segment_m": 0.0},
            {"lat": 55.7513, "lng": 37.61, "segment_m": 150.0},
        ],
        "revenue": 500.0,
        "orders": [{"id": "ord1", "amount": 500.0, "created_at": "2026-01-02T07:00:00+00:00"}],
        "expenses": [
            {"id": "exp1", "amount": 50.0, "category": "food", "created_at": "2026-01-02T08:00:00+00:00"}
        ],
    },
}

MALFORMED_STATES = {
    "truncated_object": b'{"car_brand": "Synthetic", "shift": {"started_at": "2026-01-02T06:',
    "empty_file": b"",
    "garbage_text": b"not json at all\n",
    "invalid_utf8": b'{"car_brand": "\xff\xfe"}',
}

NON_OBJECT_STATES = {
    "array_root": b"[]\n",
    "array_of_state": b'[{"car_brand": "Synthetic"}]\n',
    "null_root": b"null\n",
    "number_root": b"42\n",
    "string_root": b'"state"\n',
    "bool_root": b"true\n",
}

# Маршруты, зависящие от состояния: (метод, путь, тело запроса).
STATE_READ_ROUTES = [
    ("GET", "/api/state", None),
    ("GET", "/", None),
]

STATE_MUTATION_ROUTES = [
    ("POST", "/api/car", {"car_brand": "Other", "car_plate": "X111XX"}),
    ("POST", "/api/status", {"status": "busy"}),
    ("POST", "/api/markers", {"lat": 55.76, "lng": 37.62}),
    ("POST", "/api/track", {"lat": 55.76, "lng": 37.62, "new_segment": True}),
    ("POST", "/api/mileage/reset", {}),
    ("POST", "/api/orders", {"amount": 300}),
    ("POST", "/api/expenses", {"amount": 40, "category": "wash"}),
    ("POST", "/api/shift/finish", {}),
]

ALL_STATE_ROUTES = STATE_READ_ROUTES + STATE_MUTATION_ROUTES

_REAL_FILES = (
    os.path.join(taxi_app.BASE_DIR, "driver_state.json"),
    os.path.join(taxi_app.BASE_DIR, "shift_history.json"),
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
    """Перенаправляет DATA_FILE и HISTORY_FILE во временный каталог."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="taxi-state-guard-")
        self.addCleanup(shutil.rmtree, self.tmpdir, True)
        self.data_file = os.path.join(self.tmpdir, "driver_state.json")
        self.history_file = os.path.join(self.tmpdir, "shift_history.json")

        for name, value in (("DATA_FILE", self.data_file), ("HISTORY_FILE", self.history_file)):
            patcher = mock.patch.object(taxi_app, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

        taxi_app.app.config["TESTING"] = True
        self.client = taxi_app.app.test_client()

    # -- помощники ----------------------------------------------------------

    def write_bytes(self, path: str, data: bytes) -> None:
        with open(path, "wb") as fh:
            fh.write(data)

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
        return self.client.post(path, json=body)

    def assert_fail_closed(self, method: str, path: str, body, before, during=None):
        """Маршрут отвечает 503 и не меняет ни одного байта хранилища.

        during — фабрика контекст-менеджера, действующего только на время
        запроса (например, имитация ОС-ошибки), но не на снимок хранилища.
        """
        if during is None:
            response = self.call(method, path, body)
        else:
            with during():
                response = self.call(method, path, body)
        self.assertEqual(response.status_code, 503, f"{method} {path}: {response.status_code}")
        payload = response.get_json()
        self.assertIsInstance(payload, dict)
        self.assertTrue(payload.get("error"))
        self.assertNotIn("state", payload)
        self.assertEqual(self.snapshot(), before, f"{method} {path} изменил хранилище")


class CorruptStateFailsClosedTests(_IsolatedStorageCase):
    """AC-1 / AC-3: повреждённый или нечитаемый файл состояния."""

    def _check_all_routes(self, state_bytes: bytes):
        self.write_bytes(self.data_file, state_bytes)
        self.write_bytes(self.history_file, HISTORY_BYTES)
        before = self.snapshot()
        for method, path, body in ALL_STATE_ROUTES:
            with self.subTest(route=f"{method} {path}"):
                self.assert_fail_closed(method, path, body, before)
        self.assertEqual(_file_bytes(self.data_file), state_bytes)
        self.assertEqual(_file_bytes(self.history_file), HISTORY_BYTES)

    def test_malformed_json(self):
        for label, data in MALFORMED_STATES.items():
            with self.subTest(case=label):
                self._check_all_routes(data)

    def test_non_object_root(self):
        for label, data in NON_OBJECT_STATES.items():
            with self.subTest(case=label):
                self._check_all_routes(data)

    def test_malformed_without_history_file_creates_nothing(self):
        self.write_bytes(self.data_file, MALFORMED_STATES["truncated_object"])
        before = self.snapshot()
        for method, path, body in ALL_STATE_ROUTES:
            with self.subTest(route=f"{method} {path}"):
                self.assert_fail_closed(method, path, body, before)
        self.assertFalse(os.path.exists(self.history_file))

    def test_simulated_os_read_error(self):
        """Ошибка ввода-вывода при чтении существующего файла (EIO, EACCES)."""
        state_bytes = json.dumps(VALID_STATE).encode("utf-8")
        self.write_bytes(self.data_file, state_bytes)
        self.write_bytes(self.history_file, HISTORY_BYTES)
        before = self.snapshot()
        real_open = builtins.open

        for code in (errno.EIO, errno.EACCES):
            def failing_open(file, mode="r", *args, code=code, **kwargs):
                if file == self.data_file and "r" in mode:
                    raise OSError(code, os.strerror(code), file)
                return real_open(file, mode, *args, **kwargs)

            def during(failing_open=failing_open):
                return mock.patch("builtins.open", failing_open)

            for method, path, body in ALL_STATE_ROUTES:
                with self.subTest(errno=errno.errorcode[code], route=f"{method} {path}"):
                    self.assert_fail_closed(method, path, body, before, during=during)

        self.assertEqual(_file_bytes(self.data_file), state_bytes)
        self.assertEqual(_file_bytes(self.history_file), HISTORY_BYTES)

    def test_real_os_error_path_is_directory(self):
        """Настоящая ОС-ошибка без моков: на месте файла каталог."""
        os.mkdir(self.data_file)
        self.write_bytes(self.history_file, HISTORY_BYTES)
        before = self.snapshot()
        for method, path, body in ALL_STATE_ROUTES:
            with self.subTest(route=f"{method} {path}"):
                self.assert_fail_closed(method, path, body, before)
        self.assertTrue(os.path.isdir(self.data_file))
        self.assertEqual(os.listdir(self.data_file), [])

    def test_recovers_after_file_is_repaired(self):
        self.write_bytes(self.data_file, b"{broken")
        self.assertEqual(self.client.get("/api/state").status_code, 503)
        self.write_bytes(self.data_file, json.dumps(VALID_STATE).encode("utf-8"))
        response = self.client.get("/api/state")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["car_plate"], "S000YN")


class PreservedBehaviourTests(_IsolatedStorageCase):
    """AC-2 / AC-3: первый запуск, валидное состояние, legacy-миграции, история."""

    def test_missing_file_first_run_initialises_state(self):
        self.assertFalse(os.path.exists(self.data_file))
        response = self.client.get("/api/state")
        self.assertEqual(response.status_code, 200)
        state = response.get_json()
        self.assertEqual(state["status"], "offline")
        self.assertEqual(state["car_brand"], "")
        self.assertEqual(state["shift"]["orders"], [])
        self.assertTrue(os.path.exists(self.data_file))

        with open(self.data_file, encoding="utf-8") as fh:
            on_disk = json.load(fh)
        self.assertEqual(on_disk["shift"]["started_at"], state["shift"]["started_at"])

        # Время начала смены стабильно между запросами.
        again = self.client.get("/api/state").get_json()
        self.assertEqual(again["shift"]["started_at"], state["shift"]["started_at"])
        self.assertFalse(os.path.exists(self.history_file))

    def test_missing_file_first_mutation_succeeds(self):
        response = self.client.post("/api/orders", json={"amount": 250})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["state"]["shift"]["revenue"], 250.0)
        with open(self.data_file, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["shift"]["revenue"], 250.0)

    def test_missing_file_index_page_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.exists(self.data_file))

    def test_valid_state_read_does_not_rewrite(self):
        state_bytes = json.dumps(VALID_STATE, ensure_ascii=False, indent=2).encode("utf-8")
        self.write_bytes(self.data_file, state_bytes)
        self.write_bytes(self.history_file, HISTORY_BYTES)
        before = self.snapshot()

        response = self.client.get("/api/state")
        self.assertEqual(response.status_code, 200)
        state = response.get_json()
        self.assertEqual(state["car_brand"], "Synthetic")
        self.assertEqual(state["status"], "free")
        self.assertEqual(state["shift"]["started_at"], VALID_STATE["shift"]["started_at"])
        self.assertEqual(state["shift"]["total_meters"], 150.0)
        self.assertEqual(self.snapshot(), before)

        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.snapshot(), before)

    def test_valid_state_mutations_persist(self):
        self.write_bytes(self.data_file, json.dumps(VALID_STATE).encode("utf-8"))
        self.write_bytes(self.history_file, HISTORY_BYTES)

        self.assertEqual(self.client.post("/api/status", json={"status": "busy"}).status_code, 200)
        self.assertEqual(self.client.post("/api/orders", json={"amount": 300}).status_code, 200)
        self.assertEqual(
            self.client.post("/api/expenses", json={"amount": 40, "category": "wash"}).status_code, 200
        )
        self.assertEqual(self.client.post("/api/markers", json={"lat": 55.76, "lng": 37.62}).status_code, 200)

        with open(self.data_file, encoding="utf-8") as fh:
            on_disk = json.load(fh)
        self.assertEqual(on_disk["status"], "busy")
        self.assertEqual(on_disk["shift"]["revenue"], 800.0)
        self.assertEqual(len(on_disk["shift"]["expenses"]), 2)
        self.assertEqual(len(on_disk["shift"]["markers"]), 3)
        self.assertEqual(on_disk["shift"]["started_at"], VALID_STATE["shift"]["started_at"])
        self.assertEqual(_file_bytes(self.history_file), HISTORY_BYTES)

    def test_valid_state_finish_shift_appends_history(self):
        self.write_bytes(self.data_file, json.dumps(VALID_STATE).encode("utf-8"))
        self.write_bytes(self.history_file, HISTORY_BYTES)

        response = self.client.post("/api/shift/finish", json={})
        self.assertEqual(response.status_code, 200)
        archived = response.get_json()["archived"]
        self.assertEqual(archived["revenue"], 500.0)
        self.assertEqual(archived["car_plate"], "S000YN")

        with open(self.history_file, encoding="utf-8") as fh:
            history = json.load(fh)
        self.assertEqual([item["id"] for item in history], ["synthhist001", archived["id"]])
        with open(self.data_file, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["shift"]["orders"], [])

    def test_legacy_object_without_shift_is_migrated(self):
        legacy = {"car_brand": "Legacy", "car_plate": "L000EG", "status": "busy"}
        self.write_bytes(self.data_file, json.dumps(legacy).encode("utf-8"))

        response = self.client.get("/api/state")
        self.assertEqual(response.status_code, 200)
        state = response.get_json()
        self.assertEqual(state["car_brand"], "Legacy")
        self.assertEqual(state["car_plate"], "L000EG")
        self.assertEqual(state["status"], "busy")

        with open(self.data_file, encoding="utf-8") as fh:
            on_disk = json.load(fh)
        self.assertEqual(on_disk["car_brand"], "Legacy")
        self.assertIsInstance(on_disk["shift"]["started_at"], str)
        self.assertTrue(on_disk["shift"]["started_at"])
        self.assertEqual(
            self.client.get("/api/state").get_json()["shift"]["started_at"],
            on_disk["shift"]["started_at"],
        )

    def test_legacy_shift_without_started_at_keeps_data(self):
        legacy = {
            "car_brand": "Legacy",
            "car_plate": "L000EG",
            "status": "free",
            "shift": {
                "markers": [{"lat": 55.75, "lng": 37.61, "segment_m": 0}],
                "orders": [{"id": "lo1", "amount": 700, "created_at": "2026-01-03T07:00:00+00:00"}],
                "expenses": [{"id": "le1", "amount": 70, "category": "fuel"}],
            },
        }
        self.write_bytes(self.data_file, json.dumps(legacy).encode("utf-8"))

        response = self.client.get("/api/state")
        self.assertEqual(response.status_code, 200)
        shift = response.get_json()["shift"]
        self.assertEqual(shift["revenue"], 700.0)
        self.assertEqual(len(shift["markers"]), 1)
        self.assertEqual(shift["expenses"][0]["category"], "fuel")

        with open(self.data_file, encoding="utf-8") as fh:
            on_disk = json.load(fh)
        self.assertTrue(on_disk["shift"]["started_at"])
        self.assertEqual(on_disk["shift"]["orders"][0]["id"], "lo1")

    def test_legacy_revenue_without_orders_is_kept(self):
        legacy = {"status": "offline", "shift": {"started_at": "2026-01-04T06:00:00+00:00", "revenue": 1234.5}}
        self.write_bytes(self.data_file, json.dumps(legacy).encode("utf-8"))
        response = self.client.get("/api/state")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["shift"]["revenue"], 1234.5)

    def test_history_route_unchanged_with_valid_files(self):
        self.write_bytes(self.history_file, HISTORY_BYTES)
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        shifts = response.get_json()["shifts"]
        self.assertEqual([item["id"] for item in shifts], ["synthhist001"])

    def test_history_route_separates_missing_from_corrupt(self):
        """Отсутствующая история — пустой список; битая или не-массив — 503.

        Раньше этот тест (test_history_route_keeps_existing_fallbacks)
        закреплял пустой список и для битой истории; TAXI-HISTORY-READ-GUARD-01
        заменил это ожидание. В обоих случаях хранилище не меняется.
        """
        for label, data in {"malformed": b"{oops", "non_list": b'{"a": 1}', "missing": None}.items():
            with self.subTest(case=label):
                if data is None:
                    if os.path.exists(self.history_file):
                        os.remove(self.history_file)
                else:
                    self.write_bytes(self.history_file, data)
                before = self.snapshot()
                response = self.client.get("/api/history")
                if data is None:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.get_json(), {"shifts": []})
                else:
                    self.assertEqual(response.status_code, 503)
                    payload = response.get_json()
                    self.assertTrue(payload.get("error"))
                    self.assertNotIn("shifts", payload)
                self.assertEqual(self.snapshot(), before)

    def test_history_route_independent_of_corrupt_state(self):
        self.write_bytes(self.data_file, b"[]")
        self.write_bytes(self.history_file, HISTORY_BYTES)
        before = self.snapshot()
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()["shifts"]), 1)
        self.assertEqual(self.snapshot(), before)

    def test_validation_errors_still_return_400_before_state_read(self):
        self.write_bytes(self.data_file, b"{broken")
        before = self.snapshot()
        response = self.client.post("/api/orders", json={"amount": -1})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
