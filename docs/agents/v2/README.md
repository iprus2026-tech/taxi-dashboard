# Протокол агентов Taxi Dashboard v2 — нормативный контракт (черновик)

- Задача: `TAXI-AGENT-PROTOCOL-V2-IMPL-01` ([Issue #26](https://github.com/iprus2026-tech/taxi-dashboard/issues/26))
- SPEC/1: [#6830894759](https://github.com/iprus2026-tech/taxi-dashboard/issues/26#issuecomment-6830894759), `issue_spec_sha256` `1239d9897b721482a923bb713729c00828a648fbf943d6718259f0619f5a1ba2`
- Личный OWNER G0: [#6831274083](https://github.com/iprus2026-tech/taxi-dashboard/issues/26#issuecomment-6831274083) (`target_branch: main`, `scope: DOCS_ONLY`, `v2_activation: forbidden`)
- Base SHA: `48b0454d3b68f90e7687bd00b2ccc5a9318f6d70`
- Автор: `claude-code`, сессия `claude-code-session_01UHQjyd5XEFZ66Ye4Xg8CG3`, [ASSIGN #6831703608](https://github.com/iprus2026-tech/taxi-dashboard/issues/26#issuecomment-6831703608)
- Ревизия: `TAXI-AGENT-PROTOCOL-V2-REWORK-01` ([Issue #28](https://github.com/iprus2026-tech/taxi-dashboard/issues/28)), личный OWNER G0 [#6836138282](https://github.com/iprus2026-tech/taxi-dashboard/issues/28#issuecomment-6836138282), исходный HEAD `47872072a4be6f5dc4aa6ffdb296ff7f58ef1ae7`, сессия `session_01UHQjyfBPVwEsksRKHAxcJL`, [ASSIGN #6836474247](https://github.com/iprus2026-tech/taxi-dashboard/issues/28#issuecomment-6836474247). См. §9
- Ревизия F4: `TAXI-AGENT-PROTOCOL-V2-F4-WIRE-01` ([Issue #32](https://github.com/iprus2026-tech/taxi-dashboard/issues/32)), личный OWNER G0 [#6850660930](https://github.com/iprus2026-tech/taxi-dashboard/issues/32#issuecomment-6850660930), Base `cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059`, сессия `session_01UHQjybzrunmUVCwurrxXj2`, [ASSIGN #6851942229](https://github.com/iprus2026-tech/taxi-dashboard/issues/32#issuecomment-6851942229). См. §10

## 1. Статус: `DRAFT / NOT ACTIVE`

**Этот каталог не меняет действующий порядок работы.** Действующий протокол — `docs/agents/PROTOCOL.md` v1. Он не изменён и остаётся единственным нормативным документом для всех текущих задач. При любом расхождении между v1 и этим каталогом для реальных задач действует v1.

Пока v2 не активирован:

- сообщения `CLAIM/2`, `ASSIGN/2`, `RESUME/2`, `HANDOFF/2`, `QA-REPORT/2` по реальным задачам **недействительны**;
- ни одна задача v1 не превращается в задачу v2. RESUME v1 в RESUME/2 не преобразуется;
- все проверки здесь процедурные: общий аккаунт GitHub не подтверждает личность (v1 §0.1).

## 2. Граница этапа и активация

Этот этап — **только документация** в `docs/agents/v2/**`. Валидаторы, тесты, GitHub Actions, код приложения, `PROTOCOL.md` v1 и исторические Issues не меняются.

Порядок до любого использования v2:

1. HANDOFF этого этапа с точным commit SHA и SHA-256 каждого файла.
2. Независимый QA (исполнитель не проверяет свою работу).
3. Отдельный личный **G2** владельца по точному HEAD PR. Merge делает только владелец, вручную.
4. **Merge не активирует v2.** Активация — отдельное решение владельца в отдельной задаче, после реализации и независимой проверки валидатора (этап D1–D2, §8). До этого G0 #6831274083 прямо запрещает активацию: `v2_activation: forbidden`.

## 3. Состав

| Файл | Содержание | AC |
|---|---|---|
| [PROFILES.md](PROFILES.md) | профили `CODE_CHANGE/1` и `READ_ONLY_EVIDENCE_QA/1`, роли, `allowed_actions`, SPEC/2, Base/target/source, проверки NO_BRANCH_READ_ONLY, снимок refs | AC-1, AC-3 |
| [LIFECYCLE.md](LIFECYCLE.md) | сериализация сообщений, CLAIM/2, ASSIGN/2, fencing, lease, восстановление, личный G0 для каждого RESUME/2, схема RESUME/2, HANDOFF/2 | AC-2, AC-7 |
| [EVIDENCE.md](EVIDENCE.md) | `EvidenceRef/2`, `body_sha256` и граница провенанса, конверт `ISSUE_TEXT_LF/1`, проверки изменения, итоги VERIFIED/NOT_VERIFIED/STALE, нормализация времени GitHub | AC-4, AC-7 |
| [QA-REPORT.md](QA-REPORT.md) | независимые измерения, инварианты, словарь reason_code, таблица исходов, независимость проверяющего, порядок вычисления итога | AC-5 |
| [F4-WIRE.md](F4-WIRE.md) | проводная форма `AGENT-MSG/2 INDEXED` для `HANDOFF/2` и `QA-REPORT/2`: обёртка, байты, ключи, списки, типы, инварианты, привязка, таксономия ошибок `F4-*`, синтетические векторы, контракт будущего валидатора | F4 (Issue #32) |
| [RESUME2-FIXTURE.md](RESUME2-FIXTURE.md) | закреплённый канонический пример RESUME/2: 757 байт, SHA-256 `55709c80…aaaa6` | AC-6, AC-7 |
| [TEST-CASES.md](TEST-CASES.md) | положительные и отрицательные случаи как документация | AC-6 |
| [`fixtures/`](fixtures/) | точные байты векторов, 24 отрицательные фикстуры RESUME/2, [`SHA256SUMS`](fixtures/SHA256SUMS) | AC-6 |
| [`.gitattributes`](.gitattributes) | `fixtures/** -text`: Git не меняет переводы строк в фикстурах | AC-6 |

## 4. Источники (закреплены)

Принятая составная архитектура ([OWNER-DECISION #6830102574](https://github.com/iprus2026-tech/taxi-dashboard/issues/18#issuecomment-6830102574), `APPROVE_DESIGN_WITH_CONDITIONS`):

| Источник | Комментарий | `created_at` = `updated_at` | Байт | SHA-256 декодированного тела |
|---|---|---|---|---|
| DESIGN_NOTE/2 | [#6822137218](https://github.com/iprus2026-tech/taxi-dashboard/issues/18#issuecomment-6822137218) | `2026-11-12T11:18:17Z` | 20358 | `b810f9248c84f2d55722eeda36903258bf5d053d2944ae7d3cfff84156ba945c` |
| DESIGN_NOTE/3 | [#6824047634](https://github.com/iprus2026-tech/taxi-dashboard/issues/18#issuecomment-6824047634) | `2026-11-12T12:48:50Z` | 18888 | `1b20a65615654a980d9fbecf4127ef0b73e06290b26178221f07e02bc357f06c` |
| DESIGN_ERRATUM/1 | [#6826279439](https://github.com/iprus2026-tech/taxi-dashboard/issues/18#issuecomment-6826279439) | `2026-11-12T14:25:09Z` | 13574 | `eb9860cb0f289c4c99773130df6eaaffe39e7e47afd61fc9733045f2673ae78a` |
| OWNER-DECISION (дизайн) | [#6830102574](https://github.com/iprus2026-tech/taxi-dashboard/issues/18#issuecomment-6830102574) | `2026-11-12T16:54:38Z` | 1658 | `f9d72c79dd9311d997c70c17ad3ee00c64b72fd64f5fb633a0a8b243a09cd0b8` |

Хэши — `DECODED_BODY_UTF8/1` ([EVIDENCE.md §3](EVIDENCE.md)) строки `body`, полученной автором через GitHub MCP-сервер (прокси к REST API) при подготовке этого этапа. Это `provenance: AGENT_REPORTED` для проверяющего: перед использованием их нужно получить заново самостоятельно. Аттестацией байтов хранилища GitHub они не являются.

Дополнительно использованы (по ID, хэши тел здесь не закрепляются):

- [REVIEW_MEMO/4 #6829357927](https://github.com/iprus2026-tech/taxi-dashboard/issues/24#issuecomment-6829357927) — консультативный, только R4/R8/AC-6;
- [PRE_G0_CONDITIONS_NOTE/1 #6831064801](https://github.com/iprus2026-tech/taxi-dashboard/issues/26#issuecomment-6831064801) — условия C1–C3, утверждены G0 #6831274083;
- [COORDINATOR G0 RECEIPT #6831335844](https://github.com/iprus2026-tech/taxi-dashboard/issues/26#issuecomment-6831335844).

Три обязательных условия владельца и где они закрыты:

| Условие | Где закрыто |
|---|---|
| 1. Личное утверждение владельцем срока lease RESUME/2 (≤ 24 ч, без наследования и одностороннего продления) | политика `PT12H` по G0 #6831274083; привязка `resume2_lease_duration: PT12H` в личном G0 **каждого** RESUME/2 — [LIFECYCLE.md §5, §6.2](LIFECYCLE.md) |
| 2. Каноническая нормализация `updated_at` в UTC `.000Z`, отказ при неоднозначности, отличие декодированного JSON от сырых байтов | [EVIDENCE.md §3, §6](EVIDENCE.md) |
| 3. Полный канонический пример RESUME/2: один LF, SHA-256, длина, положительные и отрицательные случаи | [RESUME2-FIXTURE.md](RESUME2-FIXTURE.md), [TEST-CASES.md](TEST-CASES.md), [`fixtures/`](fixtures/) |

## 5. Решения, принятые при нормализации, и известные ограничения

Проектные тексты не определяли эти пункты однозначно. Здесь выбран самый строгий вариант, совместимый с G0. Пункты вынесены отдельно для QA и владельца:

1. **`task_role: IMPLEMENTER`** — единственная роль `CODE_CHANGE/1`. В дизайне роли определены только для read-only профиля, а поле `task_role` обязательно для всех SPEC/2 ([PROFILES.md §1.2](PROFILES.md)).
2. **Схемы CLAIM/2 и ASSIGN/2.** Проектные тексты закрепили только схему RESUME/2. Схемы CLAIM/2, ASSIGN/2 и служебных сообщений построены по тем же правилам `AGENT-MSG/2 FLAT` ([LIFECYCLE.md §1–§3](LIFECYCLE.md)).
3. **Lease ASSIGN/2 не продлевается**, в том числе CHECKPOINT/2. Это строже v1 §5.3 и следует требованию «без одностороннего продления» ([LIFECYCLE.md §5](LIFECYCLE.md)). **Решено владельцем** (замечание F3): [OWNER-DECISION #6836003274](https://github.com/iprus2026-tech/taxi-dashboard/issues/26#issuecomment-6836003274) утверждает для будущего v2 `assign2_lease_policy: NON_RENEWABLE` и `checkpoint2_lease_extension: FORBIDDEN`. После истечения lease ASSIGN/2 нужно новое отдельное разрешение (`expired_assign2_requires_new_authorization: true`). Политика RESUME/2 `PT12H` сохраняется (п.4). Действующий v1, включая продление lease через CHECKPOINT до истечения (v1 §5.3), **не меняется** (`active_v1_policy: UNCHANGED`). Решение не активирует v2. Запись — [LIFECYCLE.md §5.1](LIFECYCLE.md).
4. **Lease RESUME/2 — ровно PT12H**, а не «до PT12H». Другая длительность требует нового решения владельца по новой ревизии контракта.
5. **RESUME/2 для `CODE_CHANGE/1` не определён.** Восстановление code-задачи идёт через новый личный G0 и новый ASSIGN/2 с сохранением процедуры v1 §8.2 по HEAD ([LIFECYCLE.md §6.1](LIFECYCLE.md)).
6. **Сериализация HANDOFF/2 и QA-REPORT/2.** Поля и инварианты зафиксированы. Точная проводная форма со списками определена ревизией F4 в [F4-WIRE.md](F4-WIRE.md) (§10). Машинно эти сообщения по-прежнему не проверяются: валидатор — отдельная будущая задача.
7. **Диапазон лет 1970–9999** для времени GitHub ([EVIDENCE.md §6.1](EVIDENCE.md)).
8. **`evidence_outcome`** — итог одного доказательства. Он явно отображён на `verification_status` и `report_validity`. Набор значений и отображение задаёт только [EVIDENCE.md §2](EVIDENCE.md); после ревизии §9 значений четыре.
9. **Имя `DECODED_BODY_UTF8/1`** для `body_sha256`. В DESIGN_NOTE/2 этот хэш назывался «raw API body hash». Термин изменён, чтобы хэш не выдавался за аттестацию сырых байтов (условие 2).
10. **Строка `agent-msg` внутри fence.** Повтор info-string fence первой строкой тела сохранён, как в утверждённой схеме эррата. Он входит в 757 байт и в SHA-256.
11. **Ограничения, которые не устранены:** идентичность и независимость не криптографические; байты хранилища GitHub не аттестуются; валидатора нет, поэтому ожидаемые исходы в [TEST-CASES.md](TEST-CASES.md) выведены из текста, а не из прогона.

## 6. Трассировка критериев приёмки

| AC | Где выполнено |
|---|---|
| AC-1 | [PROFILES.md §1, §1.1](PROFILES.md) — раздельные профили, инвариант неприсваивания привилегий; NEG-AC1-01..03 |
| AC-2 | [LIFECYCLE.md §2–§6](LIFECYCLE.md) — CLAIM/2, ASSIGN/2 с привязкой к сессии, fencing `assign_ref`, lease, HANDOFF/2, личный G0 для каждого RESUME/2, без автоматического возобновления |
| AC-3 | [PROFILES.md §4, §5](PROFILES.md) — S1–S6 до и после, снимок refs, обязательная ветка `CODE_CHANGE/1`; NEG-AC3-01..04 |
| AC-4 | [EVIDENCE.md §1–§5](EVIDENCE.md) — `EvidenceRef/2`, конверт, ID комментария, repeat-fetch, итоги VERIFIED/NOT_VERIFIED/STALE |
| AC-5 | [QA-REPORT.md §1–§6](QA-REPORT.md) — четыре независимых поля, инварианты I1–I9, закрытая таблица исходов |
| AC-6 | [RESUME2-FIXTURE.md](RESUME2-FIXTURE.md), [TEST-CASES.md §1–§3](TEST-CASES.md), [`fixtures/SHA256SUMS`](fixtures/SHA256SUMS) — все девять обязательных категорий (NEG-01..21) |
| AC-7 | [LIFECYCLE.md §5, §6.2](LIFECYCLE.md) (PT12H, личный G0, без продления); [EVIDENCE.md §3, §6](EVIDENCE.md) (`.000Z`, без заявления об аттестации сырых байтов) |
| AC-8 | этот README §1–§2, §7; изменения только в `docs/agents/v2/**`; HANDOFF с точным SHA; QA и G2 впереди; v2 не активирован |

## 7. Совместимость с v1 и историческими состояниями

- `docs/agents/PROTOCOL.md` v1 не изменён (SHA-256 в Base SHA: `7e2b9114fe40545f5a1ef3373000b6cc37d520d349757f66298ad7d1cf0aad0b`). SPEC/1 по-прежнему проверяется только правилами v1 §4.2.
- Исторические сообщения и отчёты, не соответствующие v2, помечаются `HISTORICAL_NON_NORMATIVE`. Они не конвертируются, не переписываются и не «исправляются» задним числом.
- Статусы Issues не меняются этим этапом. В частности, #16 остаётся `handoff`, #17 и #18 — `blocked`; исторические FAIL, VOID и PASS владельца не переопределяются.
- Синтетические векторы (`TAXI-PROTOCOL-EXAMPLE-01`) не являются разрешениями.

## 8. Миграция D0–D3 (кратко)

| Этап | Содержание | Состояние |
|---|---|---|
| D0 | дизайн и его принятие владельцем | выполнено: OWNER-DECISION #6830102574 (только дизайн) |
| D1 | документация (этот каталог); затем отдельная задача `CODE_CHANGE/1` на валидатор и исполняемые тесты по [TEST-CASES.md](TEST-CASES.md) | документация — этот этап; валидатор — будущая отдельная задача |
| D2 | независимая проверка реализации на всех положительных и отрицательных фикстурах; личный G2; ручной merge | впереди |
| D3 | активация v2 отдельным решением владельца. Старые материалы (например, #16) оцениваются по v2 только через **новую** SPEC/2, G0, CLAIM/2 и ASSIGN/2, никогда через RESUME задачи v1 | впереди |

## 9. Ревизия `TAXI-AGENT-PROTOCOL-V2-REWORK-01` (Issue #28)

- SPEC/1: [#6836105748](https://github.com/iprus2026-tech/taxi-dashboard/issues/28#issuecomment-6836105748), `issue_spec_sha256` `3c387c4df132162389edf6fc7ddd773b522e7b25b37326c1efd07f780f056a72`; личный OWNER G0 [#6836138282](https://github.com/iprus2026-tech/taxi-dashboard/issues/28#issuecomment-6836138282) (`target_branch: main`, `decision_scope: DOCUMENTATION_REWORK_ONLY`, `v2_activation: forbidden`).
- Base SHA `48b0454d3b68f90e7687bd00b2ccc5a9318f6d70`; исходный HEAD `47872072a4be6f5dc4aa6ffdb296ff7f58ef1ae7` (ветка Issue #26 не менялась); ветка ревизии `agent/claude-code/taxi-agent-protocol-v2-rework-01`.
- Основание: [QA-REPORT/1 #6835645843](https://github.com/iprus2026-tech/taxi-dashboard/issues/26#issuecomment-6835645843) (verdict `VOID`, не PASS). Исторический HANDOFF #26 и этот отчёт не меняются и не переносятся на новый HEAD как PASS.

| Замечание | Где | Что сделано |
|---|---|---|
| F1 | [EVIDENCE.md](EVIDENCE.md) §2, §2.1–§2.4, §4.1; [QA-REPORT.md](QA-REPORT.md) §2, §3, §4, §4.1–§4.2, §6–§8 | некорректный конверт (`REJECTED` / `CANONICALIZATION_ERROR`) отделён от недоступности (`NOT_VERIFIED`); некорректная ссылка не делает отчёт `INVALID` |
| F2 | те же два файла: EVIDENCE.md §5, §6.3; QA-REPORT.md §4, §6–§7 | некорректный `updated_at` доказательства (`EVIDENCE_TS_UNVERIFIABLE`) и ссылки (`EVIDENCE_REF_INVALID`) отделены от схемы отчёта и времени сообщения протокола; общая таблица решений D01–D16 |
| F3 | этот README §5 п.3; [LIFECYCLE.md](LIFECYCLE.md) §5, §5.1, §8 | только запись политики владельца #6836003274; v1 не меняется; v2 не активируется |
| F4 | — | без изменений: проводная форма HANDOFF/2 и QA-REPORT/2 по-прежнему отложена (§5 п.6); до неё v2 не может быть активирован |

Остальные 35 файлов каталога, в том числе все 30 фикстур (`fixtures/SHA256SUMS`), побайтно совпадают с исходным HEAD. Статус по-прежнему `DRAFT / NOT ACTIVE`. Нужны отдельный независимый QA по точному HEAD ревизии и отдельная незаинтересованная проверка происхождения #22/#24/sem-03. Валидатора v2 нет; примеры и отрицательные случаи ревизии — документация, а не прогон.

## 10. Ревизия F4 `TAXI-AGENT-PROTOCOL-V2-F4-WIRE-01` (Issue #32)

- SPEC/1: [#6849953313](https://github.com/iprus2026-tech/taxi-dashboard/issues/32#issuecomment-6849953313), `issue_spec_sha256` `37d209c2ec8c0ed594e1966ae0efb96e7708c3e0c4aa41e96027a8f87a559a06` (5036 байт). Личный OWNER G0 [#6850660930](https://github.com/iprus2026-tech/taxi-dashboard/issues/32#issuecomment-6850660930): `target_branch: main`, `decision_scope: F4_WIRE_DOCS_ONLY`, `existing_fixtures_modification: forbidden`, `validator_implementation: not_authorized`, `pr_creation: not_authorized`, `v2_activation: forbidden`.
- CLAIM [#6851856755](https://github.com/iprus2026-tech/taxi-dashboard/issues/32#issuecomment-6851856755) новой сессии `session_01UHQjybzrunmUVCwurrxXj2`. ASSIGN v1 [#6851942229](https://github.com/iprus2026-tech/taxi-dashboard/issues/32#issuecomment-6851942229): lease 12 ч до `2026-11-13T23:47:41Z`, одна ветка `agent/claude-code/taxi-agent-protocol-v2-f4-wire-01` от Base `cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059`. Сессии, назначения и ветки #26 и #28 не наследуются. `ASSIGN/2` не используется: действует v1.
- Раскрытие: прежние сессии того же агента готовили v2 (#26, #28). Независимый QA этой ревизии ДОЛЖЕН выполнить другой агент в отдельной фактической сессии.

| Файл | Что сделано |
|---|---|
| [F4-WIRE.md](F4-WIRE.md) | новый: проводная форма `AGENT-MSG/2 INDEXED`, уровни M/W/B/L/K/S/H/Q/X, таксономия `F4-ERR/1`, 4 положительных вектора с длиной и SHA-256, 24 байтовых и 14 прочих отрицательных векторов, контракт будущего валидатора, решения нормализации (§17), трассировка AC-1..AC-10 (§18) |
| [LIFECYCLE.md](LIFECYCLE.md) | примечание о ревизии; последний абзац §1 и примечание после таблицы §7 ссылаются на F4-WIRE.md |
| [QA-REPORT.md](QA-REPORT.md) | примечание о ревизии; абзац о проводной форме в §2; абзац о D16 и кодах `F4-*` после таблицы §4.2; проверки C-11–C-17 в §8 |
| [TEST-CASES.md](TEST-CASES.md) | примечание о ревизии; §5 (векторы F4), §6 (матрица приёмки будущего валидатора) |
| этот README | шапка, строка таблицы §3, §5 п.6, этот раздел |

Не менялись: `docs/agents/PROTOCOL.md` v1, EVIDENCE.md, PROFILES.md, RESUME2-FIXTURE.md, `.gitattributes`, все 30 файлов `fixtures/` и `SHA256SUMS` (RESUME/2 757 байт, SPEC/2 499 байт, `sem-03`), байты таблицы D01–D16 в обеих копиях (7038 байт, `e91f4d30…ba03`), I1–I10, словарь `reason_code`, политика владельца F3 (§5 п.3–4).

Строка F4 в таблице §9 — историческая запись ревизии #28 и не переписывается. Теперь F4 закрыт на уровне документации. Статус каталога по-прежнему `DRAFT / NOT ACTIVE`. Дальше нужны: независимый QA по точному HEAD этой ревизии; отдельное решение владельца о PR и G2; затем отдельная задача `CODE_CHANGE/1` на валидатор ([F4-WIRE.md §16](F4-WIRE.md)), зависящая от `status:done` этой задачи; и только после проверки валидатора — отдельное решение об активации (этап D3, §8). Векторы F4 — документация, а не прогон и не фикстуры.
