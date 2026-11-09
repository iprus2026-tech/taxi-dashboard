# TAXI-MULTI-AGENT-01 / STAGE-A — архитектура совместной работы агентов

- Роль: Lead Architect (Claude Code)
- Режим: STRICT_READ_ONLY / DESIGN_ONLY
- Репозиторий: `iprus2026-tech/taxi-dashboard`
- Ветка: `checkpoint/taxi-dashboard-current-20261108`
- Baseline SHA: `8dc3402f84eb817266360fa83f66f01766ef4bc4` (подтверждён: `refs/heads/checkpoint/...` = `refs/pull/1/head`)
- Дата: 2026-11-08
- Статус: **TAXI-MULTI-AGENT-01 / STAGE-A_READY_FOR_OWNER_REVIEW**

Ничего не изменено: нет commit, push, merge, Issues, labels, Actions; production, данные, GPS и Mapbox не затронуты.

> **Решение владельца: STAGE-A ACCEPTED WITH CONDITIONS.**
> Архитектура из четырёх компонентов принята за основу. Обязательные исправления
> внесены в `docs/agents/PROTOCOL.md`, и **при расхождениях действует PROTOCOL.md**.
> Кратко:
> 1. Комментарии общего аккаунта не подтверждают личность владельца.
> 2. Owner Approval на Stage-B действует только процедурно; auto-merge и автоматический deploy запрещены.
> 3. CLAIM — заявка, а не атомарная блокировка; исполнителя подтверждает координатор (`ASSIGN`).
> 4. Истечение lease → `BLOCKED`, без автоматической передачи другому агенту.
> 5. Каждый артефакт = общедоступный адрес + SHA-256.
> 6. Порты 5001 (Mapbox Preview) и 5002 (резерв) исключены для нового QA, порт 5000 — production.
> 7. OWNER-DECISION всегда содержит точный утверждённый SHA.
> 8. Устаревший HANDOFF после изменения HEAD использовать нельзя.
> 9. `static/style.css` и `templates/index.html` входят в защищённые компоненты; пилот UI-STYLE может менять только `static/style.css`, и только после G0 и G1.
>
> **Ревизия R1 (по независимому аудиту DeepSeek Harness):**
> 10. На G0 владелец утверждает `issue_spec_sha256` канонической спецификации задачи. Перед ASSIGN, HANDOFF, QA и G2 хэш пересчитывается; изменение требований требует нового G0 (PROTOCOL §4.2).
> 11. Возобновление после обрыва сессии подтверждает только координатор сообщением `RESUME`; новая сессия не возобновляет работу сама (PROTOCOL §8.2).
> 12. Issue Form не активна, пока её нет в ветке по умолчанию `main`; план активации — PROTOCOL §12.
> 13. Labels 0/17 — BLOCKED. Stage-B не считается операционно готовым, пока labels не созданы (PROTOCOL §3, §13).
> 14. Автоматическое назначение агентов workflow'ом (§11 ниже) не разрешено: решение владельца запрещает автоматическое распределение задач.
>
> Текст ниже — исходная редакция Stage-A, сохранённая для истории. Места, изменённые
> решением владельца, отмечены «[изменено Stage-B]» или «[изменено Stage-B-R1]». Отменённые
> формулировки зачёркнуты. **Ни одна формулировка ниже не действует, если она расходится с PROTOCOL.md.**

---

## 1. Что сейчас есть в репозитории

### 1.1 Файлы в baseline (10 файлов)

| Файл | Строк | SHA-256 (содержимое файла) |
|---|---|---|
| `.gitignore` | 9 | `fa9891acba26145b4fc459a8df10f95a04127b9095c0703d90808178ae1f3c68` |
| `README-MAPBOX.md` | 163 | `73bb1f7dbb210487ca23fbae7b8b76b3d009c71d6804a069075e5aeb08f28869` |
| `README.md` | — | `82e4d3f0b7ccd9f09b00a96b104f23ae557fcb3019c7005b97efc8fcca1d16e0` |
| `app.py` | 683 | `353946a4f758cf7bbc2046f5dfe499c22db710862556a8eceff45120dc600515` |
| `bootstrap_storage.py` | 64 | `f348b50de5ead53efed0ebe1b1e11ddaf65c1345a515eab82696cd8901d8659c` |
| `static/mapbox-token.example.json` | 3 | `c4c7353f7ce35dfc9270e5da0035b35cc9fb81ccc29677953f68b89aea0d9175` |
| `static/script.js` | 2146 | `90f70d1f2858cd5da3b8ad15b95074e5b6ae1a94160359c881594fdf0df37df2` |
| `static/style.css` | 2377 | `ab947aee16a62ae14e1d060ce159bd5ef45b9e74c70d27216f5a158ccb335345` |
| `storage.py` | 549 | `08dfe2fff53147d293afa6d7af21462146847e34b51d335ddac59561c5784944` |
| `templates/index.html` | 543 | `3043c622b8033df2bf3ed6df021a92405fb6262087b429b6c933dcd4e71712ac` |

### 1.2 Состояние GitHub

- Issues: **0**. Project: нет. Каталога `.github/` нет: ни шаблонов, ни workflows, ни CODEOWNERS.
- PR: один, [iprus2026-tech/taxi-dashboard#1](https://github.com/iprus2026-tech/taxi-dashboard/pull/1) — draft `[CHECKPOINT]`, `checkpoint/...` → `main` (`main` = `0f8a939`).
- Collaborators: **один аккаунт** `iprus2026-tech` (admin).

### 1.3 Выводы, которые влияют на архитектуру

1. **Все агенты и владелец работают под одним GitHub-аккаунтом** (или через владельца, который пересылает сообщения). Поэтому по `assignee` или автору комментария нельзя понять, какой агент действовал. Исполнителя нужно обозначать **label'ом**, а авторство — **подписью внутри комментария**. Из-за этого Owner Approval сейчас нельзя обеспечить технически, только процедурой (см. §8 и риск R1).
2. **SQLite в репозитории нет.** Хранилище работает на JSON-файлах через `storage.py`: `driver_state.json`, `shift_history.json`, `storage_meta.json`, `.storage.lock`, `.storage_blocked.json`, и все они в `.gitignore`. Запрет «не трогать SQLite» оставляю в силе для production-окружения, но в коде под защиту попадают `storage.py`, `bootstrap_storage.py` и JSON-файлы данных.
3. **Нет ни тестов, ни CI.** `README-MAPBOX.md` ссылается на `tests/serve_isolated.py` и `artifacts/rollback/script.js.original`, но **этих файлов в baseline нет**. Независимый QA пока не может опереться на код в репозитории (риск R3).
4. Зоны с повышенным риском: GPS (`navigator.geolocation.watchPosition`, `script.js` ~стр. 891–911, `/api/track` в `app.py`) и Mapbox (`script.js` стр. 27–47, ~1780–1840, `mapbox-token*.json`).
5. Для пилота UI-STYLE удобно, что `style.css` уже держит дизайн-токены в `:root` (стр. 6–40). Но после `:root` в файле остаётся ~135 литеральных цветов (`#hex` и `rgba(`), так что смена стиля может задеть много мест.

---

## 2. Принципы минимальной архитектуры

- **Единственный источник правды — GitHub Issues.** Состояние задачи = labels + последний структурированный комментарий + HEAD ветки. Внешних БД, ботов, серверов и очередей нет.
- **Журнал = комментарии Issue.** Они упорядочены по времени, их timestamp ставит GitHub, а правки видны в истории. Отдельный файл журнала не нужен.
- **Целостность = SHA-256** для каждого переданного файла и git SHA для каждого состояния кода.
- **Автоматизация добавляется постепенно:** сначала протокол, который вручную ведёт GPT-координатор (Stage B), затем один проверяющий workflow (Stage C, только после отдельного разрешения).
- GitHub Project v2 **не обязателен**. Если нужен, то только как *представление* (доска по label `status:*`), а не как хранилище состояния.

---

## 3. Компоненты (их всего 4)

| # | Компонент | Где лежит | Этап |
|---|---|---|---|
| C1 | Набор labels (агенты, статусы, гейты) | настройки репозитория | B |
| C2 | Шаблон Issue-задачи (форма) | `.github/ISSUE_TEMPLATE/agent-task.yml` | B |
| C3 | Протокол: сообщения, переходы, восстановление | `docs/agents/PROTOCOL.md` | B |
| C4 | Workflow-валидатор (ничего не назначает сам, только проверяет и выставляет labels) | `.github/workflows/agent-guard.yml` + `tools/agent_guard.py` (stdlib) | C, опционально |

Сюда **не входят**: внешний оркестратор, отдельная БД задач, отдельный лог-файл в git, токены агентов в репозитории.

---

## 4. Роли и права

| Агент | Label | Может | Не может |
|---|---|---|---|
| Owner (человек) | `agent:owner` | создавать и закрывать задачи, проходить гейты, делать merge и deploy | — |
| GPT, координатор | `agent:gpt` | декомпозировать задачи, назначать `agent:*`, переводить статусы `backlog→ready`, следить за зависимостями и lease | писать код, делать merge, проходить Owner-гейты |
| Claude Code, архитектор и разработчик | `agent:claude-code` | писать код в своей ветке, публиковать HANDOFF, открывать draft PR | делать merge, ставить `status:qa-passed`, менять файлы вне scope |
| Claude Design, визуальный дизайн | `agent:claude-design` | выпускать спецификации и макеты (файлы + SHA-256) | менять код в репозитории |
| DeepSeek Harness, независимый QA | `agent:deepseek-qa` | проверять, выставлять вердикт PASS/FAIL | исправлять проверяемый код, проверять свою же работу |

**Один исполнитель:** на открытой задаче всегда ровно один label `agent:*`. Сменить его может только координатор или владелец, и только с комментарием `REASSIGN`.

**Relay-режим:** агенты без доступа к GitHub (GPT, Claude Design, DeepSeek) отдают структурированный блок (§6), и владелец вставляет его комментарием как есть. Подпись `agent:` внутри блока считается авторством. [изменено Stage-B-R1]: подпись не проверяется технически и не подтверждает личность (PROTOCOL §0.1).

---

## 5. Модель задачи

### 5.1 Идентификатор и ветка

- ID: `TAXI-<AREA>-<NN>[.<step>]`, например `TAXI-UI-STYLE-01.2`. ID ставится первым в заголовке Issue: `[TAXI-UI-STYLE-01.2] ...`.
- Ветка: `agent/<agent>/<id-lowercase>`, например `agent/claude-code/taxi-ui-style-01.2`. В неё пишет только агент-исполнитель. Ветка ответвляется от `base_sha`, который указан в Issue.

### 5.2 Поля шаблона Issue (C2)

```
Task ID:            TAXI-UI-STYLE-01.2
Parent:             #<n>
Agent (one):        claude-code
Depends on:         #<n>, #<m>           # все должны быть status:done
Base SHA:           8dc3402f…
Allowed paths:      static/style.css
Forbidden paths:    app.py, storage.py, bootstrap_storage.py, static/script.js,
                    static/mapbox-token*.json, *.json data, .github/**
Acceptance criteria: - …
Owner gate:         none | G1-design | G2-merge | G3-deploy
Lease:              24h
```

### 5.3 Labels (C1)

- Исполнитель: `agent:owner`, `agent:gpt`, `agent:claude-code`, `agent:claude-design`, `agent:deepseek-qa`
- Статус (ровно один): `status:backlog`, `status:ready`, `status:in-progress`, `status:handoff`, `status:qa`, `status:owner-gate`, `status:done`, `status:blocked`
- Гейт: `gate:G1-design`, `gate:G2-merge`, `gate:G3-deploy`
- Защищённые зоны (помечают задачи, которые их касаются): `zone:gps`, `zone:mapbox`, `zone:storage`. Любая задача с `zone:*` автоматически получает `gate:G2-merge`.

### 5.4 Машина состояний

```
backlog ──(GPT: зависимости done, scope не пересекается)──► ready
ready ──(агент: CLAIM)──► ~~in-progress~~ ready; координатор: ASSIGN ──► in-progress   [изменено Stage-B-R1, PROTOCOL §4.1]
in-progress ──(агент: HANDOFF)──► handoff
handoff ──(GPT: назначает QA-задачу)──► qa
qa ──(DeepSeek: QA-REPORT PASS)──► owner-gate | done (если gate=none)
qa ──(FAIL)──► in-progress (тот же исполнитель, новый цикл)
owner-gate ──(Owner: OWNER-DECISION APPROVE <sha>)──► done
owner-gate ──(REJECT)──► in-progress | blocked
any ──(lease истёк / нет связи)──► blocked ──(RESUME или REASSIGN)──► in-progress
```

---

## 6. Протокол сообщений (журнал + передача + SHA-256)

Каждый значимый шаг оформляется **одним комментарием** в Issue с fenced-блоком. Первая строка блока — тип сообщения. Свободный текст вне блока допускается, но не является частью протокола.

### 6.1 CLAIM (захват задачи)

````
```agent-msg
type: CLAIM
v: 1
task: TAXI-UI-STYLE-01.2
agent: claude-code
session: <id сессии / чата>
base_sha: 8dc3402f84eb817266360fa83f66f01766ef4bc4
branch: agent/claude-code/taxi-ui-style-01.2
lease_until: 2026-11-09T21:00:00Z
```
````

[изменено Stage-B-R1]: в CLAIM нет `lease_until`. Lease назначает координатор в `ASSIGN` или `RESUME` (PROTOCOL §5.1–5.2).

### 6.2 CHECKPOINT (прогресс, используется для восстановления)

```
type: CHECKPOINT
task: …   agent: …   session: …
head_sha: <git sha последнего push>
done: [шаги]
next: [шаги]
lease_until: …
```

### 6.3 HANDOFF (передача результата)

```
type: HANDOFF
v: 1
task: TAXI-UI-STYLE-01.2
from: claude-code
to: deepseek-qa
base_sha: 8dc3402f…
head_sha: <commit>
branch: agent/claude-code/taxi-ui-style-01.2
changed_files:
  - path: static/style.css
    sha256: <64 hex>          # sha256 файла в head_sha
artifacts:                     # для файлов вне git (макеты, скриншоты)
  - name: mockup-driving-dark.png
    sha256: <64 hex>
    location: <ссылка-вложение / путь>
self_checks: [что проверено автором, с результатом]
known_limits: [что НЕ проверено — NOT RUN]
```

Правила:
- `changed_files` = в точности `git diff --name-only base_sha..head_sha`. Каждый путь должен входить в `Allowed paths`.
- SHA-256 считается от байтов файла в `head_sha`: `git show <head_sha>:<path> | sha256sum`.
- Если после HANDOFF появился новый commit, предыдущий HANDOFF недействителен и нужен новый.

### 6.4 QA-REPORT

```
type: QA-REPORT
task: TAXI-UI-STYLE-01.3
reviews: TAXI-UI-STYLE-01.2 @ <head_sha>
agent: deepseek-qa
hash_check: PASS | FAIL (по каждому файлу)
scope_check: PASS | FAIL
checks:
  - id: AC-1  result: PASS  evidence: <sha256 скриншота/лога>
verdict: PASS | FAIL
environment: <ОС, браузер, порт, изолированное хранилище: да>
```

### 6.5 OWNER-DECISION

```
type: OWNER-DECISION
task: …   gate: G1-design | G2-merge | G3-deploy
decision: APPROVE | REJECT | CHANGES
approved_sha: <git sha или sha256 артефакта>   # [изменено Stage-B-R1]: раздельные поля approved_sha / approved_sha256 / approved_spec_sha256 / spec_sha256 — PROTOCOL §5.6
note: …
```

Решение относится **только** к `approved_sha`. Если что-то меняется после одобрения, гейт нужно проходить заново.

### 6.6 Служебные: `REASSIGN`, `RESUME`, `RELEASE`, `BLOCKED` (поля: task, agent, reason, head_sha).

---

## 7. Защита от дублирования и конфликтов

1. **Один исполнитель:** ровно один `agent:*` и ровно один `status:*` на задаче.
2. **Захват:** брать можно только задачу в `status:ready`, где `agent:*` совпадает с собой. ~~Если CLAIM-комментариев несколько, действует первый по времени GitHub~~ [изменено Stage-B]: CLAIM — только заявка; исполнителя подтверждает координатор сообщением `ASSIGN`, остальные заявители публикуют `RELEASE` (PROTOCOL §0.3, §5.2).
3. **Lease:** ~~CLAIM и~~ CHECKPOINT продлевают аренду [изменено Stage-B-R1: аренду выдаёт координатор в ASSIGN или RESUME, CHECKPOINT продлевает её только до истечения], по умолчанию на 24 часа. Если она истекла, координатор переводит задачу в `blocked` и решает, что дальше: `RESUME` тем же агентом или `REASSIGN`. [изменено Stage-B]: истечение lease никогда не передаёт задачу автоматически (PROTOCOL §8.1).
4. **Конфликты файлов:** две задачи в `in-progress` или `handoff` не могут иметь пересекающиеся `Allowed paths`. Координатор проверяет это до перехода в `ready`. Для пилота `static/style.css` занимает одна задача.
5. **Отдельная ветка на задачу** + fast-forward/PR только владельцем. Агенты не пишут в `main` и `checkpoint/*`.
6. **Дубликаты задач:** перед созданием задачи ищется её ID в заголовках. Если ID уже есть, новая задача не создаётся.

---

## 8. Зависимости и Owner Approval Gates

- **Зависимости** записываются в поле `Depends on` (и/или во встроенных связях GitHub «blocked by» и sub-issues). Задача становится `ready` только когда все зависимости в `status:done`. Это проверяет координатор, а на Stage C ещё и workflow.
- **Гейты:**
  - **G0, приём задачи:** владелец утверждает scope и Allowed paths родительской задачи до декомпозиции.
  - **G1, дизайн:** владелец утверждает спецификацию и макеты (по sha256) до начала реализации.
  - **G2, merge:** владелец сам делает merge PR после QA PASS.
  - **G3, deploy:** владелец сам разворачивает в production. Агенты production не трогают никогда.
- **Ограничение (R1):** аккаунт один, поэтому GitHub не отличит OWNER-DECISION владельца от сообщения агента. Пока это решается процедурой: (а) merge и deploy физически делает только владелец; (б) агентам запрещено публиковать `OWNER-DECISION`; (в) координатор и QA считают недействительным `OWNER-DECISION`, если он пришёл в relay-блоке от агента. Надёжное решение (Stage C+): отдельный machine-user или GitHub App для агентов + branch protection на `main` (merge только через PR, approve только владельцем).

---

## 9. Независимый QA

- QA получает **только** HANDOFF (head_sha, хэши, критерии приёмки), без переписки исполнителя.
- Порядок проверки:
  1. Пересчитать SHA-256 всех `changed_files` и `artifacts`.
  2. Сравнить `git diff --name-only base..head` с `Allowed paths`.
  3. Проверить, что `Forbidden paths` побайтно совпадают с baseline (хэши из §1.1).
  4. Пройти критерии приёмки.
  5. Опубликовать QA-REPORT.
- Запуск только **в изолированной копии**: другой порт ~~(5001)~~ [изменено Stage-B: 5000, 5001 и 5002 запрещены, порт задаётся в QA-задаче — PROTOCOL §7.4], временный каталог хранилища, никаких production JSON и настоящего Mapbox-токена (при отсутствии токена приложение откатывается на OSM).
- QA не исправляет код. Если проверка провалена, задача возвращается исполнителю.
- Исполнитель не может проверять собственную задачу. Если DeepSeek недоступен, задача ждёт в `qa`, обходного пути нет.

---

## 10. Восстановление после обрыва сессии

Всё состояние лежит в GitHub, поэтому новая сессия любого агента восстанавливается так:

> [изменено Stage-B-R1] Порядок ниже **отменён** и заменён PROTOCOL §8.2: новая сессия никогда не публикует `RESUME` и не продолжает работу сама. Она фиксирует состояние сообщением `BLOCKED` и ждёт `RESUME` от координатора с новым `session` и проверкой `issue_spec_sha256`.

1. Открыть Issue и прочитать labels: `agent:*` (это я?) и `status:*`.
2. Найти последний `CLAIM`, `CHECKPOINT` или `HANDOFF` в комментариях.
3. Сверить `head_sha` из комментария с текущим HEAD ветки:
   - **совпадает** → ~~опубликовать `RESUME` (новый session id) и продолжать с `next`~~ [изменено Stage-B-R1]: опубликовать `BLOCKED (session_lost)` и ждать `RESUME` от координатора;
   - **HEAD впереди** → незафиксированный прогресс прежней сессии; ~~проверить diff, затем опубликовать CHECKPOINT~~ [изменено Stage-B-R1]: ничего не пушить, опубликовать `BLOCKED` с фактическим HEAD, решает координатор;
   - **HEAD позади или ветки нет** → `BLOCKED` и решение координатора.
4. Если lease истёк, а задача уже передана другому агенту (`REASSIGN`), прежний агент ничего не делает.
5. Агент без доступа к GitHub получает от владельца стандартную «вставку восстановления»: ссылку на Issue + последний блок `agent-msg`.

---

## 11. Автоматическое распределение (поэтапно)

- **Stage B (без Actions):** распределяет GPT-координатор по таблице маршрутизации, владелец применяет labels.

  | Тип работы | Агент по умолчанию |
  |---|---|
  | визуальная спецификация, макеты | claude-design |
  | код, архитектура, PR | claude-code |
  | проверка, тест-план, вердикт | deepseek-qa |
  | декомпозиция, статусы, зависимости | gpt |
  | гейты, merge, deploy | owner |

- **Stage C (после разрешения):** один workflow `agent-guard.yml`, только `GITHUB_TOKEN`, без секретов и без доступа к production. Он срабатывает на `issues`, `issue_comment` и `pull_request` и делает следующее:
  - проверяет инварианты: ровно один `agent:*`/`status:*`, зависимости закрыты перед `ready`, формат блоков `agent-msg`;
  - ~~при `status:ready` без `agent:*` ставит агента по label типа работы (таблица выше)~~ [изменено Stage-B-R1: автоматическое распределение задач запрещено решением владельца];
  - в PR сверяет diff с `Allowed paths`, пересчитывает SHA-256 из HANDOFF, проверяет неизменность `Forbidden paths`;
  - при нарушении ставит `status:blocked` и пишет комментарий с причиной.

  Workflow **никогда** не делает merge, deploy и не проходит гейты.

---

## 12. Пилот: TAXI-UI-STYLE-01

> [изменено Stage-B] Предварительно согласованный scope и ограничения пилота см. в PROTOCOL §10: реализация только в `static/style.css`, изменения HTML и JS — отдельной задачей с разрешением, запуск после G0, дизайн проходит G1.

Точное содержание стилевой задачи владелец ещё не описал, поэтому scope ниже — предложение, его нужно подтвердить на G0.

| Issue | Агент | Зависит от | Allowed paths | Результат | Гейт |
|---|---|---|---|---|---|
| **TAXI-UI-STYLE-01** (родитель) | gpt | — | — | декомпозиция, контроль | G0 |
| **01.1** Визуальная спецификация | claude-design | G0 | вне git (артефакты) | токены (цвета, радиусы, тени, типографика), макеты: дашборд, «за рулём», история, модалка; viewports 1280×800, 800×1280, 390×844; sha256 каждого файла | **G1** |
| **01.2** Реализация | claude-code | 01.1 + G1 | `static/style.css` (если понадобится разметка — отдельная подзадача с разрешением на `templates/index.html`) | ветка `agent/claude-code/taxi-ui-style-01.2`, draft PR → `checkpoint/...`, HANDOFF | — |
| **01.3** Независимый QA | deepseek-qa | 01.2 | — | QA-REPORT: хэши, scope, скриншоты в 3 viewports × 4 экрана, сравнение с макетами 01.1, `prefers-reduced-motion`, контраст текста, нет ошибок в консоли, GPS-кнопки и карта работают (OSM-fallback без токена) | — |
| **01.4** Решение о merge | owner | 01.3 PASS | — | OWNER-DECISION G2 по head_sha | **G2** |

Forbidden paths на весь пилот: `app.py`, `storage.py`, `bootstrap_storage.py`, `static/script.js`, `static/mapbox-token*.json`, `templates/index.html` (пока нет отдельного разрешения), файлы данных `*.json`, `.github/**`. Их хэши из §1.1 являются эталоном для QA.

Пилот считается успешным, если:
- задачи прошли весь цикл без ручного выяснения «кто это делал»;
- все HANDOFF воспроизводимы по хэшам;
- QA проверил результат независимо от исполнителя;
- была хотя бы одна имитация восстановления: новая сессия Claude Code продолжила работу по CHECKPOINT.

---

## 13. Риски и открытые вопросы для владельца

| ID | Риск / вопрос | Предложение |
|---|---|---|
| R1 | Один GitHub-аккаунт: авторство и гейты не обеспечиваются технически | Пилот провести на процедуре; затем решить, нужен ли machine-user или GitHub App и branch protection |
| R2 | В коде нет SQLite (только JSON); формулировку запрета нужно уточнить | Подтвердить, что под запретом `storage.py`, `bootstrap_storage.py`, JSON-данные и production-БД, если она есть вне репозитория |
| R3 | Нет тестов; `tests/serve_isolated.py` и `artifacts/rollback/*` упомянуты в README-MAPBOX, но отсутствуют | Отдельная задача (claude-code → QA): вернуть или создать изолированный запуск для QA |
| R4 | Каждый пилотный шаг на Stage B потребует ручного relay | Допустимо для пилота; Stage C снимет часть нагрузки |
| Q1 | Цель пилота: в какую ветку делать PR, `checkpoint/...` или `main`? Сейчас открыт draft [iprus2026-tech/taxi-dashboard#1](https://github.com/iprus2026-tech/taxi-dashboard/pull/1) checkpoint→main | Предлагаю: пилотные PR в `checkpoint/...`, слияние с `main` отдельным решением владельца |
| Q2 | Нужен ли GitHub Project v2 как визуальная доска? | Опционально, только как представление |
| Q3 | Конкретное содержание TAXI-UI-STYLE-01 | Владелец описывает на G0 |

---

## 14. Следующие этапы (каждый — только с отдельного разрешения)

- **STAGE-B:**
  - создать labels (C1);
  - в ветке `claude/happy-meitner-9mir0r` (или другой, указанной владельцем) добавить `.github/ISSUE_TEMPLATE/agent-task.yml` (C2) и `docs/agents/PROTOCOL.md` (C3), открыть draft PR;
  - после merge создать Issues пилота. [изменено Stage-B-R1: только после выполнения всех условий операционной готовности, PROTOCOL §13]
- **STAGE-C:** `agent-guard.yml` + `tools/agent_guard.py`, затем решение по R1.
- **Пилот:** провести TAXI-UI-STYLE-01 по §12.

**TAXI-MULTI-AGENT-01 / STAGE-A_READY_FOR_OWNER_REVIEW** — работа остановлена до решения владельца.
