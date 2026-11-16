---
name: taxi-preflight
description: Read-only gate check for Taxi Dashboard agent tasks under docs/agents/PROTOCOL.md v1. Use before CLAIM, before the first write after ASSIGN, before HANDOFF, and when a new session finds an in-progress or blocked task. Rebuilds the canonical TAXI-ISSUE-SPEC/1 and its SHA-256 from the live Issue, checks the owner G0 and target_branch, Base/main, CLAIM/ASSIGN session fencing, lease, and conflicting branches, PRs, worktrees and scopes. Returns PASS, STOP, BLOCKED or NOT_VERIFIED. It never grants G0, ASSIGN, G2/G3, merge or deploy, and never writes OWNER-DECISION.
---

# taxi-preflight — проверка предусловий задачи (протокол v1)

Канонический источник этого навыка — файл `.agents/skills/taxi-preflight/SKILL.md`. Адаптер `.claude/skills/taxi-preflight/SKILL.md` только указывает сюда и собственных правил не содержит.

## 0. Статус и иерархия документов

- Нормативный документ — **`docs/agents/PROTOCOL.md` v1**. Этот навык лишь пересказывает порядок проверки и **ничего не добавляет к протоколу и не отменяет в нём**. Если навык расходится с PROTOCOL.md v1, прав PROTOCOL.md v1, а расхождение записывается в отчёт как дефект навыка.
- **`docs/agents/v2/**` имеет статус `DRAFT / NOT ACTIVE`**. Сообщения `CLAIM/2`, `ASSIGN/2`, `RESUME/2`, `HANDOFF/2`, `QA-REPORT/2` по реальным задачам недействительны. Ссылка на v2 как на действующие правила — повод для `BLOCKED (protocol_v2_not_active)`.
- Навык — **процедурная справка, а не полномочие**. Он не выдаёт G0, ASSIGN, RESUME, REASSIGN, G2 или G3, не делает merge и deploy, не меняет labels и статусы. Без явного поручения он ничего не публикует в GitHub.
- Агент **никогда** не составляет и не публикует `OWNER-DECISION` от имени владельца, даже как «черновик для владельца» (PROTOCOL v1 §0.2, §5.6).

## 1. Когда применять

- **WHEN:**
  - перед публикацией `CLAIM` — режим `READ_ONLY_PREFLIGHT`;
  - после `ASSIGN`, перед первой записью (ветка, файл, commit, draft PR) — режим `PRE_WRITE`;
  - перед публикацией `HANDOFF` — режим `PRE_HANDOFF`;
  - когда новая сессия находит задачу в `in-progress` или `blocked` (§8.2) — режим `RECOVERY`;
  - QA-задача перед началом проверки и перед публикацией отчёта: этот навык как первый шаг, затем `taxi-evidence-qa`.
- **WHEN NOT:**
  - для выдачи или подделки решений владельца или координатора (G0, ASSIGN, RESUME, G2, G3);
  - как замена независимого QA — для доказательств есть `taxi-evidence-qa`, для кода нужна отдельная QA-задача;
  - для задач по протоколу v2;
  - для production, планшета, GPS, Car-Jukebox и сервисов: навык их не касается и не разрешает к ним доступ;
  - когда Issue нет и задача сформулирована только в чате: результат `BLOCKED (no_issue)`.

## 2. Входные данные

| Вход | Откуда | Если нет |
|---|---|---|
| номер Issue и Task ID | поручение человека или координатора | `BLOCKED (no_issue)` |
| своя роль (`agent:`) | назначение | `BLOCKED (role_unknown)` |
| фактический ID сессии | платформа (см. §3, шаг S1) | `BLOCKED (session_unknown)` |
| режим | `READ_ONLY_PREFLIGHT`, `PRE_WRITE`, `PRE_HANDOFF` или `RECOVERY` | по умолчанию `READ_ONLY_PREFLIGHT` |
| текущее время UTC | системные часы | при сомнении в часах — `NOT_VERIFIED` для lease |

## 3. Процедура (только чтение)

Все шаги выполняются **заново в текущей сессии** по первичным источникам: GitHub API или коннектор, `git ls-remote`, файлы на закреплённом commit. Цитаты из чата, таблицы координатора и отчёты других агентов — это ожидаемые значения, а не доказательства. Порядок шагов фиксирован. Если обязательный шаг дал не `PASS`, итог не может быть `PASS`.

Используйте только инструменты, разрешённые в своей среде. Например, в облачной сессии Claude Code к GitHub обращаются через MCP-инструменты, а `gh` — только для поиска. Обходить ограничения прокси или сети запрещено: недоступный источник даёт `NOT_VERIFIED`, а не обходной путь.

**S0. Действующий протокол.** Прочитать `docs/agents/PROTOCOL.md` на `origin/<target_branch>`. Убедиться, что v2 помечен `DRAFT / NOT ACTIVE` (`docs/agents/v2/README.md` §1). Любое сообщение задачи с `v: 2` или типом `*/2` недействительно.

**S1. Сессия.** Узнать **фактический** ID своей сессии от платформы, а не придумать его:
- Claude Code Remote — инструмент `get_session` (поле `id`);
- DeepSeek Harness — `DSH_SESSION_ID` и метаданные сессии (`isSeeded`, `inheritedEventCount`, `parentSession`);
- Codex и другие платформы — их штатный способ. Если способа нет, записать `NOT_VERIFIED (session_id_source)` и сообщить координатору до CLAIM.

Раскрыть родительские сессии, общий хост, рабочее пространство и учётные данные, если они есть. Общий аккаунт GitHub `iprus2026-tech` личность **не подтверждает** (§0.1).

**S2. Issue.** Issue открыт. Ровно один label `agent:*`, и он совпадает с ролью исполнителя. Статус допустим для режима:

| Режим | Допустимый статус |
|---|---|
| `READ_ONLY_PREFLIGHT` | `ready` |
| `PRE_WRITE`, `PRE_HANDOFF` | `in-progress` |
| `RECOVERY` | `in-progress` или `blocked` |

Поиск по Task ID должен находить ровно одно Issue. Текст вне канонической формы (например, устаревший раздел Status) на SPEC не влияет, но несоответствие записывается в отчёт.

**S3. Каноническая SPEC (§4.2).** Построить `TAXI-ISSUE-SPEC/1` из **текущего** тела Issue:
1. Взять только поля `task_id`, `base_sha`, `depends_on`, `allowed_paths`, `forbidden_paths`, `acceptance`, `gates` из соответствующих разделов Issue Form. Порядок полей — как в списке.
2. Скаляры вида `ключ: значение` без обрамляющих обратных кавычек. Списки — строка `ключ:`, затем строки `- элемент`.
3. В `depends_on` — Task ID без повторов, отсортированные побайтно; пусто → `- none`. В `allowed_paths` и `forbidden_paths` — пути без `./` и ведущего `/`, без повторов, отсортированные побайтно; пояснительный текст после блока путей в форму не входит. `allowed_paths` пусто → `- none`; `forbidden_paths` пустым быть не может.
4. В `acceptance` — элементы `AC-<n>: <текст>`, n = 1..k подряд. Текст в одну строку, последовательности пробелов сжаты до одного.
5. В `gates` — подмножество `G0-intake`, `G1-design`, `G2-merge`, `G3-deploy` в этом порядке.
6. Байты: UTF-8 без BOM, Unicode NFC, только LF, без табуляций, без пробелов в начале и конце строк, без пустых строк, первая строка `TAXI-ISSUE-SPEC/1`, ровно один завершающий LF.
7. `issue_spec_sha256` = SHA-256 этих байтов. Записать длину в байтах.

**Самопроверка реализации обязательна:** проверочный вектор §4.2 (495 байт) должен дать `f9b02543d760371607e263bc8b1f00c0e2030b9d074cf159899f7e716e7456cd`. Иначе — `NOT_VERIFIED (canonicalizer)`, сравнивать хэши нельзя.

Затем сравнить:
- с блоком `issue-spec` последнего действующего сообщения `SPEC` — оно не редактировалось (`created_at = updated_at`), а цепочка `supersedes` прослежена до конца;
- с `approved_spec_sha256` в G0 (S4).

Любое расхождение → `BLOCKED (spec_changed)`. Работа и передача результата прекращаются до новой пары `SPEC` + G0 (§4.2 п.4–5). Старый G0 на новый хэш не распространяется.

**S4. G0 (§5.6, §4.3).** Найти `OWNER-DECISION` с `gate: G0-intake`, `decision: APPROVE` и `approved_spec_sha256`, равным хэшу из S3 (полные 64 hex). Комментарий не редактировался. В `note` есть строка `target_branch: <ветка>`; без неё G0 недействителен для ASSIGN (§4.3 п.2). Сверить остальные ограничения `note` (роль, scope, запреты) с планируемыми действиями.

- G0 нет → `BLOCKED (g0_missing)`.
- G0 опубликован агентом или пришёл в relay от агента → недействителен.
- Сообщение координатора «владелец подтвердил в чате» — это квитанция координатора, а не `OWNER-DECISION`. Её можно учитывать как контекст, но G0 она не заменяет.
- Отметка `gate:G0-intake` в Issue — тоже не решение (T35).

**S5. Base и целевая ветка (§4.3).**
- `base_sha` — полные 40 hex.
- `git ls-remote origin refs/heads/<target_branch>` записывается как фактический HEAD.
- `git merge-base --is-ancestor <base_sha> origin/<target_branch>` возвращает 0. Иначе SPEC недействителен → `BLOCKED (base_not_ancestor)`.
- Если целевая ветка ушла вперёд после G0, Base **не меняется** (§4.3 п.7). Это записывается в отчёт, но провалом не является.
- Смена `target_branch` после G0 без нового G0 → `BLOCKED (target_changed)`.

**S6. CLAIM, ASSIGN и fencing (§0.3, §5.1, §5.2).** Найти все `CLAIM`, `ASSIGN`, `RESUME`, `REASSIGN`, `RELEASE`, `BLOCKED` и `CHECKPOINT` задачи. Порядок определяется по `created_at` GitHub, а не по внутреннему `ts`.

| Режим | Требования |
|---|---|
| `READ_ONLY_PREFLIGHT` | Своих CLAIM ещё нет: допускается **ровно один**. Чужие CLAIM и ASSIGN раскрываются; при действующем ASSIGN на другую сессию — `STOP`. CLAIM — заявка, а не блокировка. |
| `PRE_WRITE` | Последний действующий `ASSIGN` от `agent: gpt` — отдельный комментарий, не редактировался. `claim_session` = фактическая сессия из S1. `spec_sha256` = хэш из S3 = G0. `base_sha` = Base. `branch` = планируемая ветка. Позднее нет `REASSIGN`, `BLOCKED` или `RELEASE`, которые его отменяют. |
| `PRE_HANDOFF` | Всё из `PRE_WRITE`, плюс S3 и S4 пересчитаны **непосредственно перед** HANDOFF. HEAD ветки = commit, который будет указан в HANDOFF. |
| `RECOVERY` | §8.2: сравнить `head_sha` последнего ASSIGN, RESUME, CHECKPOINT или HANDOFF с `git ls-remote origin <branch>`. В любом случае подготовить `BLOCKED` и ждать `RESUME` от координатора с **новой** сессией. Самостоятельный `RESUME` недействителен. |

Чужая или неизвестная сессия, ASSIGN без указания сессии, «посеянная» или возобновлённая сессия без RESUME → `STOP`. Работать может только сессия из `claim_session`.

**S7. Lease (§8.1).**
- `now_utc < lease_until` строго, по UTC. Сравнивать с `lease_until` из **последнего** действующего ASSIGN, RESUME или CHECKPOINT.
- Срок lease не больше максимума, указанного в Issue или G0.
- CHECKPOINT продлевает lease только до его истечения.
- Истёк → `BLOCKED (lease_expired)`. Неявного продления нет, автоматической передачи задачи нет.
- Новый ASSIGN, который сохраняет прежний `lease_until`, срок **не продлевает**.

**S8. Конфликты.**
- Удалённые ветки задачи (`git ls-remote origin`).
- Открытые PR из этих веток.
- Другие открытые Issues в статусах `in-progress`, `handoff`, `qa`: их `Allowed paths` не должны пересекаться с нашими (§4). Пересечение glob-шаблонов, которое не удаётся однозначно исключить, считается конфликтом.
- Локальные worktree (`git worktree list`) и незакоммиченные изменения: чужие не трогать.
- Служебная ветка окружения, если она есть, раскрывается и **не получает** коммитов задачи.

Конфликт → `STOP (conflict)` и раскрытие координатору.

**S9. Пути.** Каждый планируемый к изменению путь входит в `allowed_paths` и не совпадает ни с одним `forbidden_paths`. Перед HANDOFF то же проверяется для `git diff --name-only <base_sha>..<head_sha>`.

## 4. Семантика результатов

| Результат | Значение | Что делать |
|---|---|---|
| `PASS` | проверено по первичному источнику в этой сессии | переходить к следующему шагу |
| `NOT_VERIFIED (<что>)` | проверить не удалось: нет доступа, инструмент запрещён, источник недоступен | для обязательного шага итог — `BLOCKED`; обходов нет |
| `BLOCKED (<причина>)` | предусловия нет или оно изменилось | никаких записей; подготовить черновик `BLOCKED` |
| `STOP` | конфликт, чужая сессия, неясная полномочность | остановиться, раскрыть, ждать координатора |

Итог отчёта: `PASS`, только если все обязательные шаги S0–S9 для режима дали `PASS`. Иначе берётся самый строгий результат (`STOP` > `BLOCKED` > `NOT_VERIFIED`).

## 5. Режимы и их границы

- **`READ_ONLY_PREFLIGHT`** — только чтение. Разрешено одно действие записи: **один** `CLAIM/1`, и только если поручение явно просит его опубликовать. После CLAIM — `STOP` до ASSIGN. Ни веток, ни файлов, ни коммитов, ни PR.
- **`PRE_WRITE`** — при `PASS` разрешено то, что прямо перечислено в ASSIGN: обычно ветка `agent/<agent>/<id-lowercase>` строго от `base_sha`, файлы только из `allowed_paths`, draft PR в `target_branch`.
- **`PRE_HANDOFF`** — при `PASS` разрешён один `HANDOFF/1` по §6. HANDOFF действует, пока HEAD ветки = `head_sha` (§6.4).
- **`RECOVERY`** — только `BLOCKED` с фактическим HEAD, затем ждать `RESUME`.

## 6. Шаблон отчёта (черновик, в чат или поручающему)

```text
TAXI-PREFLIGHT REPORT
task: <Task ID>  issue: #<n>  mode: <режим>
role: <agent>  session: <фактический id>  source: <как получен>
now_utc: <ISO 8601>
S0 protocol: v1 normative; v2 DRAFT/NOT ACTIVE -> PASS|...
S1 session: <id>; disclosures: <...> -> PASS|NOT_VERIFIED
S2 issue: labels=<...> status=<...> dup_search=<n> -> PASS|BLOCKED
S3 spec: <bytes> bytes, sha256=<64hex>; vector=<PASS|FAIL>; spec_ref=<url> -> PASS|BLOCKED(spec_changed)
S4 g0: ref=<url> approved=<64hex> target_branch=<ветка> -> PASS|BLOCKED(g0_missing)
S5 base: base=<40hex> target_head=<40hex> ancestor=<0|1> -> PASS|BLOCKED
S6 fencing: claim=<url> assign=<url> claim_session=<id> -> PASS|STOP
S7 lease: lease_until=<ISO> -> PASS|BLOCKED(lease_expired)
S8 conflicts: branches=<...> prs=<...> scopes=<...> worktrees=<...> -> PASS|STOP
S9 paths: <список> -> PASS|BLOCKED
NOT_VERIFIED: <что и почему>
RESULT: PASS | STOP | BLOCKED(<reason>) | NOT_VERIFIED
NEXT: <единственное разрешённое следующее действие или "ждать координатора">
```

Черновики сообщений `CLAIM`, `BLOCKED` и `RELEASE` составляются по форматам §5.1 и §5.7. Публикуются они только по поручению: отдельным комментарием, без последующей правки. Если внутренний `ts` разошёлся с `created_at`, это раскрывается, а не исправляется.

## 7. Запреты, которые навык не снимает

Нельзя: auto-merge, merge и deploy агентом; G2 и G3; запись `OWNER-DECISION`; правка опубликованных сообщений протокола; изменения вне `allowed_paths`; доступ к production-данным, планшету, GPS, Car-Jukebox, портам и секретам; включение протокола v2; GitHub Actions и автоматическое распределение задач (§0.8).
