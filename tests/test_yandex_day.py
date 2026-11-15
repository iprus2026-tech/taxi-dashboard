"""Тесты TAXI-YANDEX-DAY-01: итог дня из Яндекс Про.

Дневной снимок вводится вручную, хранится по московской дате в отдельном
файле и не должен влиять на заказы, выручку смены и историю смен.

Все тесты работают через маршруты Flask (test_client) в отдельном временном
каталоге хранилища и только на синтетических данных. Настоящие
driver_state.json, shift_history.json и yandex_day.json рядом с app.py не
читаются и не изменяются (это проверяется в конце модуля).

Запуск из корня репозитория:
    python3 -m unittest discover -s tests -v
    python3 -m pytest tests/test_yandex_day.py
"""

from __future__ import annotations

import builtins
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import date
from unittest import mock

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import app as taxi_app  # noqa: E402

# Фиксированное «сегодня» по Москве: тесты не зависят от текущей даты.
FIXED_TODAY = date(2026, 1, 15)
DAY_A = "2026-01-10"
DAY_B = "2026-01-11"

# Синтетический пример из AC-2: 1000 + 200 + 20 + 10.50 - 210 - 5.25 = 1015.25.
EXAMPLE_AMOUNTS = {
    "card": "1000",
    "cash": "200",
    "bonuses": "20",
    "tips": "10.50",
    "commission": "210",
    "extra_services": "5.25",
}
EXAMPLE_KOPECKS = {
    "card": 100000,
    "cash": 20000,
    "bonuses": 2000,
    "tips": 1050,
    "commission": 21000,
    "extra_services": 525,
}
EXAMPLE_PROCEEDS_KOPECKS = 101525

ZERO_AMOUNTS = {field: "0" for field in taxi_app.YANDEX_DAY_FIELDS}

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


def _amounts(**overrides) -> dict:
    result = dict(EXAMPLE_AMOUNTS)
    result.update(overrides)
    return result


class _IsolatedCase(unittest.TestCase):
    """Перенаправляет все файлы хранилища во временный каталог."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="taxi-yandex-day-")
        self.addCleanup(shutil.rmtree, self.tmpdir, True)
        self.data_file = os.path.join(self.tmpdir, "driver_state.json")
        self.history_file = os.path.join(self.tmpdir, "shift_history.json")
        self.yday_file = os.path.join(self.tmpdir, "yandex_day.json")

        patches = (
            mock.patch.object(taxi_app, "DATA_FILE", self.data_file),
            mock.patch.object(taxi_app, "HISTORY_FILE", self.history_file),
            mock.patch.object(taxi_app, "YANDEX_DAY_FILE", self.yday_file),
            mock.patch.object(taxi_app, "_moscow_today", return_value=FIXED_TODAY),
        )
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

        taxi_app.app.config["TESTING"] = True
        self.client = taxi_app.app.test_client()

    # -- помощники ----------------------------------------------------------

    def put_day(self, day: str, kind: str = "partial", amounts: dict | None = None):
        body = {"kind": kind, "amounts": dict(EXAMPLE_AMOUNTS if amounts is None else amounts)}
        return self.client.put(f"/api/yandex-day/{day}", json=body)

    def get_day(self, day: str):
        return self.client.get(f"/api/yandex-day/{day}")

    def stored(self) -> dict:
        with open(self.yday_file, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def write_bytes(self, path: str, data: bytes) -> None:
        with open(path, "wb") as fh:
            fh.write(data)

    def snapshot_dir(self) -> dict[str, bytes | None]:
        result: dict[str, bytes | None] = {}
        for root, dirs, files in os.walk(self.tmpdir):
            for name in dirs:
                result[os.path.relpath(os.path.join(root, name), self.tmpdir) + "/"] = None
            for name in files:
                full = os.path.join(root, name)
                result[os.path.relpath(full, self.tmpdir)] = _file_bytes(full)
        return result

    def assert_no_temp_files(self):
        leftovers = [name for name in os.listdir(self.tmpdir) if name.endswith(".tmp")]
        self.assertEqual(leftovers, [])


# ---------------------------------------------------------------------------
# Создание, чтение, правка
# ---------------------------------------------------------------------------


class CreateReadEditTests(_IsolatedCase):
    def test_missing_store_reads_as_empty_without_creating_file(self):
        listing = self.client.get("/api/yandex-day")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.get_json()["store_state"], "missing")
        self.assertEqual(listing.get_json()["days"], [])
        self.assertEqual(listing.get_json()["today"], FIXED_TODAY.isoformat())

        single = self.get_day(DAY_A)
        self.assertEqual(single.status_code, 200)
        self.assertEqual(single.get_json(), {"store_state": "missing", "date": DAY_A, "snapshot": None})

        self.assertFalse(os.path.exists(self.yday_file))

    def test_create_then_read(self):
        response = self.put_day(DAY_A)
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["store_state"], "ok")
        self.assertFalse(payload["replaced"])

        snapshot = payload["snapshot"]
        self.assertEqual(snapshot["date"], DAY_A)
        self.assertEqual(snapshot["kind"], "partial")
        self.assertEqual(snapshot["amounts_kopecks"], EXAMPLE_KOPECKS)
        self.assertEqual(snapshot["proceeds_kopecks"], EXAMPLE_PROCEEDS_KOPECKS)
        self.assertEqual(snapshot["proceeds"], "1015.25")

        read = self.get_day(DAY_A).get_json()
        self.assertEqual(read["store_state"], "ok")
        self.assertEqual(read["snapshot"], snapshot)
        self.assert_no_temp_files()

    def test_edit_replaces_same_date_and_keeps_created_at(self):
        first = self.put_day(DAY_A).get_json()["snapshot"]

        with mock.patch.object(taxi_app, "_now_iso", return_value="2026-01-10T20:00:00+00:00"):
            response = self.put_day(DAY_A, amounts=_amounts(tips="99.99"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["replaced"])

        edited = self.get_day(DAY_A).get_json()["snapshot"]
        self.assertEqual(edited["amounts_kopecks"]["tips"], 9999)
        self.assertEqual(edited["proceeds_kopecks"], EXAMPLE_PROCEEDS_KOPECKS - 1050 + 9999)
        self.assertEqual(edited["created_at"], first["created_at"])
        self.assertEqual(edited["updated_at"], "2026-01-10T20:00:00+00:00")
        self.assertEqual(list(self.stored()["days"]), [DAY_A])

    def test_repeated_identical_saves_keep_one_snapshot_per_date(self):
        for _ in range(5):
            self.assertEqual(self.put_day(DAY_A).status_code, 200)

        days = self.stored()["days"]
        self.assertEqual(list(days), [DAY_A])
        listing = self.client.get("/api/yandex-day").get_json()["days"]
        self.assertEqual(len(listing), 1)
        self.assertEqual(listing[0]["proceeds_kopecks"], EXAMPLE_PROCEEDS_KOPECKS)

    def test_two_dates_are_independent(self):
        self.put_day(DAY_A, "final")
        self.put_day(DAY_B, "partial", _amounts(card="500"))
        day_b_before = self.stored()["days"][DAY_B]

        self.put_day(DAY_A, "final", _amounts(cash="0"))

        self.assertEqual(self.stored()["days"][DAY_B], day_b_before)
        self.assertEqual(self.get_day(DAY_A).get_json()["snapshot"]["amounts_kopecks"]["cash"], 0)
        self.assertEqual(self.get_day(DAY_B).get_json()["snapshot"]["amounts_kopecks"]["card"], 50000)

        listing = self.client.get("/api/yandex-day").get_json()["days"]
        self.assertEqual([item["date"] for item in listing], [DAY_B, DAY_A])

    def test_partial_then_final(self):
        partial = self.put_day(DAY_A, "partial", _amounts(card="600")).get_json()["snapshot"]
        self.assertEqual(partial["kind"], "partial")
        self.assertEqual(partial["kind_label"], "Промежуточный срез")

        final = self.put_day(DAY_A, "final").get_json()["snapshot"]
        self.assertEqual(final["kind"], "final")
        self.assertEqual(final["kind_label"], "Итог дня")

        read = self.get_day(DAY_A).get_json()["snapshot"]
        self.assertEqual(read["kind"], "final")
        self.assertEqual(read["proceeds_kopecks"], EXAMPLE_PROCEEDS_KOPECKS)
        self.assertEqual(list(self.stored()["days"]), [DAY_A])

    def test_today_by_moscow_is_accepted(self):
        response = self.put_day(FIXED_TODAY.isoformat())
        self.assertEqual(response.status_code, 200)

    def test_moscow_today_uses_utc_plus_three(self):
        self.assertEqual(taxi_app.MOSCOW_TZ.utcoffset(None).total_seconds(), 3 * 3600)


# ---------------------------------------------------------------------------
# Точные суммы в копейках
# ---------------------------------------------------------------------------


class ExactAmountTests(_IsolatedCase):
    def test_synthetic_example_is_exact(self):
        snapshot = self.put_day(DAY_A).get_json()["snapshot"]
        self.assertEqual(snapshot["income_kopecks"], 100000 + 20000 + 2000 + 1050)
        self.assertEqual(snapshot["deductions_kopecks"], 21000 + 525)
        self.assertEqual(snapshot["proceeds_kopecks"], 101525)
        self.assertEqual(snapshot["proceeds"], "1015.25")
        self.assertEqual(self.stored()["days"][DAY_A]["amounts_kopecks"], EXAMPLE_KOPECKS)

    def test_comma_and_dot_are_equivalent(self):
        comma = _amounts(tips="10,50", extra_services="5,25")
        snapshot = self.put_day(DAY_A, amounts=comma).get_json()["snapshot"]
        self.assertEqual(snapshot["amounts_kopecks"], EXAMPLE_KOPECKS)
        self.assertEqual(snapshot["proceeds_kopecks"], EXAMPLE_PROCEEDS_KOPECKS)

    def test_json_numbers_are_accepted_exactly(self):
        numbers = {
            "card": 1000,
            "cash": 200,
            "bonuses": 20,
            "tips": 10.5,
            "commission": 210,
            "extra_services": 5.25,
        }
        snapshot = self.put_day(DAY_A, amounts=numbers).get_json()["snapshot"]
        self.assertEqual(snapshot["amounts_kopecks"], EXAMPLE_KOPECKS)

    def test_small_fractions_do_not_drift(self):
        amounts = {
            "card": "0.10",
            "cash": "0.20",
            "bonuses": "0.01",
            "tips": "0.09",
            "commission": "0.3",
            "extra_services": "0.07",
        }
        snapshot = self.put_day(DAY_A, amounts=amounts).get_json()["snapshot"]
        self.assertEqual(snapshot["income_kopecks"], 40)
        self.assertEqual(snapshot["deductions_kopecks"], 37)
        self.assertEqual(snapshot["proceeds_kopecks"], 3)
        self.assertEqual(snapshot["proceeds"], "0.03")

    def test_values_that_float_arithmetic_gets_wrong(self):
        # 0.29 * 100 = 28.999…, 8.2 * 100 = 819.999… и т. д. во float.
        amounts = {
            "card": "0.29",
            "cash": "8.20",
            "bonuses": "1.13",
            "tips": "0,57",
            "commission": "1.15",
            "extra_services": "4.35",
        }
        snapshot = self.put_day(DAY_A, amounts=amounts).get_json()["snapshot"]
        self.assertEqual(
            snapshot["amounts_kopecks"],
            {"card": 29, "cash": 820, "bonuses": 113, "tips": 57, "commission": 115, "extra_services": 435},
        )
        self.assertEqual(snapshot["proceeds_kopecks"], 29 + 820 + 113 + 57 - 115 - 435)
        self.assertEqual(snapshot["proceeds"], "4.69")

    def test_negative_proceeds_are_reported_not_rejected(self):
        snapshot = self.put_day(DAY_A, amounts=_amounts(commission="2000")).get_json()["snapshot"]
        self.assertEqual(snapshot["proceeds_kopecks"], 123050 - 200525)
        self.assertEqual(snapshot["proceeds"], "-774.75")

    def test_zero_and_boundaries(self):
        zero = self.put_day(DAY_A, amounts=ZERO_AMOUNTS).get_json()["snapshot"]
        self.assertEqual(zero["proceeds_kopecks"], 0)
        self.assertEqual(zero["proceeds"], "0.00")

        top = self.put_day(DAY_B, amounts=_amounts(card="10000000.00"))
        self.assertEqual(top.status_code, 200)
        self.assertEqual(top.get_json()["snapshot"]["amounts_kopecks"]["card"], 1_000_000_000)

    def test_whitespace_around_amount_is_ignored(self):
        snapshot = self.put_day(DAY_A, amounts=_amounts(card="  1000 ")).get_json()["snapshot"]
        self.assertEqual(snapshot["amounts_kopecks"]["card"], 100000)


# ---------------------------------------------------------------------------
# Некорректный ввод: 400 и ни одного изменённого байта
# ---------------------------------------------------------------------------

BAD_DATES = [
    "2026-02-30",
    "2026-13-01",
    "2026-1-05",
    "20260105",
    "2026-01-05T00:00",
    "abcd-ef-gh",
    "1999-12-31",
    "2026-01-16",  # завтра относительно FIXED_TODAY
    "2030-01-01",
    "２０２６-01-01",  # полноширинные цифры
]

BAD_AMOUNTS = [
    "-1",
    "1.234",
    "1e3",
    "",
    "   ",
    "1,000.00",
    "1 000",
    "10000000.01",
    "100000000",
    ".5",
    "5.",
    "abc",
    "١٢",  # арабско-индийские цифры
    None,
    True,
    False,
    -5,
    -0.5,
    1.234,
    [],
    {},
]


class InvalidInputTests(_IsolatedCase):
    def assert_rejected(self, response, field=None):
        self.assertEqual(response.status_code, 400, response.get_data(as_text=True))
        payload = response.get_json()
        self.assertTrue(payload.get("error"))
        if field is not None:
            self.assertEqual(payload.get("field"), field)

    def _check_all(self, make_request, field=None):
        # Без файла хранилища и с уже сохранённой датой: оба раза ничего не пишется.
        before = self.snapshot_dir()
        self.assert_rejected(make_request(), field)
        self.assertEqual(self.snapshot_dir(), before)

        self.assertEqual(self.put_day(DAY_B).status_code, 200)
        before = self.snapshot_dir()
        self.assert_rejected(make_request(), field)
        self.assertEqual(self.snapshot_dir(), before)
        os.remove(self.yday_file)

    def test_invalid_dates_on_save(self):
        for bad in BAD_DATES:
            with self.subTest(date=bad):
                self._check_all(lambda bad=bad: self.put_day(bad), "date")

    def test_invalid_dates_on_read(self):
        for bad in BAD_DATES:
            with self.subTest(date=bad):
                self.assert_rejected(self.get_day(bad), "date")
        self.assertFalse(os.path.exists(self.yday_file))

    def test_invalid_amounts(self):
        for field in taxi_app.YANDEX_DAY_FIELDS:
            for bad in BAD_AMOUNTS:
                with self.subTest(field=field, value=bad):
                    amounts = _amounts(**{field: bad})
                    self._check_all(lambda amounts=amounts: self.put_day(DAY_A, amounts=amounts), field)

    def test_missing_amount_field(self):
        for field in taxi_app.YANDEX_DAY_FIELDS:
            with self.subTest(field=field):
                amounts = dict(EXAMPLE_AMOUNTS)
                del amounts[field]
                self._check_all(lambda amounts=amounts: self.put_day(DAY_A, amounts=amounts), field)

    def test_unknown_amount_field(self):
        amounts = _amounts(fuel="100")
        self._check_all(lambda: self.put_day(DAY_A, amounts=amounts), "amounts")

    def test_invalid_kind(self):
        for kind in (None, "", "draft", "FINAL", 1, True):
            with self.subTest(kind=kind):
                body = {"kind": kind, "amounts": EXAMPLE_AMOUNTS}
                self._check_all(lambda body=body: self.client.put(f"/api/yandex-day/{DAY_A}", json=body), "kind")

    def test_invalid_body_shape(self):
        bodies = [
            ("json-array", lambda: self.client.put(f"/api/yandex-day/{DAY_A}", json=[1, 2])),
            ("not-json", lambda: self.client.put(f"/api/yandex-day/{DAY_A}", data="kind=final")),
            ("no-amounts", lambda: self.client.put(f"/api/yandex-day/{DAY_A}", json={"kind": "final"})),
            (
                "amounts-list",
                lambda: self.client.put(
                    f"/api/yandex-day/{DAY_A}", json={"kind": "final", "amounts": ["1000"]}
                ),
            ),
        ]
        for name, make_request in bodies:
            with self.subTest(body=name):
                self._check_all(make_request)


# ---------------------------------------------------------------------------
# Повреждённое или недоступное хранилище: явная ошибка без перезаписи
# ---------------------------------------------------------------------------


def _store_bytes(days: dict, version=1) -> bytes:
    return json.dumps({"version": version, "days": days}, ensure_ascii=False).encode("utf-8")


_GOOD_ENTRY = {
    "date": DAY_A,
    "kind": "final",
    "amounts_kopecks": dict(EXAMPLE_KOPECKS),
    "created_at": "2026-01-10T10:00:00+00:00",
    "updated_at": "2026-01-10T10:00:00+00:00",
}


def _entry(**overrides) -> dict:
    entry = json.loads(json.dumps(_GOOD_ENTRY))
    entry.update(overrides)
    return entry


DAMAGED_STORES = {
    "truncated": b'{"version": 1, "days": {"2026-01-10": {"date": "2026-01-',
    "empty_file": b"",
    "garbage": b"not json\n",
    "invalid_utf8": b'{"version": 1, "days": {"\xff\xfe": {}}}',
    "array_root": b"[]\n",
    "null_root": b"null\n",
    "no_version": json.dumps({"days": {}}).encode(),
    "future_version": _store_bytes({}, version=2),
    "bool_version": _store_bytes({}, version=True),
    "days_list": json.dumps({"version": 1, "days": []}).encode(),
    "bad_date_key": _store_bytes({"2026-02-30": _entry(date="2026-02-30")}),
    "key_mismatch": _store_bytes({DAY_A: _entry(date=DAY_B)}),
    "entry_not_object": _store_bytes({DAY_A: "final"}),
    "bad_kind": _store_bytes({DAY_A: _entry(kind="draft")}),
    "missing_amount": _store_bytes(
        {DAY_A: _entry(amounts_kopecks={k: v for k, v in EXAMPLE_KOPECKS.items() if k != "tips"})}
    ),
    "negative_amount": _store_bytes({DAY_A: _entry(amounts_kopecks=dict(EXAMPLE_KOPECKS, cash=-1))}),
    "float_amount": _store_bytes({DAY_A: _entry(amounts_kopecks=dict(EXAMPLE_KOPECKS, cash=1.5))}),
    "bool_amount": _store_bytes({DAY_A: _entry(amounts_kopecks=dict(EXAMPLE_KOPECKS, cash=True))}),
    "huge_amount": _store_bytes(
        {DAY_A: _entry(amounts_kopecks=dict(EXAMPLE_KOPECKS, cash=1_000_000_001))}
    ),
    "no_updated_at": _store_bytes({DAY_A: {k: v for k, v in _GOOD_ENTRY.items() if k != "updated_at"}}),
}


class DamagedStoreTests(_IsolatedCase):
    def requests(self):
        return [
            ("GET list", lambda: self.client.get("/api/yandex-day")),
            ("GET day", lambda: self.get_day(DAY_A)),
            ("PUT same day", lambda: self.put_day(DAY_A, "final")),
            ("PUT other day", lambda: self.put_day(DAY_B)),
        ]

    def assert_damaged(self, response):
        self.assertEqual(response.status_code, 503, response.get_data(as_text=True))
        payload = response.get_json()
        self.assertEqual(payload["store_state"], "damaged")
        self.assertIn("yandex_day.json", payload["error"])

    def test_good_store_fixture_is_valid(self):
        self.write_bytes(self.yday_file, _store_bytes({DAY_A: _GOOD_ENTRY}))
        response = self.get_day(DAY_A)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["snapshot"]["proceeds_kopecks"], EXAMPLE_PROCEEDS_KOPECKS)

    def test_damaged_store_fails_closed_without_overwrite(self):
        for name, data in DAMAGED_STORES.items():
            self.write_bytes(self.yday_file, data)
            for label, make_request in self.requests():
                with self.subTest(store=name, request=label):
                    before = self.snapshot_dir()
                    self.assert_damaged(make_request())
                    self.assertEqual(self.snapshot_dir(), before)
                    self.assertEqual(_file_bytes(self.yday_file), data)

    def test_store_path_is_a_directory(self):
        os.mkdir(self.yday_file)
        for label, make_request in self.requests():
            with self.subTest(request=label):
                before = self.snapshot_dir()
                self.assert_damaged(make_request())
                self.assertEqual(self.snapshot_dir(), before)
        self.assertTrue(os.path.isdir(self.yday_file))

    def test_unreadable_store(self):
        original = _store_bytes({DAY_A: _GOOD_ENTRY})
        self.write_bytes(self.yday_file, original)
        real_open = builtins.open

        def guarded_open(file, *args, **kwargs):
            if os.fspath(file) == self.yday_file:
                raise PermissionError(13, "Permission denied (synthetic)", file)
            return real_open(file, *args, **kwargs)

        for label, make_request in self.requests():
            with self.subTest(request=label):
                with mock.patch("builtins.open", guarded_open):
                    response = make_request()
                self.assert_damaged(response)
                self.assertEqual(_file_bytes(self.yday_file), original)
        self.assert_no_temp_files()

    def test_missing_and_damaged_are_distinguished(self):
        missing = self.client.get("/api/yandex-day")
        self.assertEqual((missing.status_code, missing.get_json()["store_state"]), (200, "missing"))

        self.put_day(DAY_A)
        ok = self.client.get("/api/yandex-day")
        self.assertEqual((ok.status_code, ok.get_json()["store_state"]), (200, "ok"))

        self.write_bytes(self.yday_file, b"{broken")
        damaged = self.client.get("/api/yandex-day")
        self.assertEqual((damaged.status_code, damaged.get_json()["store_state"]), (503, "damaged"))

    def test_write_failure_keeps_old_file_and_cleans_temp(self):
        self.put_day(DAY_A)
        original = _file_bytes(self.yday_file)

        with mock.patch.object(taxi_app.os, "replace", side_effect=OSError(28, "No space left (synthetic)")):
            response = self.put_day(DAY_A, "final", _amounts(card="1"))
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json()["store_state"], "write_failed")
        self.assertTrue(response.get_json()["error"])
        self.assertEqual(_file_bytes(self.yday_file), original)
        self.assert_no_temp_files()

    def test_write_failure_on_first_save_creates_nothing(self):
        with mock.patch.object(taxi_app.os, "fsync", side_effect=OSError(5, "I/O error (synthetic)")):
            response = self.put_day(DAY_A)
        self.assertEqual(response.status_code, 500)
        self.assertFalse(os.path.exists(self.yday_file))
        self.assert_no_temp_files()


# ---------------------------------------------------------------------------
# Независимость от смены, заказов и истории
# ---------------------------------------------------------------------------


class ShiftCoexistenceTests(_IsolatedCase):
    def test_manual_order_and_daily_snapshot_do_not_mix(self):
        order = self.client.post("/api/orders", json={"amount": 450})
        self.assertEqual(order.status_code, 200)
        state_bytes = _file_bytes(self.data_file)

        self.assertEqual(self.put_day(DAY_A, "final").status_code, 200)

        # Снимок не трогает файл состояния и не добавляет заказов или выручки.
        self.assertEqual(_file_bytes(self.data_file), state_bytes)
        shift = self.client.get("/api/state").get_json()["shift"]
        self.assertEqual(len(shift["orders"]), 1)
        self.assertEqual(shift["revenue"], 450.0)
        self.assertEqual(shift["expenses"], [])

        yday_bytes = _file_bytes(self.yday_file)
        finish = self.client.post("/api/shift/finish")
        self.assertEqual(finish.status_code, 200)
        archived = finish.get_json()["archived"]
        self.assertEqual(archived["orders_count"], 1)
        self.assertEqual(archived["revenue"], 450.0)
        self.assertEqual(archived["profit"], 450.0)

        history = self.client.get("/api/history").get_json()["shifts"]
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["orders_count"], 1)
        self.assertEqual(history[0]["revenue"], 450.0)

        # Завершение смены не меняет и не удаляет дневной снимок.
        self.assertEqual(_file_bytes(self.yday_file), yday_bytes)
        snapshot = self.get_day(DAY_A).get_json()["snapshot"]
        self.assertEqual(snapshot["proceeds_kopecks"], EXAMPLE_PROCEEDS_KOPECKS)

        # Новая смена пустая, снимок по-прежнему на месте.
        new_shift = self.client.get("/api/state").get_json()["shift"]
        self.assertEqual(new_shift["orders"], [])
        self.assertEqual(new_shift["revenue"], 0.0)

    def test_shift_routes_never_touch_daily_store(self):
        self.put_day(DAY_A)
        yday_bytes = _file_bytes(self.yday_file)

        for method, path, body in (
            ("POST", "/api/car", {"car_brand": "Synthetic", "car_plate": "S000YN"}),
            ("POST", "/api/status", {"status": "busy"}),
            ("POST", "/api/markers", {"lat": 55.75, "lng": 37.61}),
            ("POST", "/api/orders", {"amount": 300}),
            ("POST", "/api/expenses", {"amount": 40, "category": "wash"}),
            ("POST", "/api/mileage/reset", {}),
            ("POST", "/api/shift/finish", {}),
            ("GET", "/api/state", None),
            ("GET", "/api/history", None),
            ("GET", "/", None),
        ):
            with self.subTest(route=f"{method} {path}"):
                response = self.client.get(path) if method == "GET" else self.client.post(path, json=body)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(_file_bytes(self.yday_file), yday_bytes)

    def test_damaged_daily_store_does_not_break_shift(self):
        self.write_bytes(self.yday_file, b"{broken")
        self.assertEqual(self.client.post("/api/orders", json={"amount": 100}).status_code, 200)
        self.assertEqual(self.client.get("/api/state").status_code, 200)
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(_file_bytes(self.yday_file), b"{broken")

    def test_damaged_shift_state_does_not_block_daily_snapshot(self):
        self.write_bytes(self.data_file, b"{broken")
        self.assertEqual(self.client.get("/api/state").status_code, 503)
        self.assertEqual(self.put_day(DAY_A).status_code, 200)
        self.assertEqual(_file_bytes(self.data_file), b"{broken")

    def test_snapshot_survives_app_restart(self):
        self.put_day(DAY_A, "final")
        self.put_day(DAY_B, "partial", _amounts(card="1"))
        self.client.post("/api/shift/finish")

        # Новый процесс Python — как перезапуск приложения.
        script = (
            "import json, sys\n"
            "from datetime import date\n"
            "from unittest import mock\n"
            f"sys.path.insert(0, {REPO_ROOT!r})\n"
            "import app\n"
            f"app.YANDEX_DAY_FILE = {self.yday_file!r}\n"
            f"app.DATA_FILE = {self.data_file!r}\n"
            f"app.HISTORY_FILE = {self.history_file!r}\n"
            "with mock.patch.object(app, '_moscow_today', return_value=date(2026, 1, 15)):\n"
            "    data = app.app.test_client().get('/api/yandex-day').get_json()\n"
            "print(json.dumps(data))\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True, timeout=60, check=True
        )
        data = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(data["store_state"], "ok")
        self.assertEqual([day["date"] for day in data["days"]], [DAY_B, DAY_A])
        self.assertEqual(data["days"][1]["kind"], "final")
        self.assertEqual(data["days"][1]["proceeds_kopecks"], EXAMPLE_PROCEEDS_KOPECKS)


# ---------------------------------------------------------------------------
# Последовательные обновления в одном процессе
# ---------------------------------------------------------------------------


class SerializedUpdateTests(_IsolatedCase):
    def test_concurrent_saves_of_different_dates_are_not_lost(self):
        dates = [f"2026-01-{day:02d}" for day in range(1, 15)]
        barrier = threading.Barrier(len(dates))
        errors: list[str] = []

        def worker(day: str):
            client = taxi_app.app.test_client()
            barrier.wait()
            response = client.put(
                f"/api/yandex-day/{day}",
                json={"kind": "partial", "amounts": _amounts(card=str(int(day[-2:])))},
            )
            if response.status_code != 200:
                errors.append(f"{day}: {response.status_code}")

        threads = [threading.Thread(target=worker, args=(day,)) for day in dates]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        self.assertEqual(errors, [])
        days = self.stored()["days"]
        self.assertEqual(sorted(days), dates)
        for day in dates:
            self.assertEqual(days[day]["amounts_kopecks"]["card"], int(day[-2:]) * 100)
        self.assert_no_temp_files()

    def test_save_holds_dedicated_lock(self):
        self.assertTrue(taxi_app._yandex_day_lock.acquire(timeout=1))
        result: dict = {}
        try:
            thread = threading.Thread(target=lambda: result.setdefault("r", self.put_day(DAY_A)))
            thread.start()
            thread.join(timeout=0.3)
            self.assertTrue(thread.is_alive(), "сохранение не ждёт блокировку дневных итогов")
            self.assertFalse(os.path.exists(self.yday_file))
        finally:
            taxi_app._yandex_day_lock.release()
        thread.join(timeout=10)
        self.assertEqual(result["r"].status_code, 200)


# ---------------------------------------------------------------------------
# Разметка панели
# ---------------------------------------------------------------------------


class DashboardMarkupTests(_IsolatedCase):
    def test_index_has_button_and_form(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("Итог дня из Яндекс Про", html)
        self.assertIn('id="yday-btn"', html)
        self.assertIn('id="yday-form"', html)
        self.assertIn('id="yday-date"', html)
        self.assertIn('id="yday-error"', html)
        self.assertIn('value="partial"', html)
        self.assertIn('value="final"', html)
        for field in taxi_app.YANDEX_DAY_FIELDS:
            with self.subTest(field=field):
                self.assertIn(f'id="yday-{field}"', html)
                self.assertIn(f'data-field="{field}"', html)


if __name__ == "__main__":
    unittest.main()
