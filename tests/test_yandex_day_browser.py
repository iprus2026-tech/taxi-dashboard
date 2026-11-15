"""Браузерные регрессии TAXI-YANDEX-DAY-PR54-REWORK-01: форма «Итог дня».

Проверяют два замечания P2 к PR #54:

* P2-1: пока GET выбранной даты не завершился (или завершился ошибкой), форма
  не даёт сохранить суммы прежней даты, а ответ GET не стирает молча правки
  водителя. Повторная загрузка после сбоя восстанавливает работу.
* P2-2: запоздалый ответ PUT (успех или ошибка) не подменяет форму другой даты
  и не сбрасывает её: видимая дата, суммы и дата, под которой уходит PUT,
  совпадают.

Как устроено:

* Flask из app.py запускается в этом же процессе на 127.0.0.1 со случайным
  портом ОС (не 5000/5001/5002). Файлы driver_state.json, shift_history.json и
  yandex_day.json перенаправлены во временный каталог; «сегодня» по Москве
  зафиксировано (2026-01-15) и на сервере, и в браузере. Настоящие файлы
  рядом с app.py не читаются и не меняются (проверяется в tearDownModule).
* Chromium через Playwright, экран 360 × 800. Все внешние запросы (CDN Leaflet,
  погода, тайлы) обрываются: сеть наружу не нужна.
* Завершением GET/PUT /api/yandex-day/<дата> управляет тест через page.route:
  нужный запрос удерживается и затем пропускается к серверу или завершается
  синтетической ошибкой. Скрипт в странице синхронно записывает каждый вызов
  fetch к /api/yandex-day (метод, путь, тело) и считает незавершённые запросы,
  поэтому тест ждёт событий, а не таймеров.
* Данные только синтетические.

Запуск из корня репозитория (нужны flask и playwright для Python; браузер —
Chromium из PLAYWRIGHT_BROWSERS_PATH или путь в TAXI_TEST_CHROMIUM):
    python3 -m unittest tests.test_yandex_day_browser -v
Без playwright модуль пропускается (skip) с объяснением.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from datetime import date
from unittest import mock

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - зависит от окружения
    sync_playwright = None

try:
    from werkzeug.serving import WSGIRequestHandler, make_server

    import app as taxi_app

    class _QuietHandler(WSGIRequestHandler):
        def log_request(self, *args, **kwargs):  # noqa: D401 - тихий журнал
            pass
except ImportError:  # pragma: no cover - зависит от окружения
    taxi_app = None

FIXED_TODAY = date(2026, 1, 15)
TODAY = FIXED_TODAY.isoformat()
# 09:00 UTC = 12:00 по Москве 15 января 2026.
BROWSER_NOW = "2026-01-15T09:00:00Z"
DAY_A = "2026-01-10"
DAY_B = "2026-01-11"
FORBIDDEN_PORTS = {5000, 5001, 5002}

FIELDS = ("card", "cash", "bonuses", "tips", "commission", "extra_services")

# Синтетические суммы в том виде, как их вводит водитель.
INPUT_A = {"card": "1000", "cash": "200", "bonuses": "20", "tips": "10,50",
           "commission": "210", "extra_services": "5,25"}
INPUT_B = {"card": "2500", "cash": "300", "bonuses": "", "tips": "40",
           "commission": "512,75", "extra_services": ""}
INPUT_T = {"card": "700", "cash": "", "bonuses": "", "tips": "",
           "commission": "140", "extra_services": ""}
EMPTY_FORM = {field: "" for field in FIELDS}


def _to_kopecks(text: str) -> int:
    if not text:
        return 0
    rubles, _, rest = text.replace(",", ".").partition(".")
    return int(rubles) * 100 + int(rest.ljust(2, "0") or 0)


def _kopecks(inputs: dict) -> dict:
    return {field: _to_kopecks(inputs[field]) for field in FIELDS}


def _api_amounts(inputs: dict) -> dict:
    return {field: f"{k // 100}.{k % 100:02d}" for field, k in _kopecks(inputs).items()}


_REAL_FILES = [os.path.join(REPO_ROOT, name)
               for name in ("driver_state.json", "shift_history.json", "yandex_day.json")]
_REAL_SNAPSHOT: dict = {}


def _file_bytes(path):
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except FileNotFoundError:
        return None


def setUpModule():
    if sync_playwright is None:
        raise unittest.SkipTest("playwright для Python не установлен: браузерные регрессии не запущены")
    if taxi_app is None:
        raise unittest.SkipTest("flask не установлен: браузерные регрессии не запущены")
    for path in _REAL_FILES:
        _REAL_SNAPSHOT[path] = _file_bytes(path)


def tearDownModule():
    for path, before in _REAL_SNAPSHOT.items():
        if _file_bytes(path) != before:
            raise AssertionError(f"Тесты изменили настоящий файл {path}")


# Пишет каждый вызов fetch к /api/yandex-day синхронно в момент вызова и
# считает незавершённые. Счётчик уменьшается макрозадачей после того, как
# страница прочитала ответ (или получила ошибку), то есть когда обработчик
# в script.js уже отработал.
FETCH_PROBE = r"""
(() => {
  const original = window.fetch.bind(window);
  window.__ydayLog = [];
  window.__ydayInflight = 0;
  window.fetch = async (input, init = {}) => {
    const raw = typeof input === "string" ? input : input.url;
    const url = new URL(raw, location.href);
    if (!url.pathname.startsWith("/api/yandex-day")) return original(input, init);
    let body = null;
    try { body = init.body ? JSON.parse(init.body) : null; } catch { body = String(init.body); }
    window.__ydayLog.push({ method: (init.method || "GET").toUpperCase(), path: url.pathname, body });
    window.__ydayInflight += 1;
    let settled = false;
    const done = () => {
      if (settled) return;
      settled = true;
      setTimeout(() => { window.__ydayInflight -= 1; }, 0);
    };
    let response;
    try {
      response = await original(input, init);
    } catch (error) {
      done();
      throw error;
    }
    const json = response.json.bind(response);
    response.json = () => json().finally(done);
    return response;
  };
})();
"""


class _ApiGate:
    """Удерживает выбранные запросы /api/yandex-day/<дата> до команды теста."""

    def __init__(self, test):
        self.test = test
        self.rules = []  # (method, date) — удержать следующий такой запрос
        self.held = []  # (method, date, route)

    def handle(self, route):
        request = route.request
        day = request.url.rsplit("/", 1)[-1]
        key = (request.method, day)
        if key in self.rules:
            self.rules.remove(key)
            self.held.append((request.method, day, route))
            return
        route.fallback()

    def hold(self, method, day):
        self.rules.append((method, day))

    def wait_held(self, method, day, timeout=5.0):
        deadline = time.monotonic() + timeout
        while not any(m == method and d == day for m, d, _ in self.held):
            if time.monotonic() > deadline:
                self.test.fail(f"запрос {method} {day} не дошёл до сети")
            # Пока ждём, Playwright доставляет события route.
            self.test.page.wait_for_timeout(10)

    def release(self, method, day, *, status=None, abort=False):
        for index, (m, d, route) in enumerate(self.held):
            if m == method and d == day:
                del self.held[index]
                break
        else:
            self.test.fail(f"нет удержанного запроса {method} {day}")
        if abort:
            route.abort("failed")
        elif status is not None:
            route.fulfill(
                status=status,
                content_type="application/json",
                body=json.dumps({"error": "Синтетический сбой сервера"}),
            )
        else:
            route.continue_()


class YandexDayBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="taxi-yday-browser-")
        cls.yday_file = os.path.join(cls.tmpdir, "yandex_day.json")
        cls._patches = [
            mock.patch.object(taxi_app, "DATA_FILE", os.path.join(cls.tmpdir, "driver_state.json")),
            mock.patch.object(taxi_app, "HISTORY_FILE", os.path.join(cls.tmpdir, "shift_history.json")),
            mock.patch.object(taxi_app, "YANDEX_DAY_FILE", cls.yday_file),
            mock.patch.object(taxi_app, "_moscow_today", return_value=FIXED_TODAY),
        ]
        for patcher in cls._patches:
            patcher.start()

        cls.server = make_server("127.0.0.1", 0, taxi_app.app, threaded=True,
                                 request_handler=_QuietHandler)
        cls.port = cls.server.server_port
        assert cls.port not in FORBIDDEN_PORTS, cls.port
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

        cls.pw = sync_playwright().start()
        executable = os.environ.get("TAXI_TEST_CHROMIUM") or None
        cls.browser = cls.pw.chromium.launch(executable_path=executable)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.browser.close()
            cls.pw.stop()
        finally:
            cls.server.shutdown()
            cls.server_thread.join(timeout=10)
            for patcher in reversed(cls._patches):
                patcher.stop()
            shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def setUp(self):
        if os.path.exists(self.yday_file):
            os.remove(self.yday_file)
        self.context = self.browser.new_context(viewport={"width": 360, "height": 800},
                                                locale="ru-RU", timezone_id="Europe/Moscow")
        self.addCleanup(self.context.close)
        self.context.add_init_script(FETCH_PROBE)
        self.context.route("**/*", self._only_local)
        self.gate = _ApiGate(self)
        self.context.route("**/api/yandex-day/*", self.gate.handle)
        self.page = self.context.new_page()
        self.page.set_default_timeout(5000)
        self.page.clock.set_fixed_time(BROWSER_NOW)
        self.dialogs = []
        self.dialog_answer = True
        self.page.on("dialog", self._on_dialog)
        self.page_errors = []
        self.page.on("pageerror", lambda error: self.page_errors.append(str(error)))

    def tearDown(self):
        self.assertEqual(self.page_errors, [], "ошибки JavaScript на странице")

    # --- окружение ---------------------------------------------------------

    def _only_local(self, route):
        if route.request.url.startswith(self.base_url + "/"):
            route.fallback()
        else:
            route.abort()

    def _on_dialog(self, dialog):
        self.dialogs.append(dialog.message)
        if self.dialog_answer:
            dialog.accept()
        else:
            dialog.dismiss()

    def seed(self, day, inputs, kind="partial"):
        """Сохраняет снимок напрямую через API, минуя браузер."""
        request = urllib.request.Request(
            f"{self.base_url}/api/yandex-day/{day}",
            data=json.dumps({"kind": kind, "amounts": _api_amounts(inputs)}).encode(),
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            self.assertEqual(response.status, 200)

    def stored(self):
        """Сохранённые записи: дата → суммы в копейках (читается сервером)."""
        with urllib.request.urlopen(f"{self.base_url}/api/yandex-day", timeout=10) as response:
            data = json.load(response)
        return {day["date"]: day["amounts_kopecks"] for day in data["days"]}

    # --- страница -----------------------------------------------------------

    def log(self):
        return self.page.evaluate("window.__ydayLog")

    def puts(self):
        return [entry for entry in self.log() if entry["method"] == "PUT"]

    def wait_inflight(self, count):
        self.page.wait_for_function("n => window.__ydayInflight === n", arg=count)

    def open_screen(self, *, hold_today=False):
        self.page.goto(self.base_url + "/")
        if hold_today:
            self.gate.hold("GET", TODAY)
        self.page.click("#yday-btn")
        if hold_today:
            self.gate.wait_held("GET", TODAY)
        else:
            self.wait_inflight(0)

    def choose_date(self, day):
        """Выбор даты в поле так, как это делает браузер: input + change."""
        self.page.fill("#yday-date", day)

    def force_choose_date(self, day):
        """Событие change в обход disabled — проверяет и обработчик, и блокировку."""
        self.page.evaluate(
            """day => {
                const input = document.getElementById('yday-date');
                input.value = day;
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }""",
            day,
        )

    def force_submit(self):
        """Отправка формы любым путём: кнопка, Enter в поле — submit-событие."""
        self.page.evaluate("document.getElementById('yday-form').requestSubmit()")

    def fill_amounts(self, inputs):
        for field in FIELDS:
            self.page.fill(f"#yday-{field}", inputs[field])

    def form_amounts(self):
        return self.page.evaluate(
            "fields => Object.fromEntries(fields.map(f => [f, document.getElementById('yday-' + f).value]))",
            list(FIELDS),
        )

    def shown_date(self):
        return self.page.input_value("#yday-date")

    def text(self, selector):
        return self.page.text_content(selector) or ""

    def is_visible(self, selector):
        return self.page.is_visible(selector)

    def editable_controls(self):
        """Поля и кнопки, через которые можно изменить или сохранить суммы."""
        return self.page.evaluate(
            """() => [...document.querySelectorAll(
                    '#yday-form .yday-amount, #yday-form input[name="kind"], #yday-save')]
                 .filter(el => !el.disabled).map(el => el.id || el.value)"""
        )

    def assert_locked(self, why):
        self.assertEqual(self.editable_controls(), [], why)

    # --- P2-1: загрузка даты -------------------------------------------------

    def test_pending_load_never_saves_previous_date_amounts(self):
        self.seed(DAY_A, INPUT_A)
        self.open_screen()
        self.choose_date(DAY_A)
        self.wait_inflight(0)
        self.assertEqual(self.form_amounts(), INPUT_A)

        self.gate.hold("GET", DAY_B)
        self.choose_date(DAY_B)
        self.gate.wait_held("GET", DAY_B)

        # Водитель жмёт «Сохранить» / Enter, пока B ещё грузится.
        self.page.press("#yday-date", "Enter")
        self.force_submit()
        self.assertEqual(
            self.puts(), [],
            "во время загрузки B ушёл PUT — суммы даты A сохраняются под датой B",
        )
        self.assertNotIn(DAY_B, self.stored())
        self.assertEqual(self.form_amounts(), EMPTY_FORM, "в форме B видны суммы даты A")
        self.assert_locked("до загрузки B форму можно править или сохранить")
        self.assertEqual(self.text("#yday-state"), "Загружаем…")

        self.gate.release("GET", DAY_B)
        self.wait_inflight(0)
        self.assertIn("Новая запись", self.text("#yday-state"))
        self.assertEqual(self.form_amounts(), EMPTY_FORM)
        self.fill_amounts(INPUT_B)
        self.page.click("#yday-save")
        self.wait_inflight(0)

        self.assertEqual(
            [(p["path"], p["body"]["amounts"]) for p in self.puts()],
            [(f"/api/yandex-day/{DAY_B}", _api_amounts(INPUT_B))],
        )
        self.assertEqual(self.stored(), {DAY_A: _kopecks(INPUT_A), DAY_B: _kopecks(INPUT_B)})

    def test_pending_load_does_not_silently_erase_edits(self):
        self.seed(TODAY, INPUT_T)
        self.open_screen(hold_today=True)

        editable = self.page.is_editable("#yday-card")
        if editable:
            self.page.fill("#yday-card", "777")
        self.gate.release("GET", TODAY)
        self.wait_inflight(0)
        if editable:
            self.assertTrue(
                self.page.input_value("#yday-card") == "777" or self.dialogs,
                "правка «777», сделанная во время загрузки, молча заменена ответом GET",
            )
        self.assertFalse(editable, "суммы можно править до завершения загрузки даты")

        self.assertEqual(self.form_amounts(), INPUT_T)
        self.assertIn("Сохранено", self.text("#yday-state"))
        self.assertEqual(set(self.editable_controls()),
                         {f"yday-{f}" for f in FIELDS} | {"partial", "final", "yday-save"})
        # Загруженный снимок не считается правкой: закрытие без вопроса.
        self.page.click("#yday-close")
        self.assertEqual(self.dialogs, [])

    def test_failed_load_blocks_save_and_retry_recovers(self):
        self.seed(DAY_A, INPUT_A)
        self.open_screen()

        self.gate.hold("GET", DAY_A)
        self.choose_date(DAY_A)
        self.gate.wait_held("GET", DAY_A)
        self.gate.release("GET", DAY_A, status=500)
        self.wait_inflight(0)

        self.page.press("#yday-date", "Enter")
        self.force_submit()
        self.assertEqual(self.puts(), [], "после сбоя загрузки ушёл PUT с незагруженными суммами")
        self.assertEqual(self.stored()[DAY_A], _kopecks(INPUT_A), "сохранённый снимок A затёрт")
        self.assert_locked("после сбоя загрузки форму можно править или сохранить")
        self.assertIn("Не удалось загрузить", self.text("#yday-state"))
        self.assertTrue(self.is_visible("#yday-error"))
        self.assertIn("Синтетический сбой сервера", self.text("#yday-error"))
        self.assertEqual(self.shown_date(), DAY_A)

        # Повтор: пока идёт, форма закрыта; после успеха — снимок A и правка.
        self.assertTrue(self.is_visible("#yday-retry"), "нет кнопки повторной загрузки")
        self.gate.hold("GET", DAY_A)
        self.page.click("#yday-retry")
        self.gate.wait_held("GET", DAY_A)
        self.assert_locked("во время повторной загрузки форму можно править")
        self.assertFalse(self.is_visible("#yday-error"))
        self.gate.release("GET", DAY_A)
        self.wait_inflight(0)

        self.assertFalse(self.is_visible("#yday-retry"))
        self.assertEqual(self.form_amounts(), INPUT_A)
        self.assertIn("Сохранено", self.text("#yday-state"))
        self.page.fill("#yday-card", "1100")
        self.page.click("#yday-save")
        self.wait_inflight(0)
        self.assertEqual(self.stored()[DAY_A], _kopecks(dict(INPUT_A, card="1100")))

    def test_network_failure_then_reselect_same_date_recovers(self):
        self.seed(DAY_A, INPUT_A)
        self.seed(DAY_B, INPUT_B)
        self.open_screen()

        self.gate.hold("GET", DAY_B)
        self.page.click(f'#yday-saved-list button[data-date="{DAY_B}"]')
        self.gate.wait_held("GET", DAY_B)
        self.gate.release("GET", DAY_B, abort=True)
        self.wait_inflight(0)

        self.force_submit()
        self.assertEqual(self.puts(), [], "после обрыва сети ушёл PUT с незагруженными суммами")
        self.assert_locked("после обрыва сети форму можно править или сохранить")

        # Повторный выбор той же даты в списке — тоже повтор загрузки.
        self.page.click(f'#yday-saved-list button[data-date="{DAY_B}"]')
        self.wait_inflight(0)
        self.assertEqual(self.form_amounts(), INPUT_B)
        self.assertFalse(self.is_visible("#yday-error"))
        self.assertEqual(self.stored(), {DAY_A: _kopecks(INPUT_A), DAY_B: _kopecks(INPUT_B)})

    # --- P2-2: ответ сохранения ----------------------------------------------

    def test_delayed_save_cannot_land_on_another_date(self):
        self.seed(DAY_B, INPUT_B)
        self.open_screen()
        self.choose_date(DAY_A)
        self.wait_inflight(0)
        self.fill_amounts(INPUT_A)

        self.gate.hold("PUT", DAY_A)
        self.page.click("#yday-save")
        self.gate.wait_held("PUT", DAY_A)

        # Пока PUT(A) в пути, водитель пытается перейти на B: список и поле даты.
        self.page.evaluate(
            "day => document.querySelector(`#yday-saved-list button[data-date='${day}']`).click()",
            DAY_B,
        )
        self.force_choose_date(DAY_B)
        self.wait_inflight(1)  # остался только PUT(A)

        self.gate.release("PUT", DAY_A)
        self.wait_inflight(0)

        # Что видно, то и уходит: водитель снова жмёт «Сохранить».
        visible_date, visible = self.shown_date(), self.form_amounts()
        self.force_submit()
        self.wait_inflight(0)
        last_put = self.puts()[-1]
        self.assertEqual(last_put["path"], f"/api/yandex-day/{visible_date}")
        self.assertEqual(last_put["body"]["amounts"], _api_amounts(visible))

        self.assertEqual(
            self.stored(), {DAY_A: _kopecks(INPUT_A), DAY_B: _kopecks(INPUT_B)},
            "запоздалый ответ PUT(A) подменил форму B — B перезаписан суммами A",
        )
        self.assertEqual((visible_date, visible), (DAY_A, INPUT_A))

    def test_navigation_is_locked_while_saving(self):
        self.seed(DAY_B, INPUT_B)
        self.open_screen()
        self.choose_date(DAY_A)
        self.wait_inflight(0)
        self.fill_amounts(INPUT_A)

        self.gate.hold("PUT", DAY_A)
        self.page.click("#yday-save")
        self.gate.wait_held("PUT", DAY_A)
        self.assertTrue(self.page.is_disabled("#yday-date"))
        self.assertTrue(self.page.is_disabled(f'#yday-saved-list button[data-date="{DAY_B}"]'))
        self.assert_locked("во время сохранения суммы можно править")

        self.gate.release("PUT", DAY_A)
        self.wait_inflight(0)
        self.assertEqual(self.text("#toast"), "Итог дня сохранён")
        self.assertIn("Сохранено", self.text("#yday-state"))
        self.assertFalse(self.page.is_disabled("#yday-date"))
        self.choose_date(DAY_B)
        self.wait_inflight(0)
        self.assertEqual(self.form_amounts(), INPUT_B)

    def test_delayed_save_success_after_close_and_reopen(self):
        self.open_screen()
        self.choose_date(DAY_A)
        self.wait_inflight(0)
        self.fill_amounts(INPUT_A)

        self.gate.hold("PUT", DAY_A)
        self.page.click("#yday-save")
        self.gate.wait_held("PUT", DAY_A)
        self.page.click("#yday-close")  # подтверждение потери правок — принять
        self.page.click("#yday-btn")
        self.wait_inflight(1)  # GET сегодня завершён, PUT(A) ещё в пути

        self.gate.release("PUT", DAY_A)
        self.wait_inflight(0)

        self.assertEqual(
            (self.shown_date(), self.form_amounts()), (TODAY, EMPTY_FORM),
            "запоздалый ответ PUT(A) подменил форму сегодняшней даты",
        )
        self.assertIn("Новая запись", self.text("#yday-state"))
        self.assertEqual(self.text("#toast"), "Итог за 10.01.2026 сохранён")
        self.assertEqual(self.stored(), {DAY_A: _kopecks(INPUT_A)})

        self.fill_amounts(INPUT_T)
        self.page.click("#yday-save")
        self.wait_inflight(0)
        self.assertEqual(self.puts()[-1]["path"], f"/api/yandex-day/{TODAY}")
        self.assertEqual(self.stored(), {DAY_A: _kopecks(INPUT_A), TODAY: _kopecks(INPUT_T)})

    def test_delayed_save_error_after_close_and_reopen(self):
        self.open_screen()
        self.choose_date(DAY_A)
        self.wait_inflight(0)
        self.fill_amounts(INPUT_A)

        self.gate.hold("PUT", DAY_A)
        self.page.click("#yday-save")
        self.gate.wait_held("PUT", DAY_A)
        self.page.click("#yday-close")
        self.page.click("#yday-btn")
        self.wait_inflight(1)
        if not self.page.is_disabled("#yday-card"):
            self.fill_amounts(INPUT_T)
        before = self.form_amounts()

        self.gate.release("PUT", DAY_A, status=500)
        self.wait_inflight(0)

        self.assertFalse(
            self.is_visible("#yday-error"),
            "ошибка запоздалого PUT(A) показана в форме сегодняшней даты",
        )
        self.assertEqual((self.shown_date(), self.form_amounts()), (TODAY, before))
        self.assertEqual(self.text("#toast"),
                         "Итог за 10.01.2026 не сохранён: Синтетический сбой сервера")
        self.assertEqual(self.stored(), {})

    # --- обычная работа сохраняется ------------------------------------------

    def test_normal_save_update_error_and_reopen(self):
        self.open_screen()
        self.choose_date(DAY_A)
        self.wait_inflight(0)
        self.assertIn("Новая запись", self.text("#yday-state"))
        self.fill_amounts(INPUT_A)
        self.page.click('label.yday-kind__option:has(input[value="final"])')
        self.assertEqual(self.text("#yday-proceeds").replace(" ", " ").replace(" ", " "),
                         "1 015,25 ₽")
        self.page.click("#yday-save")
        self.wait_inflight(0)
        self.assertEqual(self.text("#toast"), "Итог дня сохранён")
        self.assertIn("Сохранено: Итог дня", self.text("#yday-state"))
        self.assertEqual(self.puts()[-1]["body"], {"kind": "final", "amounts": _api_amounts(INPUT_A)})

        self.page.fill("#yday-cash", "250")
        self.page.click("#yday-save")
        self.wait_inflight(0)
        self.assertEqual(self.text("#toast"), "Итог дня обновлён")
        updated = dict(INPUT_A, cash="250")

        # Ошибка сохранения текущей даты: сообщение в форме, правки остаются.
        self.page.fill("#yday-tips", "99")
        self.gate.hold("PUT", DAY_A)
        self.page.click("#yday-save")
        self.gate.wait_held("PUT", DAY_A)
        self.gate.release("PUT", DAY_A, status=500)
        self.wait_inflight(0)
        self.assertEqual(self.text("#yday-error"), "Не сохранено: Синтетический сбой сервера")
        self.assertEqual(self.form_amounts(), dict(updated, tips="99"))
        self.assertIn("yday-save", self.editable_controls())
        self.assertEqual(self.stored(), {DAY_A: _kopecks(updated)})

        # Несохранённые правки: отказ от закрытия оставляет экран, согласие закрывает.
        self.dialog_answer = False
        self.page.click("#yday-close")
        self.assertTrue(self.is_visible("#yday-screen"))
        self.dialog_answer = True
        self.page.click("#yday-close")
        self.assertFalse(self.is_visible("#yday-screen"))
        self.assertEqual(len(self.dialogs), 2)

        self.page.click("#yday-btn")
        self.wait_inflight(0)
        self.assertEqual(self.shown_date(), TODAY)
        self.choose_date(DAY_A)
        self.wait_inflight(0)
        self.assertEqual(self.form_amounts(), updated)
        self.assertIn("Сохранено: Итог дня", self.text("#yday-state"))


if __name__ == "__main__":
    unittest.main()
