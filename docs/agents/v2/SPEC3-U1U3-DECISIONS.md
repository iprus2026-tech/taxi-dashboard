# SPEC3-U1U3-DECISIONS — варианты решений владельца по унаследованным пробелам грамматики U-1, U-2, U-3

> **Статус: `OWNER-OPTIONS / NOT APPROVED / NOT NORMATIVE`.** Это записка с вариантами для владельца, а не нормативный документ и не решение. Она ничего не вводит в действие и не меняет ни одного правила. Действует `docs/agents/PROTOCOL.md` v1. Протокол v2 — `DRAFT / NOT ACTIVE`. `SPEC3-DESIGN.md` — `PROPOSAL / NOT NORMATIVE`, и его последняя версия провалила независимый QA40. По каждому вопросу U-1, U-2, U-3 здесь действует **`PENDING / NO DEFAULT`**. Выбор делает только владелец, лично, отдельным решением G1-design после независимого QA этой записки. Все «ожидаемые исходы» ниже выведены из текста при условии будущего выбора владельца. Это не результаты исполняемого парсера и не доказанные нормативные исходы.

> **Ревизия #45 (узкая переработка по QA44).** Эта версия — исходная записка Issue #42 (HEAD `dcf9854687c7174ac55d4d8d94713cdd078533f0`, 95102 байт, SHA-256 `86df1eba9a7d9b3afaab768ce3183e4c90ac70498e35a991e5af42da47ae4959`) с исправлением ровно трёх находок независимого QA44: **P2-QA44-01** (G2 смешивал две разные грамматики Git, §4.5, §4.7), **P2-QA44-02** (обещание отказа bidi/ESC при U2-B не охватывало исходный текст Issue до свёртки `x/..`, §4.3, §4.4, §4.8) и **P3-QA44-03** (исторический подсчёт: 10 файлов, а не 9, §2.3). Всё остальное перенесено без изменения смысла. Изменённые места помечены `[QA44]`. Карта изменений и трассировка — §11. Выбор по-прежнему не сделан: U-1…U-3, включая выбор грамматики G2 и политики исходного текста, — `PENDING / NO DEFAULT`.

---

## 0. Задача, полномочия и границы

| Элемент | Значение |
|---|---|
| Задача | `TAXI-AGENT-PROTOCOL-V2-SPEC3-U1U3-QA44-REWORK-01`, [Issue #45](https://github.com/iprus2026-tech/taxi-dashboard/issues/45) `[QA44]` |
| SPEC/1 (v1 §4.2) | [#6881640225](https://github.com/iprus2026-tech/taxi-dashboard/issues/45#issuecomment-6881640225): 4850 байт UTF-8 NFC, `issue_spec_sha256` `989a1f60919acc33c33551d3ab03520ba046f2f545b63bfafe155631a520c4e6` |
| Личный G0 | [#6881749613](https://github.com/iprus2026-tech/taxi-dashboard/issues/45#issuecomment-6881749613): `decision: APPROVE`, `target_branch: main`, `decision_scope: SPEC3_U1U3_QA44_NARROW_REWORK_DOC_ONLY`, `findings: P2-QA44-01,P2-QA44-02,P3-QA44-03`, `owner_choices_U1_U3: PENDING`, `g1_design_decision: NOT_APPROVED`, `g2_merge: NOT_APPROVED`, `max_lease_hours: 12` |
| CLAIM / ASSIGN | [CLAIM/1 #6881830732](https://github.com/iprus2026-tech/taxi-dashboard/issues/45#issuecomment-6881830732); [ASSIGN/1 #6881975950](https://github.com/iprus2026-tech/taxi-dashboard/issues/45#issuecomment-6881975950), lease `2026-11-14T18:08:47Z` … `2026-11-15T06:08:47Z` |
| Автор ревизии | `claude-code`, сессия `session_01UHQjybuJHfkZZe4pGnyDDM`. Роль — **автор узкой переработки**. Автор не принимает политику, не заменяет владельца и не проверяет собственную записку |
| Base SHA | `cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059` (= `main` на момент ASSIGN и первой записи) |
| Ветка | `agent/claude-code/taxi-agent-protocol-v2-spec3-u1u3-qa44-rework-01`, создана от Base после ASSIGN (не от HEAD #42) |
| Единственный файл | `docs/agents/v2/SPEC3-U1U3-DECISIONS.md` (этот документ, новый относительно Base). Других изменений в репозитории нет |
| Исходная версия (только чтение) | Задача `TAXI-AGENT-PROTOCOL-V2-SPEC3-U1U3-DESIGN-01`, [Issue #42](https://github.com/iprus2026-tech/taxi-dashboard/issues/42) (`status:blocked`), ветка `agent/claude-code/taxi-agent-protocol-v2-spec3-u1u3-design-01` @ `dcf9854687c7174ac55d4d8d94713cdd078533f0`, файл 95102 байт / `86df1eba9a7d9b3afaab768ce3183e4c90ac70498e35a991e5af42da47ae4959`, [HANDOFF #6878816330](https://github.com/iprus2026-tech/taxi-dashboard/issues/42#issuecomment-6878816330). SPEC/1 #42 `937a5814…a695`, G0 [#6877783092](https://github.com/iprus2026-tech/taxi-dashboard/issues/42#issuecomment-6877783092), автор `session_01UHQjycDp2LxUTQLgN2cDvn`. Ветка #42 не менялась |
| Основание переработки | [QA-REPORT/1 #6881291540](https://github.com/iprus2026-tech/taxi-dashboard/issues/42#issuecomment-6881291540) (задача #44, `verdict: FAIL`, тело 58388 байт / `af5be147beff6ea65182badaf43278781def8d262e2065ea8c041b1c68d8af6b`) и [квитанция #6881313298](https://github.com/iprus2026-tech/taxi-dashboard/issues/44#issuecomment-6881313298) |

**Раскрытие независимости.** Роль `claude-code` в других сессиях написала черновики v2, включая `PROFILES.md` (#26, #28), и обе отклонённые версии `SPEC3-DESIGN.md` (#36 `141c9ff…`, #39 `0821d1d…`). Две из трёх неопределённостей происходят из `PROFILES.md` (U-1, U-3). Исходную записку #42 тоже написала роль `claude-code` (`session_01UHQjycDp2LxUTQLgN2cDvn`). Сессия этой ревизии другая, но роль и модель те же. Поэтому автор этой записки **не независим** ни от разбираемых источников, ни от исходной версии. Независимую проверку делает отдельная задача (§10). Раскрытие сессий — в CLAIM #6881830732 (ревизия) и #6877932024 (исходная версия). Реальные личности за общим логином GitHub — `NOT_VERIFIED` (v1 §0.1).

**Чего здесь нет.** Здесь нет решения по U-1…U-3. Ни одно существующее правило не правится: v1 `PROTOCOL.md`, `PROFILES.md`, `SPEC3-DESIGN.md`, `F4-WIRE.md`, `EVIDENCE.md`, фикстуры и прочие файлы не меняются. Новых `reason_code`, итогов, кодов выхода и меток `S3-C*` нет. Нет валидатора, CI, PR, G2, merge, deploy и активации v2. OD-1…OD-7 и Q8/B-07 остаются `PENDING` (§8).

### 0.1 Классы источников (не смешивать)

| Метка | Что это | Сила |
|---|---|---|
| `[V1-ACTIVE]` | `docs/agents/PROTOCOL.md` @ Base | **действующий** нормативный протокол |
| `[V2-DRAFT]` | `docs/agents/v2/PROFILES.md` @ Base | черновик, `DRAFT / NOT ACTIVE` |
| `[S3-FAILED]` | `docs/agents/v2/SPEC3-DESIGN.md` @ `0821d1d…` (#39) | неутверждённое предложение; независимый QA40 — **FAIL** |
| `[QA40]` | [QA-REPORT/1 #6876984448](https://github.com/iprus2026-tech/taxi-dashboard/issues/39#issuecomment-6876984448) и [квитанция #6877007035](https://github.com/iprus2026-tech/taxi-dashboard/issues/40#issuecomment-6877007035) | независимый вывод проверяющего, не норма |
| `[OWNER-POLICY]` | [#6862874513](https://github.com/iprus2026-tech/taxi-dashboard/issues/32#issuecomment-6862874513) (F4 §17, п.1–4), [#6873515533](https://github.com/iprus2026-tech/taxi-dashboard/issues/34#issuecomment-6873515533) (Option A) | личные решения владельца по политике; ограничивают допустимые варианты |
| `[F4-BLOCKED]` | `docs/agents/v2/F4-WIRE.md` @ `e97df81…` (#34, `status:blocked`) | заблокированный черновик; только прецедент формулировок |
| `[GIT-OBS]` | наблюдение поведения Git 2.43.0 в сессии исходной версии #42 | факт об инструменте, а не норма проекта |
| `[GIT-DOC]` `[QA44]` | закреплённый текст документации Git 2.43.0: `glossary-content.txt` (31702 байт, SHA-256 `c9109ba0e3e7345cf8930c2d5e6feeae995ed553c27415d8337ebd2c91deb70b`) и `gitignore.txt` (8918 байт, `55e921fbc99d55d757739df4f0e143a00dcc93ea92c57ab27eeb1075f3c89577`) из пакета Ubuntu `git-doc` `1:2.43.0-1ubuntu7.4` (`.deb` SHA-256 `666e43894fa7aeb23485b522449d50c0f327465be7fd169c3b5c5991ad3f8888`) | факт о **документации** инструмента; поведение реализации не проверялось (`NOT_RUN`) |
| `[QA44]` | [QA-REPORT/1 #6881291540](https://github.com/iprus2026-tech/taxi-dashboard/issues/42#issuecomment-6881291540) и [квитанция #6881313298](https://github.com/iprus2026-tech/taxi-dashboard/issues/44#issuecomment-6881313298) | независимый вывод проверяющего, не норма; основание этой ревизии |
| `[HIST-OBS]` | обзор 352 комментариев Issues и PR репозитория с `created_at` ≤ 2026-11-14T14:13:59Z (REST API, публичный; правило отсечки — §2.3 п.4) | факт о прошлом использовании на дату отсечки, не постоянный инвариант |

Сокращения ссылок:

- V1 = `https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/PROTOCOL.md`
- PR = `https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/v2/PROFILES.md`
- S3 = `https://github.com/iprus2026-tech/taxi-dashboard/blob/0821d1d2094875cae73dbf01aa861a696262a6ac/docs/agents/v2/SPEC3-DESIGN.md`
- F4 = `https://github.com/iprus2026-tech/taxi-dashboard/blob/e97df81117d948f60b15d215916dacffda5c50cd/docs/agents/v2/F4-WIRE.md`

---

## 1. AC-1 — предусловия, проверенные до первой записи

`[QA44]` Ревизия #45. Проверено из live GitHub (публичный REST API) и `git ls-remote` повторно после ASSIGN, перед созданием ветки (2026-11-14T18:13Z–18:17Z):

1. **Сессия.** Runtime `get_session` = `session_01UHQjybuJHfkZZe4pGnyDDM` = `claim_session` ASSIGN #6881975950. Этот ID не встречался ни в одном комментарии репозитория и ни в одном трейлере коммитов до CLAIM.
2. **SPEC.** Каноническая SPEC/1 заново построена по v1 §4.2 из текущего тела Issue #45 и меток `gate:*` (только `G0-intake`): 4850 байт, UTF-8 NFC, LF, один завершающий LF, AC-1…AC-10, 1 разрешённый и 19 запрещённых путей, SHA-256 `989a1f60…c4e6`. Байты равны блоку `issue-spec` SPEC/1 #6881640225 и `approved_spec_sha256` в G0 #6881749613. Канонизатор сверен с проверочным вектором v1 §4.2 (495 байт, `f9b02543…56cd`). Смена метки статуса (`status:ready` → `status:in-progress`) в каноническую форму не входит; хэш тот же.
3. **G0 и ASSIGN.** G0 #6881749613 (литерал `target_branch: main`, scope `SPEC3_U1U3_QA44_NARROW_REWORK_DOC_ONLY`, роль, ветка, файл, исходный HEAD/хэш, ссылки на QA44) и ASSIGN #6881975950 не редактировались (created_at = updated_at). В #45 ровно один CLAIM и один ASSIGN. Lease действует до 2026-11-15T06:08:47Z.
4. **Refs.** `main` = Base, и Base — предок `origin/main`. Ветка #42 = `dcf9854687c7174ac55d4d8d94713cdd078533f0`; её файл (через `git cat-file` и raw.githubusercontent.com) = 95102 байт / `86df1eba…4959`; Base..HEAD #42 = один `A` этого файла. Ветки задачи #45 до создания не было. Замороженные #39 `0821d1d…`, #36 `141c9ff…`, #41 `efe79ea…` не изменились.
5. **QA44.** #44 закрыт (`status:done`). Единственный QA-REPORT в #42 — #6881291540, не редактирован, `verdict: FAIL`, находки ровно P2-QA44-01, P2-QA44-02, P3-QA44-03; тело 58388 байт / `af5be147…af6b` = квитанция #6881313298.
6. **Исключительность.** Открытых задач с тем же путём в `in-progress`/`qa` нет; у #41 (`status:handoff`) путь `SPEC3-DESIGN.md`. Расхождение `ts` CLAIM (на 23 с раньше `created_at`) координатор записал как `SELF_TS_SKEW_NOT_ATTESTED`; блок не правился.
7. **Фикстуры.** `docs/agents/v2/fixtures/SHA256SUMS` (30 строк) = `e475e0af5e35f37fa15ec5529ef1cf78ceb15d3b636ac07b0863feba3bee8fd5`, проверка хэшей проходит.

### 1.1 Предусловия исходной версии #42 (перенесено без изменений)

Проверено из live GitHub и `git ls-remote` повторно после ASSIGN, перед созданием ветки (2026-11-14T14:13Z):

1. **Сессия.** Runtime `get_session` = `session_01UHQjycDp2LxUTQLgN2cDvn` = `claim_session` ASSIGN.
2. **SPEC.** Каноническая SPEC/1 заново построена по v1 §4.2 из текущего тела Issue #42 (updated_at 2026-11-14T14:03:22Z) и меток `gate:*`. Результат: 4037 байт, UTF-8 NFC, LF, один завершающий LF, 10 AC, SHA-256 `937a5814…a695`. Байты равны блоку `issue-spec` в SPEC/1 #6877650937 и равны `approved_spec_sha256` в G0. Канонизатор сверен с проверочным вектором v1 §4.2 (495 байт, `f9b02543…56cd`).
3. **G0 и ASSIGN.** G0 #6877783092 (литерал `target_branch: main`, scope, роль, ветка, файл) и ASSIGN #6878416032 не редактировались (created_at = updated_at). Lease действует.
4. **Refs.** `main` = Base, и Base — предок `origin/main`. Замороженные ветки не менялись: #39 `…spec3-diagnostic-rework-01` = `0821d1d2094875cae73dbf01aa861a696262a6ac`, #36 `…spec3-design-01` = `141c9ff2217a4c1933bb4109a6695b2e24efd954`. Ветки этой задачи до создания не было. Ветка #41 `…spec3-l6-rework-01` = `efe79eae…`: она добавляет только `docs/agents/v2/SPEC3-DESIGN.md` и не касается этого файла.
5. **Исключительность.** У #41 свой путь (`SPEC3-DESIGN.md`), а наш файл в её SPEC запрещён. У #41 другая сессия (`session_01UHQjybrCGUynCqEFycYFNt`). Других CLAIM/ASSIGN по #42 нет.
6. **Расхождение времени.** `ts` в CLAIM на 8 секунд позже GitHub `created_at`. Координатор записал это как `CLOCK_SKEW / NOT_ATTESTED`. Блок не правился.
7. **Фикстуры.** `docs/agents/v2/fixtures/SHA256SUMS` (30 строк) = `e475e0af5e35f37fa15ec5529ef1cf78ceb15d3b636ac07b0863feba3bee8fd5`, проверка хэшей проходит.

---

## 2. AC-2 — матрица доказательств

### 2.1 Что сказано и чего не сказано

| U | Пункт источника | Что задаёт | Чего **не** задаёт | Контрпример | Класс |
|---|---|---|---|---|---|
| U-1 | V1 [§4.3 п.2 L206](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/PROTOCOL.md#L206): `target_branch: <полное имя ветки>` в `note` G0 | наличие строки в G0; изменение — новый G0 (п.3) | лексику значения; «полное» = короткое имя (`main`) или полный ref (`refs/heads/main`) | `target_branch: main feature` | `[V1-ACTIVE]` |
| U-1 | V1 [§4.3 п.5 L209](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/PROTOCOL.md#L209): `git merge-base --is-ancestor <base_sha> origin/<target_branch>` | проверку предка через **подстановку** значения в выражение Git | что подстановка даёт имя ветки, а не выражение ревизии | `main~1` → `origin/main~1` (§2.3, `[GIT-OBS]`) | `[V1-ACTIVE]` |
| U-1 | PR [§2.2 L73](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/v2/PROFILES.md#L73): `target_branch — полное имя ветки` | поле SPEC/2 под хэшем | ту же лексику, что и v1 | как выше | `[V2-DRAFT]` |
| U-1 | PR [§2.5 L102](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/v2/PROFILES.md#L102): совпадение с G0 байт в байт, иначе `UNAPPROVED_BASE` | равенство SPEC ↔ G0 | допустимость самой строки: два одинаково недопустимых значения совпадут | SPEC и G0 оба `main feature` | `[V2-DRAFT]` |
| U-1 | PR [§5 S3 L135](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/v2/PROFILES.md#L135): `git ls-remote origin refs/heads/<target_branch>` | чтение tip | что шаблон `ls-remote` не совпадёт с другими refs (сопоставление по хвосту и glob, §2.3) | `*`, `refs/heads/main` | `[V2-DRAFT]` |
| U-1 | PR [§2.4 L95](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/v2/PROFILES.md#L95): `<branch>` для `source_ref` — сегменты `[A-Za-z0-9][A-Za-z0-9_-]*`, ≤ 128 байт ASCII | грамматику **другого** поля (`source_ref`) | что она относится к `target_branch` | — (прецедент для U1-B) | `[V2-DRAFT]` |
| U-1 | S3 [§3.6.4 L262](https://github.com/iprus2026-tech/taxi-dashboard/blob/0821d1d2094875cae73dbf01aa861a696262a6ac/docs/agents/v2/SPEC3-DESIGN.md#L262), [§3.8 L362](https://github.com/iprus2026-tech/taxi-dashboard/blob/0821d1d2094875cae73dbf01aa861a696262a6ac/docs/agents/v2/SPEC3-DESIGN.md#L362): «проверяется только непустота → BLOCKED U-1» | честный отказ от выдумывания грамматики | грамматику | `S3-BLK-01` (`refs/heads/main`) | `[S3-FAILED]` |
| U-1 | QA40, строка U-1 таблицы блокеров | подтверждение пробела; вход `target_branch: main feature` | выбор политики (QA40 прямо отказался её придумывать) | `CE-QA40-U1` | `[QA40]` |
| U-2 | V1 [§4.2 L150](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/PROTOCOL.md#L150): «пути от корня репозитория или glob, разделитель `/`, без `./` и ведущего `/`, без повторов, сортировка побайтно» | корень; разделитель; запрет ведущего `/`; запрет `./` (в каком-то смысле); дедупликацию и порядок | пустые сегменты (`//`), сегменты `.`/`..`, завершающий `/`, допустимые символы, управляющие байты, синтаксис и семантику glob | `docs//app.py`, `docs/../app.py` | `[V1-ACTIVE]` |
| U-2 | V1 [§4.2 L151](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/PROTOCOL.md#L151): `forbidden_paths` — «те же правила; список не может быть пустым» | то же для запретов | то же | то же | `[V1-ACTIVE]` |
| U-2 | V1 [§6.2 L355](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/PROTOCOL.md#L355): «каждый путь входит в Allowed paths и не входит в Forbidden paths» | приоритет запрета при пересечении (запрет выигрывает) | как сопоставлять путь Git с шаблоном (байты? NFC? регистр? glob?) | `docs/../.github/x` в allowed | `[V1-ACTIVE]` |
| U-2 | PR [L79–L80](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/v2/PROFILES.md#L79), [§2.1 L62](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/v2/PROFILES.md#L62): те же правила, NFC для текста спецификации | перенос v1 в SPEC/2 | ничего сверх v1 | то же | `[V2-DRAFT]` |
| U-2 | S3 [L268–L269](https://github.com/iprus2026-tech/taxi-dashboard/blob/0821d1d2094875cae73dbf01aa861a696262a6ac/docs/agents/v2/SPEC3-DESIGN.md#L268), [§3.8 L363](https://github.com/iprus2026-tech/taxi-dashboard/blob/0821d1d2094875cae73dbf01aa861a696262a6ac/docs/agents/v2/SPEC3-DESIGN.md#L363): проверяются только «не с `/`», «не с `./`» → BLOCKED U-2 | честный отказ | два прочтения «без `./`» (префикс или любое вхождение) | `S3-BLK-02` | `[S3-FAILED]` |
| U-2 | `[OWNER-POLICY]` #6862874513 п.4: «ASCII-only paths: отклонить. Сохранять поддержку UTF-8/NFC и безопасную канонизацию путей» | **ограничение вариантов**: ASCII-only недопустим; нужна безопасная канонизация | конкретную грамматику | — | `[OWNER-POLICY]` |
| U-2 | F4 [L179](https://github.com/iprus2026-tech/taxi-dashboard/blob/e97df81117d948f60b15d215916dacffda5c50cd/docs/agents/v2/F4-WIRE.md#L179): `path` = `SEG *("/" SEG)`, без `//`, `.`, `..`, завершающего `/`, `\`, ≤ 255 байт, NFC, запрещённые категории Unicode | прецедент **строгой** формулировки для поля `path` проводной формы | правило для `allowed_paths`/`forbidden_paths` SPEC и glob | `NEG-F4-29` (`docs/../example.txt`) | `[F4-BLOCKED]` |
| U-3 | PR [§1 L22](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/v2/PROFILES.md#L22): `READ_ONLY_EVIDENCE_QA/1` — «G0; G2/G3 неприменимы (нечего мержить)» | что G2/G3 не имеют смысла для профиля | следствие для SPEC, где они перечислены: отвергнуть или игнорировать | `G0-intake` + `G3-deploy` | `[V2-DRAFT]` |
| U-3 | PR [§2.2 L82](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/v2/PROFILES.md#L82), [L87](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/v2/PROFILES.md#L87): `gates` — подмножество в порядке; допустимые сочетания профиля перечислены без `gates` | синтаксис `gates`; правило сочетаний | связь `gates` с `work_profile` | то же | `[V2-DRAFT]` |
| U-3 | S3 [L270](https://github.com/iprus2026-tech/taxi-dashboard/blob/0821d1d2094875cae73dbf01aa861a696262a6ac/docs/agents/v2/SPEC3-DESIGN.md#L270), [X1–X4 L276–L279](https://github.com/iprus2026-tech/taxi-dashboard/blob/0821d1d2094875cae73dbf01aa861a696262a6ac/docs/agents/v2/SPEC3-DESIGN.md#L276), [§3.8 L364](https://github.com/iprus2026-tech/taxi-dashboard/blob/0821d1d2094875cae73dbf01aa861a696262a6ac/docs/agents/v2/SPEC3-DESIGN.md#L364): «не отвергается; правило не придумывается» → BLOCKED U-3 | честный отказ | правило | `S3-BLK-03` (`G2-merge`) | `[S3-FAILED]` |
| U-3 | V1 [§5.6](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/PROTOCOL.md#L292), [§4.1](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/PROTOCOL.md#L121): G2/G3 требуют `approved_sha` (40 hex); `owner-gate` — переход после QA PASS «если нужен гейт» | машину состояний v1 | профили (в v1 их нет) | — | `[V1-ACTIVE]` |

### 2.2 Внутренние конфликты источников (обнаружены, не разрешаются)

| ID | Конфликт | Доказательство | Значение для вариантов |
|---|---|---|---|
| K-1 | Имена веток с точкой. v1 §4 ([L115](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/PROTOCOL.md#L115)) задаёт ветку `agent/<agent>/<id-lowercase>`, а `task_id` допускает `.<step>` ([L147](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/PROTOCOL.md#L147)). Реальный ref `refs/heads/agent/claude-code/taxi-ui-style-01.2` существует (`d1fdcc04…`, `git ls-remote`). Грамматика `<branch>` из PROFILES §2.4 точку **не допускает**. Черновик F4 ([L177](https://github.com/iprus2026-tech/taxi-dashboard/blob/e97df81117d948f60b15d215916dacffda5c50cd/docs/agents/v2/F4-WIRE.md#L177)) её допускает | `[V1-ACTIVE]`, `[V2-DRAFT]`, `[F4-BLOCKED]`, `[HIST-OBS]` | U1-B отвергает такие имена, U1-C — нет. Конфликт `source_ref` ↔ v1 §4 сам по себе выходит за U-1 и здесь не решается (§8.3) |
| K-2 | «Полное имя ветки» читается двояко. Пример v1 §4.3 п.1 (`checkpoint/taxi-dashboard-current-20261108`) и подстановки `origin/<target_branch>`, `refs/heads/<target_branch>` подразумевают **короткое** имя. Буквальное «полное» имя `refs/heads/main` дало бы `refs/heads/refs/heads/main` | `[V1-ACTIVE]`, `[V2-DRAFT]` | все варианты U-1 ниже исключают префикс `refs/` (общее правило R-EXCL) |
| K-3 | «Без `./`» читается двояко: только **префикс** или **любое вхождение** подстроки `./` (тогда запрещены и `../`, `docs/./x`) | `[V1-ACTIVE]`; отмечено QA40 | вариант U2-C разбит на C1 и C2 |
| K-4 | Неприменимые гейты: PROFILES L22 против L82/L87 | `[V2-DRAFT]` | U-3 |

### 2.3 Наблюдения инструментов и истории (`[GIT-OBS]`, `[HIST-OBS]`)

Это факты о поведении Git 2.43.0 и о прошлых данных репозитория. Нормой проекта они не являются и правила не задают.

1. `git check-ref-format --branch <имя>` (Git 2.43.0, запуск вне репозитория):
   - **принимает:** `main`, `checkpoint/taxi-dashboard-current-20261108`, `pilot/taxi-ui-style-01`, `agent/claude-code/taxi-ui-style-01.2`, `Main`, `фича/main`, `m\u0430in` (кириллическая «а», гомоглиф), `refs/heads/main`, `@`, 128- и 129-байтовые ASCII-имена;
   - **отвергает:** `main feature`, `main~1`, `release/../main`, `-main`, `main.lock`, `HEAD`, `main@{1}`, `a/`, `a//b`, `main` + ESC (0x1B), `a.`, `.a`, `a:b`, `a*`, `a?b`, `a[b`, `a\b`, `a^`, `a/.b`.

   Следствие: «Git-совместимо» без дополнительных исключений пропускает `refs/heads/main` и `@`.
2. `git rev-parse --verify origin/main~1^{commit}` вернул `48b0454d…` — **другой commit**, не tip `main`. Значение `target_branch: main~1` в подстановке v1 §4.3 п.5 превращает проверку предка в проверку против произвольной ревизии.
3. `git ls-remote origin taxi-ui-uat-02` вернул `refs/heads/agent/deepseek-qa/taxi-ui-uat-02`: шаблон сопоставляется **по хвосту**. `git ls-remote origin 'refs/heads/pilot/*'` раскрыл glob. Без лексики значения подстановка в шаблон `ls-remote` может совпасть с чужим ref или с несколькими refs.
4. `[HIST-OBS]`: во всех 352 комментариях Issues встречаются только значения `target_branch:` `main` (35) и `pilot/taxi-ui-style-01` (11). В 39 блоках `issue-spec` встречены только пути и шаблоны: `**/*`, `.github/**`, `app.py`, `bootstrap_storage.py`, `docs/agents/PROTOCOL.md`, `docs/agents/v2/**`, десять файлов `docs/agents/v2/*.md` (перечень ниже), `docs/agents/v2/fixtures/**`, `scripts/**`, `static/**`, `static/mapbox-token*.json`, `static/script.js`, `static/style.css`, `storage.py`, `templates/**`, `templates/index.html`, `tests/**`, `tools/**` и `none`. В гейтах — `G0-intake` (39), `G1-design` (2), `G2-merge` (7). Ни один исторический SPEC/1 не содержит пробела, `//`, `.`/`..`-сегмента, завершающего `/`, `\`, управляющих символов, `?`, `[`, `{` или не-ASCII в путях.

   `[QA44]` **Исправление P3-QA44-03.** Исходная версия #42 писала «девять файлов». Правильно — **десять**. Прямые (без дальнейшего `/`) файлы `docs/agents/v2/*.md`, встреченные в `allowed_paths`/`forbidden_paths` этих 39 блоков, побайтно отсортированы:
   1. `docs/agents/v2/EVIDENCE.md`
   2. `docs/agents/v2/F4-WIRE.md`
   3. `docs/agents/v2/LIFECYCLE.md`
   4. `docs/agents/v2/PROFILES.md`
   5. `docs/agents/v2/QA-REPORT.md`
   6. `docs/agents/v2/README.md`
   7. `docs/agents/v2/RESUME2-FIXTURE.md`
   8. `docs/agents/v2/SPEC3-DESIGN.md`
   9. `docs/agents/v2/SPEC3-U1U3-DECISIONS.md`
   10. `docs/agents/v2/TEST-CASES.md`

   **Как получено (воспроизводимо).** Выборка — все комментарии `GET /repos/iprus2026-tech/taxi-dashboard/issues/comments` (включая комментарии PR Conversation) с `created_at` ≤ `2026-11-14T14:13:59Z`. Это ровно 352 комментария; последний — #6878526326 (`2026-11-14T14:10:13Z`); ни один не правился после отсечки (`updated_at` ≤ отсечки). Манифест выборки: по строке на комментарий `<номер Issue> SP <id> SP <created_at> SP <SHA-256 тела UTF-8> LF`, порядок `created_at`, затем `id`. SHA-256 манифеста = `b4ce720083fcc85700d6e6cd21bfda0158b312e050f8fbca0c7de640c66508a5`; он совпадает с манифестом `[QA44]`. Блоки `issue-spec` — fenced-блоки ```` ```issue-spec ````. Счёт `target_branch` — строки вида `[пробелы][- ]target_branch: <значение>` с одним значением. Все прочие числа этого пункта (35, 11, 39, 39/2/7) при повторном подсчёте совпали.

   **Это исторический снимок на дату отсечки, а не инвариант репозитория.** Более поздние SPEC (например, #44 и #45) не входят в выборку и могут добавлять пути. Никакого более широкого утверждения об истории здесь нет.

---

## 3. AC-3 — U-1: лексическая грамматика `target_branch`

### 3.1 Общая часть всех вариантов

- Значение `V` — это **короткое** имя ветки, без префикса `refs/heads/` (K-2).
- **R-EXCL** (общие исключения, входят в каждый вариант): `V` ≠ `HEAD`; `V` ≠ `@`; первый сегмент `V` ≠ `refs`; `V` не начинается с `-`.
- Байтовые правила SPEC (UTF-8, NFC, без CR/TAB, без крайних пробелов) уже проверяются фазой P1 `[S3-FAILED §3.6.1]` и здесь не повторяются.
- При отказе по любому варианту ожидаемая первая метка в терминах `[S3-FAILED]` — `S3-C03 @ P8.target_branch`. Это существующая метка и существующая точка. Внешнее отображение — `SCHEMA_INVALID` до G0 и `UNAPPROVED_BASE` на контрольных точках (S3 §3.6.6), то есть существующие коды. Новых кодов нет. Всё это — **условно** на будущий выбор владельца.
- Проверка равенства SPEC ↔ G0 (`UNAPPROVED_BASE`, PR §2.5) остаётся процедурной и не меняется. Грамматика сработает раньше, при разборе SPEC.

### 3.2 Варианты

| Вариант | Определение (условно) | Плюсы | Минусы |
|---|---|---|---|
| **U1-A** — Git-совместимое короткое имя | `refs/heads/V` удовлетворяет правилам имени ref Git, записанным в протоколе **явно** (а не ссылкой на версию Git): сегменты через `/`, нет пустых сегментов, нет ведущего и завершающего `/`; сегмент не начинается с `.` и не оканчивается на `.lock`; нет подстроки `..`; нет байтов 0x00–0x20 и 0x7F; нет `~ ^ : ? * [ \`; `V` не оканчивается на `.`; нет подстроки `@{`. Плюс R-EXCL. Плюс длина ≤ `N` байт UTF-8 (параметр владельца, например 255). Не-ASCII допускается | совпадает с тем, что реально может быть веткой; принимает `…01.2` (K-1) и все исторические значения; не сужает будущие имена | гомоглифы (`m\u0430in`) и визуальная подмена при личном утверждении G0; переносимость не-ASCII имён refs; правило длинное, его надо доказать эквивалентным выбранному тексту Git; сама версия Git меняется |
| **U1-B** — узкий ASCII-словарь PROFILES §2.4 | `V` соответствует `<branch>` из PR §2.4: непустые сегменты `[A-Za-z0-9][A-Za-z0-9_-]*` через `/`, ≤ 128 байт ASCII. Плюс R-EXCL (из них по грамматике возможны только `HEAD` и первый сегмент `refs`) | одна грамматика с `source_ref`; простое регулярное выражение; доказуемо подмножество U1-A; нет гомоглифов, управляющих символов и выражений ревизий | **отвергает** `agent/claude-code/taxi-ui-style-01.2` (K-1) и любые имена с точкой, например `release/1.2`; ограничивает будущее именование |
| **U1-C** — узкий ASCII с точкой и ограничениями Git | сегмент `[A-Za-z0-9][A-Za-z0-9._-]*`; сегмент не оканчивается на `.` и на `.lock`; нет `..`; ≤ 128 байт ASCII; R-EXCL | принимает имена со ступенью `.N` (K-1) и `release/1.2`; подмножество U1-A; нет гомоглифов; близко к прецеденту [F4 L177](https://github.com/iprus2026-tech/taxi-dashboard/blob/e97df81117d948f60b15d215916dacffda5c50cd/docs/agents/v2/F4-WIRE.md#L177) | расходится с текущей грамматикой `<branch>` в PR §2.4 (её пришлось бы менять отдельно, §7); чуть сложнее U1-B |
| U1-D — закрытый реестр (слой, а не самостоятельная грамматика) | дополнительно к A/B/C: `V` ∈ списка целевых веток, утверждённого владельцем (сейчас наблюдаются `main`, `pilot/taxi-ui-style-01`; v1 §4.3 упоминает `checkpoint/…`) | самая узкая поверхность; соответствует практике «обычно `main`» (v1 §4.3 п.1) | каждая новая целевая ветка требует отдельного решения владельца и изменения реестра; реестр — ещё один источник, который надо версионировать |
| *U1-0 — базовая линия (не выбор)* | текущее `[S3-FAILED]`: только непустота, BLOCKED U-1 | — | ровно тот пробел, который QA40 признал блокером |

### 3.3 Примеры (условные ожидания; векторы §6)

`acc` — принято этой фазой при условии выбора варианта; `REJ` — `S3-C03 @ P8.target_branch`; `BLK` — проходит P8 только потому, что правила нет (базовая линия).

| Вектор | `target_branch` | Git `--branch` | U1-0 | U1-A | U1-B | U1-C |
|---|---|---|---|---|---|---|
| U-POS-RO | `main` | принимает | acc | acc | acc | acc |
| UV1-01 | `checkpoint/taxi-dashboard-current-20261108` | принимает | BLK | acc | acc | acc |
| UV1-02 | `pilot/taxi-ui-style-01` | принимает | BLK | acc | acc | acc |
| UV1-03 | `agent/claude-code/taxi-ui-style-01.2` | принимает | BLK | acc | **REJ** | acc |
| UV1-04 ≡ CE-QA40-U1 | `main feature` | отвергает | BLK | REJ | REJ | REJ |
| UV1-05 ≡ S3-BLK-01 | `refs/heads/main` | **принимает** | BLK | REJ (R-EXCL) | REJ (R-EXCL) | REJ (R-EXCL) |
| UV1-06 | `main~1` | отвергает | BLK | REJ | REJ | REJ |
| UV1-07 | `release/../main` | отвергает | BLK | REJ | REJ | REJ |
| UV1-08 | `-main` | отвергает | BLK | REJ | REJ | REJ |
| UV1-09 | `main.lock` | отвергает | BLK | REJ | REJ | REJ |
| UV1-10 | `HEAD` | отвергает | BLK | REJ | REJ (R-EXCL) | REJ (R-EXCL) |
| UV1-11 | `фича/main` (NFC) | принимает | BLK | acc | REJ | REJ |
| UV1-12 | `main@{1}` | отвергает | BLK | REJ | REJ | REJ |
| UV1-13 | `Main` | принимает | BLK | acc | acc | acc |
| UV1-14 | `main` + ESC `[0m` (0x1B) | отвергает | BLK | REJ | REJ | REJ |
| UV1-15 | `release/` + 120×`x` (128 байт) | принимает | BLK | acc | acc | acc |
| UV1-16 | `release/` + 121×`x` (129 байт) | принимает | BLK | acc (при `N` ≥ 129) | REJ | REJ |
| UV1-17 | `main/` | отвергает | BLK | REJ | REJ | REJ |
| UV1-18 | `@` | **принимает** | BLK | REJ (R-EXCL) | REJ | REJ |
| UV1-19 | `m\u0430in` (гомоглиф) | принимает | BLK | **acc** | REJ | REJ |

### 3.4 Безопасность

| Риск | Пример | U1-0 | U1-A | U1-B / U1-C |
|---|---|---|---|---|
| Выражение ревизии вместо ветки: проверка предка против другого commit | `main~1`, `main@{1}`, `main^` (§2.3 п.2) | открыт | закрыт | закрыт |
| Шаблон `ls-remote` совпадает с чужим ref или несколькими refs | `*`, хвостовое совпадение (§2.3 п.3) | открыт | закрыт (`*` запрещён); хвостовое совпадение остаётся процедурной особенностью команды, а не лексики | то же |
| Инъекция опции в команду, где значение стоит без префикса | `-main` | открыт | закрыт (R-EXCL) | закрыт |
| Разбиение по словам или управляющие последовательности терминала в журналах проверяющего | `main feature`, ESC | открыт | закрыт | закрыт |
| Визуальная подмена при личном утверждении G0 (равенство байтов не защищает, если владелец утверждает то, что видит) | `m\u0430in` | открыт | **открыт** | закрыт |
| Коллизия регистра refs на нечувствительных к регистру ФС (loose refs) | `Main` и `main` | открыт | открыт | открыт; закрывается только параметром «только нижний регистр» (не предлагается по умолчанию: ломает обратную совместимость для гипотетических имён с прописными) |

### 3.5 Обратная совместимость

- `target_branch` **не входит** в SPEC/1 (v1 §4.2). Ни один вариант не меняет `issue_spec_sha256` существующих задач.
- Все исторические значения (`main`, `pilot/taxi-ui-style-01`) принимаются всеми вариантами A/B/C (§2.3 п.4).
- Реальный ref с точкой (K-1) был **рабочей** веткой задачи, а не целевой. Как целевую ветку его не использовали. U1-B отвергнет его только если кто-то сделает его целевым.
- Ни один вариант не навязывается существующим SPEC/1 или SPEC/2. Применение к SPEC/1 и к G0 действующего v1 — отдельный вопрос U1-Q2 (§3.6).

### 3.6 Вопросы владельцу (решение не принято)

- **U1-Q1.** Какая грамматика: U1-A, U1-B или U1-C? Добавлять ли слой U1-D (реестр)? Значение `N` для U1-A? `PENDING / NO DEFAULT`.
- **U1-Q2.** Где действует выбранное правило:
  - (а) только в будущих SPEC/2 и SPEC/3 (v2 DRAFT);
  - (б) также в строке `target_branch:` личного G0 по действующему v1 §4.3. Это **поправка действующего v1**: она требует собственной задачи, G0, независимого QA и G2 (§7.3).

  `PENDING / NO DEFAULT`.

---

## 4. AC-4 — U-2: грамматика путей и glob, нормализация

### 4.1 Два уровня, которые нельзя смешивать

1. **Формирование** (`Issue → канонические байты`). Координатор строит SPEC из текста Issue (v1 §4.2). Уже сейчас на этом уровне есть преобразования: сортировка, дедупликация и сжатие пробелов в AC.
2. **Разбор канонических байтов** (`P8` в `[S3-FAILED]`). Он проверяет уже канонические байты, которые утверждены хэшем.

Векторы §6 — это канонические байты, то есть уровень 2. Канонизация (вариант U2-B) действует только на уровне 1. Поэтому на уровне 2 варианты U2-A и U2-B ведут себя одинаково, а различаются только тем, какой текст Issue вообще может дать SPEC (§4.4).

`[QA44]` Отказ на уровне 2 **не переносится** на уровень 1 автоматически. Свёртка `x/..` удаляет сегмент `x` целиком вместе со всеми его символами. Значит, при U2-B без отдельной проверки исходного текста запрещённый символ в удаляемом сегменте не доходит до уровня 2 и не может быть там отвергнут (P2-QA44-02). Будет ли исходный текст Issue проверяться до свёртки — отдельный подвыбор U2-R (§4.4.1). Каждое утверждение об отказе ниже явно указывает уровень.

### 4.2 Общая часть

- Корень — корень репозитория. Разделитель — `/` (v1 [L150](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/PROTOCOL.md#L150), без изменений).
- Байтовые правила UTF-8/NFC проверяются P1 до любых правил пути. Путь не в NFC (UV2-17) отвергается как `S3-C02 @ P1` при **любом** варианте.
- `[OWNER-POLICY]` #6862874513 п.4: вариант «только ASCII» **недопустим** и не предлагается. Не-ASCII буквы допустимы во всех вариантах.
- Приоритет запрета над разрешением задан в v1 §6.2 ([L355](https://github.com/iprus2026-tech/taxi-dashboard/blob/cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059/docs/agents/PROTOCOL.md#L355)). Он не меняется и решения не требует.
- При отказе ожидаемая первая метка — `S3-C03 @ P8.allowed_paths` или `P8.forbidden_paths`: существующие метка и точки, существующие внешние коды (условно).

### 4.3 Варианты грамматики

| Вариант | Определение (условно) | Плюсы | Минусы |
|---|---|---|---|
| **U2-A** — строгая грамматика, fail-closed, без канонизации | `P = SEG *("/" SEG)`. SEG непуст. SEG ∉ {`.`, `..`}. Нет ведущего и завершающего `/`. Запрещены кодовые точки U+0000–U+001F, U+007F–U+009F, `\` (U+005C), категория `Cf` (в том числе U+200B–U+200F, U+202A–U+202E, U+2066–U+2069, U+FEFF) и не-ASCII `Zs` (U+00A0 и др.). Длина ≤ `M` байт UTF-8 (параметр, например 255 по прецеденту [F4 L179](https://github.com/iprus2026-tech/taxi-dashboard/blob/e97df81117d948f60b15d215916dacffda5c50cd/docs/agents/v2/F4-WIRE.md#L179)). Метасимволы glob — по подвыбору U2-G (§4.5). Текст Issue с нарушением → SPEC не формируется | ни одно значение не меняется молча; отвергнутое владелец видит; совпадает с прецедентом F4; исторические пути все проходят | автор Issue должен сам записать каноническую форму; опечатку `docs//x` надо исправлять руками |
| **U2-B** — канонизация при формировании + строгие канонические байты | **Уровень 1:** (0) `[QA44]` проверка исходного текста — по подвыбору U2-R (§4.4.1), решение не принято; (1) `//…` → `/`; (2) удалить сегменты `.`; (3) лексически свернуть `x/..`; `..`, выходящий выше корня, → SPEC не формируется; (4) убрать завершающий `/`; (5) пустой результат → SPEC не формируется; (6) затем существующие дедупликация и сортировка v1. Символьных преобразований, кроме общего NFC, нет. **Уровень 2:** канонические байты обязаны удовлетворять грамматике U2-A; любая неканоническая форма в байтах → отказ | удобство для автора Issue; соответствует словам владельца «безопасная канонизация» (п.4); защитный смысл `docs/../app.py` в запретах сохраняется (он становится `app.py`) | текст Issue и утверждённые байты расходятся сильнее, чем сейчас; `docs/../.github/x` в allowed молча превращается в путь под запретом (тогда выигрывает запрет, v1 §6.2, и разрешение пустеет); разные тексты Issue дают один хэш (пересечение с Q8/B-07, §8.2); нужна доказанная идемпотентность; `[QA44]` без проверки исходного текста (U2-R0/R2) запрещённые символы в удаляемых свёрткой `x/..` сегментах исчезают без следа (§4.4.1) |
| **U2-C** — буквальный минимум (формализация текущего текста) | только явно названные правила; всё остальное — непрозрачная строка с буквальным сопоставлением. **C1:** «без `./`» = только префикс `./`. **C2:** «без `./`» = любое вхождение подстроки `./` (запрещает `../` и `/./`, но не `//`, не завершающий `/` и не `docs/.`) | ни одного нового правила; v1 не меняется по смыслу | **ложная защита:** запрет `docs//app.py` или (в C1) `docs/../app.py` не совпадает ни с одним путём Git и ничего не защищает; управляющие символы и bidi проходят (подмена имени при ревью, ср. CVE-2021-42574); `\` трактуется по-разному в Windows и Linux; полнота грамматики (требование AC-4/AC-9 QA40) по-прежнему не достигнута |

### 4.4 Канонизация U2-B на уровне 1 (условные примеры из текста Issue)

| Текст в Issue | Результат U2-B (уровень 1) | U2-A (уровень 1) |
|---|---|---|
| `docs//app.py` | `docs/app.py` | SPEC не формируется |
| `docs/../app.py` (в запретах вместе с `app.py`) | `app.py`, дедупликация с существующим `app.py` | SPEC не формируется |
| `docs/./example.txt` | `docs/example.txt` | не формируется |
| `docs/example.txt/` | `docs/example.txt` | не формируется |
| `docs/../.github/workflows/ci.yml` (в allowed) | `.github/workflows/ci.yml`; пересекается с запретом `.github/**`, запрет выигрывает (v1 §6.2) | не формируется |
| `../app.py` | не формируется (выход выше корня) | не формируется |
| `docs/.` | `docs` | не формируется |
| `docs/**/` | `docs/**` | не формируется |
| `[QA44]` `docs/<U+202E>/../example.txt` (в allowed) | зависит от U2-R (§4.4.1): R0/R2 — `docs/example.txt`, U+202E исчезает; R1/R3 — не формируется | не формируется |
| `[QA44]` `docs/<ESC>[31m/../example.txt` (в allowed) | то же: R0/R2 — `docs/example.txt`, ESC исчезает; R1/R3 — не формируется | не формируется |

Обозначения `<U+202E>` и `<ESC>` (U+001B) здесь — описание кодовой точки в тексте записки, а не буквальный символ. Точные байты — в §6.4.

### 4.4.1 `[QA44]` Подвыбор U2-R — исходный текст Issue до свёртки против проверки только канонических байтов (нужен только при U2-B)

**Проблема (P2-QA44-02).** Исходная версия #42 задавала для U2-B порядок «свёртка `x/..` → строгая грамматика U2-A для итоговых байтов» ([#42 L208](https://github.com/iprus2026-tech/taxi-dashboard/blob/dcf9854687c7174ac55d4d8d94713cdd078533f0/docs/agents/v2/SPEC3-U1U3-DECISIONS.md#L208)). Одновременно таблица §4.8 без указания уровня утверждала, что bidi/ESC при U2-B отвергаются ([#42 L284](https://github.com/iprus2026-tech/taxi-dashboard/blob/dcf9854687c7174ac55d4d8d94713cdd078533f0/docs/agents/v2/SPEC3-U1U3-DECISIONS.md#L284)). Для исходного текста Issue `docs/<U+202E>/../example.txt` или `docs/<ESC>[31m/../example.txt` свёртка удаляет опасный сегмент целиком. Итог `docs/example.txt` удовлетворяет U2-A, и при отсутствии другой проверки SPEC совпадает побайтно с U-POS-CC (597 байт, `8ef90e8a…46b4`). Оба исходных текста — корректный UTF-8 в NFC без CR/TAB. U+202E — категория `Cf`, U+001B — `Cc`. P1 сам по себе их не запрещает. Это расхождение проектного контракта, а не заявленная уязвимость production.

**Варианты** (условно; ни один не выбран и не предпочтителен):

| Подвариант | Порядок на уровне 1 | Что гарантируется | Открытые риски |
|---|---|---|---|
| **R0** — как в исходной версии #42 (для сравнения) | свёртка → U2-A только для итога | отказ bidi/ESC/Cf/Cc — **только для символов, оставшихся в канонических байтах** | обещание без указания уровня неточно; запрещённые символы в удаляемых сегментах исчезают молча; утверждённый хэш не показывает исходный текст |
| **R1** — отказ до нормализации | (а) каждый элемент **исходного** текста Issue проверяется на запрещённые кодовые точки U2-A (U+0000–U+001F, U+007F–U+009F, `\`, `Cf`, не-ASCII `Zs`) по **всей** строке, включая сегменты, которые потом удалит свёртка; (б) только затем шаги (1)–(6) U2-B; (в) итог — U2-A | запрещённый символ не может исчезнуть при свёртке; обещание «отвергается» верно на обоих уровнях | нужна вторая проверка до канонизации (две точки, где действует один набор символов); диагностика уровня 1 — «SPEC не формируется», а не метка `S3-C*`; список запрещённых символов должен совпадать на обоих уровнях |
| **R2** — проверка только канонических байтов, точно ограниченная | как R0, но обещание явно сужено: «канонические байты не содержат запрещённых символов». Дополнительно при формировании координатор обязан **раскрыть** каждый элемент, который изменился при свёртке, рядом с SPEC (исходный → канонический) | проверяемо по хэшу на уровне 2; исходный текст доступен проверяющему процедурно | защита от подмены отображения в исходном тексте процедурная, а не синтаксическая; раскрытие не входит в хэш; расширяется класс «разный текст Issue — один хэш» (Q8/B-07, §8.2); проверяющий может не заметить удалённый сегмент |
| **R3** — без свёртки `x/..` | U2-B ограничен шагами (1), (2), (4)–(6) (`//`, `.`, завершающий `/`); любой сегмент `..` в исходном тексте → SPEC не формируется | символы не могут исчезнуть: удаляются только пустые сегменты и `.`, в которых нет других символов | теряется защитный смысл `docs/../app.py` в запретах (§4.4: SPEC не формируется, автор исправляет вручную); по поведению с `..` вариант приближается к U2-A |

**Условные исходы для исходного текста Issue** (точные байты и хэши — §6.4; уровень 1, затем уровень 2):

| Вход (текст Issue) | U2-A | U2-B + R0/R2 | U2-B + R1 | U2-B + R3 | U2-C1 | U2-C2 |
|---|---|---|---|---|---|---|
| allowed `docs/<U+202E>/../example.txt` (CE-QA44-CANCEL-BIDI) | не формируется | байты = U-POS-CC → acc | не формируется (U+202E) | не формируется (`..`) | acc (непрозрачная строка) | REJ (`./` в `../`) |
| allowed `docs/<ESC>[31m/../example.txt` (CE-QA44-CANCEL-ESC) | не формируется | = U-POS-CC → acc | не формируется (U+001B) | не формируется | acc | REJ |
| allowed `docs/<U+200B>/../example.txt` (U45-R-01) | не формируется | = U-POS-CC → acc | не формируется (U+200B `Cf`) | не формируется | acc | REJ |
| allowed `docs/<U+007F>/../example.txt` (U45-R-02) | не формируется | = U-POS-CC → acc | не формируется (U+007F `Cc`) | не формируется | acc | REJ |
| forbidden + `docs/<U+2066>x/../../app.py` (U45-R-03) | не формируется | `app.py`, дедупликация с существующим `app.py` → = U-POS-CC → acc | не формируется (U+2066 `Cf`) | не формируется | acc* | REJ |
| allowed `docs/<U+202E>/x/../example.txt` (U45-R-04, контроль) | не формируется | `docs/<U+202E>/example.txt` (601 байт) → REJ на уровне 2 (`S3-C03 @ P8.allowed_paths`, (б)) | не формируется | не формируется | acc | REJ |

U45-R-04 — контрольный случай: символ остаётся в итоге, поэтому даже R0 его отвергает (на уровне 2). Он показывает, что разница между R0/R2 и R1/R3 видна только тогда, когда опасный сегмент удаляется целиком. Пять входов из таблицы дают при R0/R2 одни и те же канонические байты U-POS-CC. Это намеренные дубликаты (§6.4), а не совпадение SHA-256 разных байтов.

**Первая диагностика.** Уровень 1 меток `S3-C*` не имеет: отказ там — «SPEC не формируется» (координатор, v1 §4.2). При прямом разборе несвёрнутых байтов на уровне 2 (векторы §6.4 без формирования) U2-A и U2-B дают `S3-C03 @ P8.allowed_paths` (или `P8.forbidden_paths` для U45-R-03), подпроверка (б), первый элемент. Метка не различает, что сработало первым внутри элемента — сегмент `..` или запрещённый символ. Это не опровергает обход на уровне 1, а лишь показывает, что уровень 2 сам по себе его не видит.

**Вопрос владельцу U2-Q6** (§4.9): R1, R2 или R3 (R0 — только точка сравнения)? `PENDING / NO DEFAULT`.

### 4.5 Подвыбор U2-G — семантика glob (нужен при U2-A и U2-B; при U2-C тоже не определена)

v1 употребляет glob, но не определяет его. Исторически встречаются только `X/**`, `**/*` и `static/mapbox-token*.json` (§2.3 п.4).

| Подвариант | Определение (условно) | Плюсы | Минусы |
|---|---|---|---|
| **G1** — закрытое подмножество | Только `*` и `**`. `*` — ноль и более кодовых точек, кроме `/`, внутри одного сегмента; совпадает и с ведущей `.` (файлы-точки). `**` — только целым сегментом, ноль и более целых сегментов; `**/*` совпадает с любым путём, `d/**` — с любым путём под `d/`. `? [ ] { } !` и `\` в шаблоне запрещены. Имена файлов с буквальными `*`, `?`, `[` выразить нельзя (fail-closed) | все исторические шаблоны сохраняют очевидный смысл; конечное и полностью описанное правило | нет экранирования; файлы со спецсимволами не могут быть разрешены явным путём |
| **G2-P** `[QA44]` — точная семантика Git pathspec с магией `:(glob)` | как задокументировано в `[GIT-DOC]` glossary, `glob` (L400–L427): шаблон для fnmatch(3) с `FNM_PATHNAME`, подстановки не совпадают с `/`; `?`, `[...]`, экранирование `\` по fnmatch; `**` особый только в трёх формах (`**/` в начале, `/**` в конце, `/**/` в середине); **«Other consecutive asterisks are considered invalid»** (L425). Шаблон сопоставляется с полным путём от корня | богаче G1; знакомо по командам Git; `**` не целым сегментом недопустим, т.е. ошибка видна сразу | импорт внешней спецификации, зависимой от версии; `\` конфликтует с запретом `\` в U2-A; «invalid» в документации не задаёт, как именно проявляется отказ в реализации (`NOT_RUN`) |
| **G2-I** `[QA44]` — семантика шаблонов `.gitignore` | как задокументировано в `[GIT-DOC]` gitignore, `PATTERN FORMAT` (L69–L132): `*` и `?` не совпадают с `/`, диапазоны `[...]`; те же три формы `**`; **«Other consecutive asterisks are considered regular asterisks»** (L131). Кроме того: шаблон **без `/` в начале или середине совпадает на любом уровне** (L94–L97); завершающий `/` — только каталоги (L99–L101); ведущий `!` — отрицание (L82–L89); ведущий `#` — комментарий (L75–L77); завершающие пробелы отбрасываются, если не экранированы `\` (L79–L80) | знакомо по `.gitignore`; `**` не целым сегментом допустим (как `*`) | те же минусы импорта; семантика задумана для **списка с порядком и отрицанием**, а не для двух независимых множеств allowed/forbidden; совпадение без `/` на любом уровне **меняет область** исторических шаблонов `app.py`, `storage.py`, `bootstrap_storage.py` (в запретах они защитили бы и `x/app.py`); `!` и `#` в начале требуют отдельного правила |

`[QA44]` **G2-P и G2-I не эквивалентны** (исправление P2-QA44-01). Исходная версия #42 определяла один вариант G2 как wildmatch Git «как в pathspec `:(glob)` / gitignore» и обещала для `docs/a**b.md` при G2 «acc, `**` как `*`» ([#42 L231](https://github.com/iprus2026-tech/taxi-dashboard/blob/dcf9854687c7174ac55d4d8d94713cdd078533f0/docs/agents/v2/SPEC3-U1U3-DECISIONS.md#L231), [L275](https://github.com/iprus2026-tech/taxi-dashboard/blob/dcf9854687c7174ac55d4d8d94713cdd078533f0/docs/agents/v2/SPEC3-U1U3-DECISIONS.md#L275)). Документация одной и той же версии Git 2.43.0 даёт для «прочих последовательностей звёздочек» противоположные правила: pathspec `glob` — «considered invalid» (glossary L425), gitignore — «considered regular asterisks» (gitignore L131). Это различие двух интерфейсов одной версии, а не риск будущей смены Git. По `[QA44]`, в Git 2.52.0 формулировка pathspec «invalid» сохранена ([glossary-content.adoc L432](https://github.com/git/git/blob/9a2fb147f2c61d0cab52c883e7e26f5b7948e3ed/Documentation/glossary-content.adoc#L432)); в этой сессии текст 2.52.0 не загружался, поэтому это `NOT_VERIFIED` автором ревизии. Поэтому общий вариант G2 **снят** и заменён двумя отдельными. Владелец выбирает G1, G2-P или G2-I (U2-Q2); ни один не предпочтителен.

Несовместимости G2-P и G2-I, существенные для `allowed_paths`/`forbidden_paths`:

| Аспект | G2-P (`:(glob)`) | G2-I (gitignore) | Вектор |
|---|---|---|---|
| `**` не целым сегментом (`docs/a**b.md`) | недопустим (L425) | как `*` → `docs/a*b.md` (L131) | UV2-21 |
| `***` целым сегментом (`docs/***/a.md`) | недопустим (L425) | как `*` → `docs/*/a.md` (L131) | CE-QA44-GLOB3 |
| одиночный `**` | ни одна из трёх особых форм → по буквальному чтению L425 недопустим | как `*`; шаблон без `/` → любое имя на любом уровне, т.е. все пути | UV2-19 |
| шаблон без `/` (`example.txt`, `app.py`) | только путь от корня | любой уровень: `docs/example.txt`, `x/app.py` (L94–L97) | U45-G2-01; запрет `app.py` в U-POS-CC |
| ведущий `!` (`!docs/example.txt`) | буквальный символ имени | отрицание предыдущего совпадения (L82–L89); для независимых списков смысл не определён | U45-G2-02 |
| ведущий `#` (`#example.txt`) | буквальный символ имени | комментарий: шаблон ничего не совпадает (L75–L77) | U45-G2-03 |
| экранирование `\` (`docs/\*.md`) | fnmatch: `\*` — буквальная `*` | то же, плюс `\#`, `\!`, `\ ` в начале/конце (L76, L80, L88) | U45-G2-04; при U2-A/U2-B `\` запрещён в любом случае |
| завершающий `/` | — | только каталоги (L99–L101) | UV2-05, UV2-14; при U2-A/U2-B завершающий `/` запрещён в любом случае |

При выборе любого G2 будущая интеграция должна: (1) назвать **ровно одну** грамматику; (2) переписать её правила в текст протокола, без ссылки на версию Git; (3) для G2-I отдельно решить привязку шаблона без `/` (любой уровень или от корня), смысл ведущих `!` и `#` (запретить или считать буквальными) и согласовать экранирование с запретом `\` в U2-A; (4) для G2-P записать, что «недопустимые» последовательности дают `S3-C03` на этапе P8. Поведение реализации Git (`wildmatch`) в этой ревизии **не наблюдалось** (`NOT_RUN`). Документация и реализация могут расходиться; ни одно ожидание ниже не опирается на запуск Git или валидатора.

Ещё два открытых параметра:

- совпадает ли `d/**` с самим `d`, если `d` — файл;
- совпадают ли `*` и `**` с файлами-точками.

В G1 выше предложено «нет» и «да». Это параметры, решение не принято.

### 4.6 Подвыбор U2-N — Unicode при сопоставлении с путями Git

Спецификация обязана быть в NFC (P1). В дереве Git путь может храниться в NFD (например, после macOS без `core.precomposeunicode`).

- **N1 — fail-closed.** Путь из `git diff`, байты которого не в NFC, не совпадает ни с одним явным путём и не считается разрешённым. Дополнительно HANDOFF/QA отвергает изменение такого файла. Отвергается и тогда, когда тот покрыт разрешающим glob: иначе явный запрет `docs/café.txt` (NFC) обходится файлом `docs/cafe` + U+0301 + `.txt` (NFD).
- **N2 — нормализовать перед сопоставлением.** Сравнивается `NFC(путь Git)` с шаблоном.

N1 проще и не скрывает различий. N2 удобнее, но два разных файла Git могут дать одно NFC-имя, и тогда нужна отдельная проверка коллизий. Регистр в обоих случаях сравнивается побайтно. Опциональное усиление — отвергать разрешённый путь, который при свёртке регистра совпадает с запрещённым (`Docs/x` при запрете `docs/**` пишет в тот же каталог на нечувствительной к регистру ФС). Это параметр, решение не принято.

### 4.7 Примеры на уровне 2 (условные ожидания; векторы §6)

Столбец «A / B» — общий для U2-A и U2-B на уровне канонических байтов (§4.1). `G1`/`G2-P`/`G2-I` указаны там, где результат зависит от подвыбора glob (`[QA44]`: прежний общий `G2` разделён, §4.5). `acc*` — принято, но шаблон не совпадает ни с одним путём Git: в запретах защита иллюзорна.

| Вектор | Изменение относительно U-POS-CC | A / B | C1 | C2 |
|---|---|---|---|---|
| UV2-01 | allowed `docs/пример.txt` (NFC) | acc | acc | acc |
| UV2-02 | forbidden + `docs//app.py` | REJ | acc* | acc* |
| UV2-03 | forbidden + `docs/../app.py` | REJ | acc* | REJ |
| UV2-04 | allowed `docs/./example.txt` | REJ | acc | REJ |
| UV2-05 | allowed `docs/example.txt/` | REJ | acc | acc |
| UV2-06 | allowed `docs/../.github/workflows/ci.yml` | REJ | acc | REJ |
| UV2-07 | allowed `docs\example.txt` | REJ | acc | acc |
| UV2-08 | allowed `docs/*.md` | acc (G1, G2-P, G2-I) | acc | acc |
| UV2-09 | allowed `docs/[a-z]*.md` | REJ (G1) / acc (G2-P, G2-I: диапазон по fnmatch) | acc | acc |
| UV2-10 | allowed `docs/**` | acc (G1, G2-P, G2-I: завершающий `/**`) | acc | acc |
| UV2-11 | allowed `../app.py` | REJ | acc | REJ |
| UV2-12 | allowed `docs/a` + ESC `[31m.txt` (0x1B) | REJ | acc | acc |
| UV2-13 | allowed `docs/txt.` + U+202E + `exe` (bidi) | REJ | acc | acc |
| UV2-14 | allowed `docs/**/` | REJ | acc | acc |
| UV2-15 | allowed `docs/{a,b}.md` | REJ (G1) / acc как буквальное имя (G2-P, G2-I: `{}` ни в одном из двух текстов не определены) | acc | acc |
| UV2-16 | allowed `docs/?.md` | REJ (G1) / acc (G2-P, G2-I) | acc | acc |
| UV2-17 | allowed `docs/cafe` + U+0301 + `.txt` (NFD) | `S3-C02 @ P1` | `S3-C02 @ P1` | `S3-C02 @ P1` |
| UV2-18 | allowed `docs/.` | REJ | acc | acc |
| UV2-19 | allowed `**` | acc (G1: целый сегмент; разрешено всё, кроме запретов: семантический риск, не синтаксический) / `[QA44]` REJ (G2-P: ни одна из трёх особых форм, буквальное чтение L425) / acc (G2-I: как `*` без `/`, т.е. любое имя на любом уровне — тот же семантический риск) | acc | acc |
| UV2-20 | allowed `Docs/Example.txt` | acc (риск регистра, §4.6) | acc | acc |
| UV2-21 | allowed `docs/a**b.md` | REJ (G1: `**` не целым сегментом) / `[QA44]` REJ (G2-P: «considered invalid», L425) / acc (G2-I: «regular asterisks», L131, т.е. как `docs/a*b.md`) | acc | acc |

`[QA44]` Исправлены строки UV2-08/09/10/15/16/19/21: вместо одного столбца `G2` теперь отдельные ожидания G2-P и G2-I. Байты векторов не менялись (§6.2). Строку UV2-19 QA44 не отмечал. Она изменена потому, что при разделении G2 её прежнее безусловное «acc» перестало быть верным для G2-P. Отказ при A/B — `S3-C03 @ P8.allowed_paths`, подпроверка (б), первый элемент.

**`[QA44]` Дополнительные векторы уровня 2** (байты — §6.4):

| Вектор | Изменение относительно U-POS-CC | A / B | C1 | C2 |
|---|---|---|---|---|
| CE-QA44-GLOB3 | allowed `docs/***/a.md` | REJ (G1: `***` не `**`) / REJ (G2-P, L425) / acc (G2-I: как `docs/*/a.md`) | acc | acc |
| U45-G2-01 | allowed `example.txt` | acc при всех G; **область** разная: G1 и G2-P — только корневой `example.txt`, G2-I — `example.txt` на любом уровне, в том числе `docs/example.txt` | acc | acc |
| U45-G2-02 | allowed `!docs/example.txt` | G1: REJ (`!` запрещён в шаблоне G1) / G2-P: acc, `!` — буквальный символ имени / G2-I: отрицание; смысл в независимом списке allowed не определён → **вопрос владельцу** (запретить ведущий `!` или считать его буквальным) | acc | acc |
| U45-G2-03 | allowed `#example.txt` | G1 и G2-P: acc, `#` — буквальный символ / G2-I: комментарий, шаблон ничего не совпадает → **вопрос владельцу** (запретить ведущий `#` или считать его буквальным) | acc | acc |
| U45-G2-04 | allowed `docs/\*.md` | REJ при всех G: `\` запрещён грамматикой U2-A (§4.3); экранирование G2-P/G2-I при U2-A/U2-B невыразимо | acc | acc |
| CE-QA44-CANCEL-BIDI | allowed `docs/<U+202E>/../example.txt` (несвёрнутые байты) | REJ (`..` и `Cf`) | acc | REJ |
| CE-QA44-CANCEL-ESC | allowed `docs/<ESC>[31m/../example.txt` | REJ | acc | REJ |
| U45-R-01 | allowed `docs/<U+200B>/../example.txt` | REJ | acc | REJ |
| U45-R-02 | allowed `docs/<U+007F>/../example.txt` | REJ | acc | REJ |
| U45-R-03 | forbidden + `docs/<U+2066>x/../../app.py` | REJ (`P8.forbidden_paths`) | acc* | REJ |
| U45-R-04 | allowed `docs/<U+202E>/x/../example.txt` | REJ | acc | REJ |

Векторы CANCEL/U45-R здесь — прямой разбор несвёрнутых байтов на уровне 2. Их исход на уровне 1 (формирование из текста Issue) зависит от U2-R и приведён в §4.4.1. Отказ на уровне 2 этот обход не закрывает. Ожидания выведены из текста документации и вариантов; парсер и Git не запускались.

### 4.8 Fail-closed против явной канонизации — сравнение

| Критерий | U2-A | U2-B | U2-C |
|---|---|---|---|
| Утверждённые байты = то, что написано в Issue | да (кроме существующих сортировки и дедупликации) | нет: возможны свёртки | да |
| Запрет `docs/../app.py` защищает `app.py` | SPEC не формируется, автор исправляет | да | C1 — нет (acc*), C2 — SPEC не формируется |
| Запрет `docs//app.py` | SPEC не формируется | становится `docs/app.py` | ложная защита |
| Подмена отображения (bidi, ESC) в канонических байтах (уровень 2) | отвергается | отвергается | проходит |
| `[QA44]` Подмена отображения в сегменте исходного текста, удаляемом свёрткой `x/..` (уровень 1, §4.4.1) | SPEC не формируется | зависит от U2-R: R1 и R3 — SPEC не формируется; R0/R2 — символ исчезает, байты как без него (R2 — с раскрытием исходного текста) | свёртки нет: C1 — строка принимается как есть, C2 — отвергается из-за `../` |
| Переносимость (`\`) | отвергается | отвергается | проходит |
| Разные тексты Issue → один хэш (Q8/B-07, §8.2) | только существующие случаи (порядок, повтор) | **добавляются** новые (`docs//a` ≡ `docs/a`) | только существующие |
| Совместимость с историческими SPEC/1 | все 39 блоков проходят | канонизация — тождество на всех исторических путях | все проходят |
| `[QA44]` Область совпадения исторических шаблонов без `/` (`app.py`, `storage.py`, `bootstrap_storage.py`) | только корень при G1 и G2-P; любой уровень при G2-I (§4.5) | то же | не определена (непрозрачная строка) |
| Полнота грамматики (требование QA40) | достижима | достижима | нет |

### 4.9 Вопросы владельцу (решение не принято)

- **U2-Q1.** U2-A, U2-B, U2-C1 или U2-C2? `PENDING / NO DEFAULT`.
- **U2-Q2.** Семантика glob: G1, G2-P (pathspec `:(glob)`) или G2-I (`.gitignore`), и параметры из §4.5 (для G2-I также привязка шаблона без `/`, ведущие `!` и `#`)? `[QA44]` Прежний общий вариант G2 снят: две грамматики Git не эквивалентны. `PENDING / NO DEFAULT`.
- **U2-Q3.** Unicode при сопоставлении: N1 или N2? Нужна ли проверка коллизий регистра? `PENDING / NO DEFAULT`.
- **U2-Q4.** Параметры: `M` (длина), допустим ли пробел 0x20 внутри сегмента (Git допускает, история не использует). `PENDING / NO DEFAULT`.
- **U2-Q5.** Где действует правило:
  - (а) только SPEC/2 и SPEC/3;
  - (б) также SPEC/1 по действующему v1 §4.2 L150–L151. Это **поправка действующего v1** (§7.3).

  Исторические хэши SPEC/1 не меняются при A и C. При B они не меняются, потому что на исторических путях канонизация — тождество. `PENDING / NO DEFAULT`.
- **U2-Q6.** `[QA44]` Только при U2-B: проверяется ли исходный текст Issue до свёртки (R1), только канонические байты с точно суженным обещанием и раскрытием исходного текста (R2), или свёртка `x/..` исключается (R3)? R0 — исходное поведение #42, приведено только для сравнения (§4.4.1). `PENDING / NO DEFAULT`.

---

## 5. AC-5 — U-3: гейты G2/G3 при `READ_ONLY_EVIDENCE_QA/1`

### 5.1 Два прочтения

- **Недопустимый вход.** SPEC, где `work_profile: READ_ONLY_EVIDENCE_QA/1`, а `gates` содержит `G2-merge` или `G3-deploy`, не формируется.
- **Корректная, но неприменимая запись.** SPEC формируется и утверждается, а гейты G2/G3 для неё ничего не значат. Что именно «ничего не значат» — это отдельный выбор между U3-B и U3-C.

U-3 существует только в v2: в SPEC/1 нет `work_profile`, и в действующем v1 вопрос не возникает.

### 5.2 Варианты

| Вариант | Определение (условно) | Ожидаемая первая метка | Следствия для G0/G2/G3 и машины состояний |
|---|---|---|---|
| **U3-A1** — отвергнуть; новое правило сочетания X5 после X1–X4 | X5: `work_profile = READ_ONLY_EVIDENCE_QA/1` ⇒ в `gates` нет `G2-merge` и `G3-deploy` | `S3-C03 @ P8.X5` (существующая метка; X5 — новая документарная точка, не код) | G0 на такую SPEC невозможен (SPEC нет). Машина состояний не меняется. G2/G3 для read-only никогда не запрашиваются |
| **U3-A2** — отвергнуть внутри проверки поля `gates` | после подпроверок (а)–(г) поля `gates` (S3 §3.6.4 п.1) — проверка профиля | `S3-C03 @ P8.gates` | как A1. Отличие только в первой диагностике при одновременных нарушениях X1–X4 (UVM-06). Проверка поля обращается к значению другого, более раннего поля — это необычно для P8 |
| **U3-B** — принять; неприменимые гейты игнорируются явным правилом | SPEC формируется. Для read-only записи `G2-merge`/`G3-deploy` не имеют эффекта: координатор не переводит задачу в `owner-gate` ради них. OWNER-DECISION G2/G3 по такой задаче недействителен, потому что у неё нет `approved_sha` HEAD | нет (принято) | хэшированная SPEC содержит мёртвые записи. Владелец может ошибочно полагать, что G2 что-то защищает. Нужна правка машины состояний: «owner-gate только для применимых гейтов» |
| **U3-C** — принять; неприменимые гейты блокируют | SPEC формируется. Переход `qa → owner-gate` требует перечисленных гейтов, а G2/G3 для read-only выдать нельзя (нет `approved_sha`), поэтому задача уходит в `BLOCKED` существующим сообщением. Исправление — только новая SPEC и G0 | нет при разборе; процедурный `BLOCKED` на контрольной точке | fail-late: ошибка обнаруживается после выполнения работы. Машина состояний v1 не меняется, но задача может стать невыполнимой |

### 5.3 Сравнение

| Критерий | U3-A1 | U3-A2 | U3-B | U3-C |
|---|---|---|---|---|
| Безопасность записи в репозиторий | без изменений: X2/X3 уже запрещают запись для `FORBIDDEN` | то же | то же | то же |
| Ясность утверждённого текста для владельца | высокая: недопустимое не утверждается | высокая | низкая: утверждаются мёртвые строки | средняя: строки «живые», но невыполнимые |
| Детерминизм диагностики | да | да (порядок отличается от A1) | да (диагностики нет) | процедурный, зависит от момента обнаружения |
| Новое правило в грамматике | X5 | ветка проверки поля | правило машины состояний | нет |
| Обнаружение | при формировании SPEC (до G0) | при формировании | никогда (по определению) | после QA PASS |
| Совместимость с историей | read-only задачи в истории (#40: только `G0-intake`) проходят | то же | то же | то же |

### 5.4 Примеры (условные; векторы §6)

| Вектор | Профиль, `gates` | A1 | A2 | B | C |
|---|---|---|---|---|---|
| U-POS-RO | RO, G0 | acc | acc | acc | acc |
| UV3-01 | RO, G0 G1 | acc | acc | acc | acc |
| UV3-02 ≡ S3-BLK-03 | RO, G0 G2 | `S3-C03 @ P8.X5` | `S3-C03 @ P8.gates` | acc (G2 игнорируется) | acc → `BLOCKED` у owner-gate |
| UV3-03 ≡ CE-QA40-U3 | RO, G0 G3 | `P8.X5` | `P8.gates` | acc | acc → `BLOCKED` |
| UV3-04 | RO, G0 G1 G2 G3 | `P8.X5` | `P8.gates` | acc | acc → `BLOCKED` |
| U-POS-CC | CC, G0 G2 | acc | acc | acc | acc |
| UV3-05 | CC, G0 G2 G3 | acc | acc | acc | acc |

### 5.5 Вопрос владельцу (решение не принято)

- **U3-Q1.** SPEC read-only с `G2-merge`/`G3-deploy` — это недопустимый вход (U3-A1 или U3-A2) или корректная запись, которая игнорируется (U3-B) или блокирует задачу (U3-C)? `PENDING / NO DEFAULT`.

### 5.6 Смежное наблюдение (вне U-3, не решается)

O-ADJ-1. PR L22 требует G0 для обоих профилей и G2 перед merge для `CODE_CHANGE/1`. При этом грамматика `gates` (PR L82; S3 [L270](https://github.com/iprus2026-tech/taxi-dashboard/blob/0821d1d2094875cae73dbf01aa861a696262a6ac/docs/agents/v2/SPEC3-DESIGN.md#L270)) допускает `- none` и отсутствие `G0-intake` или `G2-merge`. Это соседний пробел того же рода, что U-3, но в задачу #42 он не входит. Записка его не классифицирует и не предлагает правила. Владелец может включить его в будущую задачу отдельным решением.

---

## 6. AC-6 — воспроизводимые байтовые векторы

### 6.1 Построение

Векторы — синтетические канонические байты SPEC/3 из `[S3-FAILED]`. Они **не являются фикстурами**, не входят в `fixtures/` и не меняют `fixtures/SHA256SUMS`.

- **U-POS-RO** — это `S3-POS-01` из S3 §8.1 (791 байт, `4efca81d…91be`); сборщик проверяет его хэш.
- **U-POS-CC** — новый синтетический вход профиля `CODE_CHANGE/1`. Он нужен для `allowed_paths` и `G2-merge`, которых в read-only нет. Его допустимость по P1–P8 `[S3-FAILED]` выведена из текста, а не из прогона.

Сборщик воспроизводит семь ранее опубликованных векторов (CE-QA40-U1…U3 из QA40, S3-BLK-01…03 из S3 §8.5) и останавливается при несовпадении хэша.

Нужен Python ≥ 3.8 только со стандартной библиотекой. Порядок:

1. Сохранить блок между маркерами в файл вне рабочего каталога.
2. Запустить `python3 -I /путь/build-u1u3.py` в пустом каталоге. С любым аргументом скрипт ещё и запишет файлы `<имя>.txt`.

Извлечь блок из клона на коммите HANDOFF:

```bash
sed -n '/^<!-- U1U3-BUILD BEGIN -->$/,/^<!-- U1U3-BUILD END -->$/p' docs/agents/v2/SPEC3-U1U3-DECISIONS.md | sed '1,2d' | sed '$d' | sed '$d' > build-u1u3.py
```

<!-- U1U3-BUILD BEGIN -->
```python
import hashlib, sys, unicodedata
SHA = '48b0454d3b68f90e7687bd00b2ccc5a9318f6d70'
R = ['TAXI-ISSUE-SPEC/3', 'task_id: TAXI-PROTOCOL-EXAMPLE-31', 'depends_on:', '- none',
     'work_profile: READ_ONLY_EVIDENCE_QA/1', 'task_role: EVIDENCE_REVIEWER',
     'base_sha: ' + SHA, 'target_branch: main', 'source_ref: refs/heads/main',
     'source_sha: ' + SHA, 'branch_policy: FORBIDDEN', 'evidence_policy: ISSUE_TEXT_LF/1',
     'allowed_actions:', '- issue_comment:create', '- repo:read', 'allowed_paths:', '- none',
     'forbidden_paths:', '- **/*', 'acceptance.count: 3',
     'acceptance.1.id: AC-1', 'acceptance.1.required: true',
     'acceptance.1.text: Required example criterion one.',
     'acceptance.2.id: AC-2', 'acceptance.2.required: false',
     'acceptance.2.text: Optional example criterion two.',
     'acceptance.3.id: AC-3', 'acceptance.3.required: true',
     'acceptance.3.text: Required example criterion three.', 'gates:', '- G0-intake']
C = ['TAXI-ISSUE-SPEC/3', 'task_id: TAXI-PROTOCOL-EXAMPLE-41', 'depends_on:', '- none',
     'work_profile: CODE_CHANGE/1', 'task_role: IMPLEMENTER',
     'base_sha: ' + SHA, 'target_branch: main', 'source_ref: refs/heads/main',
     'source_sha: ' + SHA, 'branch_policy: REQUIRED', 'evidence_policy: none',
     'allowed_actions:', '- git_commit:create', '- git_ref:create', '- repo:read',
     'allowed_paths:', '- docs/example.txt', 'forbidden_paths:', '- .github/**', '- app.py',
     'acceptance.count: 1', 'acceptance.1.id: AC-1', 'acceptance.1.required: true',
     'acceptance.1.text: Example criterion.', 'gates:', '- G0-intake', '- G2-merge']

def sub(base, old, new):
    # replace exactly one line equal to `old` by the list `new`
    assert base.count(old) == 1, old
    i = base.index(old)
    return base[:i] + new + base[i + 1:]

def tb(v, base=R):  return sub(base, 'target_branch: main', ['target_branch: ' + v])
def ap(*v):         return sub(C, '- docs/example.txt', ['- ' + x for x in v])
def fp(*v):         return sub(C, '- app.py', ['- app.py'] + ['- ' + x for x in v])

V = [
 ('U-POS-RO', R), ('U-POS-CC', C),
 ('UV1-01', tb('checkpoint/taxi-dashboard-current-20261108')),
 ('UV1-02', tb('pilot/taxi-ui-style-01')),
 ('UV1-03', tb('agent/claude-code/taxi-ui-style-01.2')),
 ('UV1-04', tb('main feature')),
 ('UV1-05', tb('refs/heads/main')),
 ('UV1-06', tb('main~1')),
 ('UV1-07', tb('release/../main')),
 ('UV1-08', tb('-main')),
 ('UV1-09', tb('main.lock')),
 ('UV1-10', tb('HEAD')),
 ('UV1-11', tb('\u0444\u0438\u0447\u0430/main')),
 ('UV1-12', tb('main@{1}')),
 ('UV1-13', tb('Main')),
 ('UV1-14', tb('main\x1b[0m')),
 ('UV1-15', tb('release/' + 'x' * 120)),
 ('UV1-16', tb('release/' + 'x' * 121)),
 ('UV1-17', tb('main/')),
 ('UV1-18', tb('@')),
 ('UV1-19', tb('m\u0430in')),
 ('UV2-01', ap('docs/\u043f\u0440\u0438\u043c\u0435\u0440.txt')),
 ('UV2-02', fp('docs//app.py')),
 ('UV2-03', fp('docs/../app.py')),
 ('UV2-04', ap('docs/./example.txt')),
 ('UV2-05', ap('docs/example.txt/')),
 ('UV2-06', ap('docs/../.github/workflows/ci.yml')),
 ('UV2-07', ap('docs\\example.txt')),
 ('UV2-08', ap('docs/*.md')),
 ('UV2-09', ap('docs/[a-z]*.md')),
 ('UV2-10', ap('docs/**')),
 ('UV2-11', ap('../app.py')),
 ('UV2-12', ap('docs/a\x1b[31m.txt')),
 ('UV2-13', ap('docs/txt.\u202eexe')),
 ('UV2-14', ap('docs/**/')),
 ('UV2-15', ap('docs/{a,b}.md')),
 ('UV2-16', ap('docs/?.md')),
 ('UV2-17', ap('docs/cafe\u0301.txt')),
 ('UV2-18', ap('docs/.')),
 ('UV2-19', ap('**')),
 ('UV2-20', ap('Docs/Example.txt')),
 ('UV2-21', ap('docs/a**b.md')),
 ('UV3-01', R + ['- G1-design']),
 ('UV3-02', R + ['- G2-merge']),
 ('UV3-03', R + ['- G3-deploy']),
 ('UV3-04', R + ['- G1-design', '- G2-merge', '- G3-deploy']),
 ('UV3-05', C + ['- G3-deploy']),
 ('UVM-01', tb('main feature', sub(R, 'base_sha: ' + SHA, ['base_sha: ' + SHA.upper()]))),
 ('UVM-02', tb('main feature') + ['- G3-deploy']),
 ('UVM-03', sub(sub(R, 'target_branch: main', ['target_branch:main feature']), '- **/*', ['- docs//app.py'])),
 ('UVM-04', sub(ap('docs//a.txt'), '- app.py', ['- app.py', '- none'])),
 ('UVM-05', ap('docs//a.txt', 'docs/a.txt')),
 ('UVM-06', sub(R, '- issue_comment:create', ['- git_commit:create', '- issue_comment:create']) + ['- G3-deploy']),
 ('UVM-07', R[:-1] + ['- G3-deploy', '- G0-intake']),
 ('UVM-08', sub(tb('-main', C), '- docs/example.txt', ['- ../app.py'])),
 # reproductions of earlier published vectors (must equal QA40 / #39 values)
 ('CE-QA40-U1', tb('main feature')),
 ('CE-QA40-U2', sub(R, '- **/*', ['- docs//app.py'])),
 ('CE-QA40-U3', R + ['- G3-deploy']),
 ('S3-BLK-01', tb('refs/heads/main')),
 ('S3-BLK-02', sub(R, '- **/*', ['- docs/../app.py'])),
 ('S3-BLK-03', R + ['- G2-merge']),
]
EXPECT = {
 'U-POS-RO':   '4efca81d58935b67dcc20d06459271873ad2ec382415ac67f32124ad883791be',
 'CE-QA40-U1': 'b3cb5643faf984d9f993c6cb041cfc09ebddba104bb28d0074b76c98bda28dd0',
 'CE-QA40-U2': 'd19efca545a1ac171a7ddd8c87d592530ebc8e49f195dcfc727412220d92d8c7',
 'CE-QA40-U3': 'c7faa129d4fa7dd4bcdd9c159f28dd7b0f322a96f722a6a0b9c7fb4f52051866',
 'S3-BLK-01':  'f24bd1706e81faec4dfb7a266316a69cf81327219fc9d5c583df35aa0dec81e0',
 'S3-BLK-02':  '8644d8e201ed07aa049f61f01f430e0d1a61b1d4870ee9a7520ada9dff225d89',
 'S3-BLK-03':  '6b16530b5171ecefa81f24ee0336ed9b22d91f2fa290a09907e31f4dd3eadde3',
}
seen = {}
for name, lines in V:
    b = ('\n'.join(lines) + '\n').encode('utf-8')
    d = hashlib.sha256(b).hexdigest()
    if name in EXPECT:
        assert d == EXPECT[name], (name, d)
    assert d not in seen or name in EXPECT or seen[d] in EXPECT, (name, seen.get(d))
    seen.setdefault(d, name)
    if len(sys.argv) > 1:
        open(name + '.txt', 'wb').write(b)
    nfc = unicodedata.is_normalized('NFC', b.decode('utf-8'))
    print(name, len(b), d, *([] if nfc else ['NOT-NFC']))
```
<!-- U1U3-BUILD END -->

Сам скрипт записан только ASCII-символами: все не-ASCII кодовые точки заданы экранированием `\uXXXX`, управляющие — `\x1b`. Поэтому в тексте записки нет буквальных U+202E, U+0301 и ESC, а сама записка остаётся в NFC.

### 6.2 Таблица векторов

Ожидания — **условные** (§3.3, §4.7, §5.4). Ни одно не является результатом исполняемого парсера.

| ID | Байт | SHA-256 | Что проверяет |
|---|---:|---|---|
| U-POS-RO | 791 | `4efca81d58935b67dcc20d06459271873ad2ec382415ac67f32124ad883791be` | = `S3-POS-01`; принят при всех вариантах |
| U-POS-CC | 597 | `8ef90e8aaf5a610e6488398ed4fbe1ca3d005bac87c9a12924f6cd96e9cc46b4` | синтетический `CODE_CHANGE/1`; принят при всех вариантах |
| UV1-01 | 829 | `2316497f2b19fb8df60f4e513fe2ac1516203efd43239f4baad1551486840711` | U-1 §3.3 |
| UV1-02 | 809 | `ce9c6c6b20bb2f62084461110e968add14a272735bee4bd8086a7a0e13df05c4` | U-1 |
| UV1-03 | 823 | `5334015d16ed6643f223e81049200c5df3cb5112fd1b9752a9b28727a2079110` | U-1, K-1 |
| UV1-04 | 799 | `b3cb5643faf984d9f993c6cb041cfc09ebddba104bb28d0074b76c98bda28dd0` | U-1; ≡ CE-QA40-U1 |
| UV1-05 | 802 | `f24bd1706e81faec4dfb7a266316a69cf81327219fc9d5c583df35aa0dec81e0` | U-1; ≡ S3-BLK-01 |
| UV1-06 | 793 | `0e14d5fc325e884ac800e29fb2d993a19a362a303a01ea257199164aafd6f888` | U-1, выражение ревизии |
| UV1-07 | 802 | `1e5ba11ed0abf7115a62477027a6d099390934498b492c0d634b35529aee4d60` | U-1 |
| UV1-08 | 792 | `437dffbf84358769248d1ffaae2c3a08a092249c96c02c7c8368fab211d8ee98` | U-1, ведущий `-` |
| UV1-09 | 796 | `249796566d250dd681fb80186abe8c35fa492acecc12840b1dc7c08e7dbcf079` | U-1 |
| UV1-10 | 791 | `1a33aa8b3567eee0ef9b90f4bec9f2f3c97b890d9e92f1292c110c1f385b4539` | U-1 |
| UV1-11 | 800 | `dc82d0697117b152388360d30ec6dc055490f2e7ea7b08a130ea5d0fcc2be46a` | U-1, не-ASCII |
| UV1-12 | 795 | `32968f0420b974b398454a5946be1a127a6f31c06afc042657d755899a79de22` | U-1 |
| UV1-13 | 791 | `67e583b5150da3fe21208f2908086a397d0e92860212b5be272e1d23bc8c5ef7` | U-1, регистр |
| UV1-14 | 795 | `2e7ab94fb0a4e1bc7f669c92bfd2d64f7905cc3690c6c8fe2f24de7750e769a1` | U-1, управляющий символ |
| UV1-15 | 915 | `5487d89400a037b569ffe7776e852e32d432e32e10767019300a1ba8a9c08e20` | U-1, длина 128 |
| UV1-16 | 916 | `d1c798e80a07d5a159e225e47c408a55b66b75793539168e457112749728973d` | U-1, длина 129 |
| UV1-17 | 792 | `d49bdb1973efcff4ef8290b450db70ce1a3bd8921ed2ca1ea0fb99d3a7451a35` | U-1 |
| UV1-18 | 788 | `5ef169416ea1b1d22c8caff5a7a40efe0fc32a2f2506c27b331b99009d78a4ae` | U-1, `@` |
| UV1-19 | 792 | `6b350f701a5092481aa77192df9dbda329a237edb1e7cab140527453ffd0bef0` | U-1, гомоглиф |
| UV2-01 | 602 | `c5a265e648b4367d0b80d5156ad60ea6d0bd404f0a4b66f9149dd00abd3aed18` | U-2 §4.7 |
| UV2-02 | 612 | `70287da9e70d6f8c825ef82f357790a63f6852daed106e05c8ecac3a8767a125` | U-2, `//` в запретах |
| UV2-03 | 614 | `26820e57af28b4b27237a18b6cc93635cbd0c900b57f5ac9d66f987e93ac9ddc` | U-2, `..` в запретах |
| UV2-04 | 599 | `6ecef84debc30cd5c9385c1254f6ba326253cde44e8d293841c3b787fda60639` | U-2 |
| UV2-05 | 598 | `ccd9ff3c04fd85ffa5dd40da187accb304f28ade25acaabc66f8c6b969d89e52` | U-2 |
| UV2-06 | 613 | `7bc383ee251dfda36567f6d27a95a0642c8b168f57d86d0ffe01055bfba68bca` | U-2, обход в запрещённое |
| UV2-07 | 597 | `f72cc86d04f908a5ec47d72629c6561d1201a4741dbfca00d5e6c9849d4716c1` | U-2, `\` |
| UV2-08 | 590 | `db4c9a1f9714c2242019cc685312e76ab26ef451b4b3a5de4e5e2101cf6a177d` | U-2, glob |
| UV2-09 | 595 | `359b34e0a52020cf2469a6ce27ea74046222292eb03b4ec35513dc671eacca34` | U-2, класс символов |
| UV2-10 | 588 | `f5ba52d6eeb90614bf829f547224c4c2d61821d32223b4cd58a96572b3ee74c7` | U-2 |
| UV2-11 | 590 | `33b02d77447770ee18a71cb3ec513a482638747b4b669c16ff229c4aa39ac7b6` | U-2, выход выше корня |
| UV2-12 | 596 | `d261b4ff9e4c4903eb9b0bea7e4222b80abb7b1ab247b293e45c7cb1c0ceb906` | U-2, управляющий символ |
| UV2-13 | 596 | `daa8086ae934fc440fcd487ab72086bad0c3457316e6d500fc2cbb8e2fa51f71` | U-2, bidi |
| UV2-14 | 589 | `b18a7aa9bd4e225414faa5853bee7c2dfb897d41508d47ffd5e67d2da2bcc359` | U-2 |
| UV2-15 | 594 | `0082f8aa4d248e0df394eb7cc01c32f89224203d8582a367151fe439143d3b2c` | U-2, фигурные скобки |
| UV2-16 | 590 | `28b63e16bd11cc70a2b49a841e7180ca7bab0ba424b193adaec51c5a5810d1a6` | U-2, `?` |
| UV2-17 | 596 | `7cb689cb92774254bdd42fac2251c1296b8549b9d9219f8a574c8e798ff3099d` | не NFC → P1 при всех вариантах |
| UV2-18 | 587 | `4abec140c5f2f52d55b321add172cc43945f7a889aed4f9e844eff54bed432f6` | U-2 |
| UV2-19 | 583 | `8e3ce379f7f2f6f5c792c164aaeb85998a4194d05317a156cffdd7b76443f930` | U-2 |
| UV2-20 | 597 | `b3c9cc7822904c0f99a1bc5edc464b39ce7d68a30c611d01e0e670d892281025` | U-2, регистр |
| UV2-21 | 593 | `28f22a1531b0eb30018718661af346217a955da70c811cc3e259da71e2525fff` | U-2, `**` не целым сегментом |
| UV3-01 | 803 | `3dc74b6a25cdc46a81cdcbb858d35b888f03b7352a039da6c32b66fd1ec02f78` | U-3 §5.4 |
| UV3-02 | 802 | `6b16530b5171ecefa81f24ee0336ed9b22d91f2fa290a09907e31f4dd3eadde3` | U-3; ≡ S3-BLK-03 |
| UV3-03 | 803 | `c7faa129d4fa7dd4bcdd9c159f28dd7b0f322a96f722a6a0b9c7fb4f52051866` | U-3; ≡ CE-QA40-U3 |
| UV3-04 | 826 | `7b714e6bbcee4d33fa0c97cfc6848f17be52e22d4fdd1716c65a46721e295853` | U-3 |
| UV3-05 | 609 | `77c75f0a6041f7b8094ce8b8f82352a4f0d35275e38eaafad7e3dbae595a3714` | U-3, `CODE_CHANGE/1` |
| UVM-01 | 799 | `5c5c4fecfb9a1d3d1897232bd46d6ecc242a043c544e7fa60402c25ab3b99521` | одновременные нарушения, §6.3 |
| UVM-02 | 811 | `94fde6e718d1a45a500c92d980d6f0916e4c16ad084c5889897a53f005883bce` | §6.3 |
| UVM-03 | 806 | `8c8a2899b77ca5e2e3e0eab4cfa46f6c74795ed4340c3c91c66726bf94da709c` | §6.3 |
| UVM-04 | 599 | `19a88efb3973c5ef9533cfa0260600f7ec7812e808612b216429054e818b16d6` | §6.3 |
| UVM-05 | 605 | `82402867740d375df9ff8d88784457ae323f1c8281da13bafcf7077d2313ea84` | §6.3 |
| UVM-06 | 823 | `fa720bb283c593180acd831220e54558099d062c0a39b91227d5a91a40967102` | §6.3 |
| UVM-07 | 803 | `acd5aa8cfafa1499c49018c9b15a657b2b728e9ef9bd131af1fb06ffcbd9064f` | §6.3 |
| UVM-08 | 591 | `7594b2e620847c99d91b006712304d3529c09856f269bb7d7cdf4067062e7676` | §6.3 |
| CE-QA40-U1 | 799 | `b3cb5643faf984d9f993c6cb041cfc09ebddba104bb28d0074b76c98bda28dd0` | воспроизведение QA40 |
| CE-QA40-U2 | 799 | `d19efca545a1ac171a7ddd8c87d592530ebc8e49f195dcfc727412220d92d8c7` | воспроизведение QA40 (read-only база, запрет `docs//app.py`) |
| CE-QA40-U3 | 803 | `c7faa129d4fa7dd4bcdd9c159f28dd7b0f322a96f722a6a0b9c7fb4f52051866` | воспроизведение QA40 |
| S3-BLK-01 | 802 | `f24bd1706e81faec4dfb7a266316a69cf81327219fc9d5c583df35aa0dec81e0` | воспроизведение S3 §8.5 |
| S3-BLK-02 | 801 | `8644d8e201ed07aa049f61f01f430e0d1a61b1d4870ee9a7520ada9dff225d89` | воспроизведение S3 §8.5 |
| S3-BLK-03 | 802 | `6b16530b5171ecefa81f24ee0336ed9b22d91f2fa290a09907e31f4dd3eadde3` | воспроизведение S3 §8.5 |

Каждый вектор UV1-*, UV2-*, UV3-* отличается от своей базы ровно одним намеренным изменением; векторы UVM-* содержат два намеренных нарушения. Порядок списков и отсутствие повторов при этом сохранены, чтобы никакая другая фаза не сработала раньше. UV2-17 — намеренное исключение: он показывает, что P1 срабатывает раньше U-2.

`[QA44]` В ревизии #45 ни одна строка этой таблицы и ни один байт сборщика §6.1 не изменились: 61 запись, 7 сверяемых хэшей. Исправлены только **условные ожидания** некоторых векторов в §4.7 (G2-P/G2-I). Новые векторы — в §6.4.

### 6.3 Одновременные нарушения и первая диагностика

Правило первой диагностики `[S3-FAILED §3.6.1]`: самая ранняя фаза; внутри P8 — поля в порядке файла, внутри списка — (а) форма, (б) элементы, (в) повторы, (г) порядок; затем X1–X4. Оно здесь не меняется. Таблица показывает, как **выбор** владельца влияет на первую метку. Метки только существующие (`S3-C02`, `S3-C03`); точки диагностики — документарные указатели.

| Вектор | Нарушения | Первая метка @ точка при вариантах |
|---|---|---|
| UVM-01 | `base_sha` в верхнем регистре (V4, строка 7) + `target_branch: main feature` (строка 8) | `S3-C03 @ P8.base_sha` при **любом** выборе U-1: поле стоит раньше в файле |
| UVM-02 | `target_branch: main feature` + RO с `G3-deploy` | U1-A/B/C → `P8.target_branch` при любом U-3. U1-0 + U3-A1 → `P8.X5`; U1-0 + U3-A2 → `P8.gates`; U1-0 + U3-B/C → принят (U-1 остаётся BLOCKED) |
| UVM-03 | `target_branch:main feature` (нет пробела после `:`) + запрет `docs//app.py` | `S3-C02 @ P3:L8` при любых U-1/U-2: лексика раньше P8 |
| UVM-04 | CC: allowed `docs//a.txt` + `none` в `forbidden_paths` (V8) | U2-A/B → `P8.allowed_paths` (поле раньше); U2-C1/C2 → `P8.forbidden_paths` (существующее правило V8) |
| UVM-05 | CC: allowed `docs//a.txt` и `docs/a.txt` | U2-A/B → `P8.allowed_paths`, подпроверка (б), элемент 1. U2-C → принят: две разные строки. На уровне 1 при U2-B из такого текста Issue получится одна строка `docs/a.txt` — хэш совпадёт с Issue, где указан только `docs/a.txt` (§8.2) |
| UVM-06 | RO + `git_commit:create` (X2) + `G3-deploy` | U3-A1 → `P8.X2` (X2 раньше X5); U3-A2 → `P8.gates` (поля раньше сочетаний); U3-B/C → `P8.X2` |
| UVM-07 | RO, `gates`: `G3-deploy`, `G0-intake` (порядок, V9) | `S3-C03 @ P8.gates` при любом U-3: подпроверка (г) раньше проверки профиля в A2 и раньше X5 в A1. Наблюдаемая метка и точка при A1 и A2 одинаковы |
| UVM-08 | CC: `target_branch: -main` + allowed `../app.py` | U1-A/B/C → `P8.target_branch` (строка 8 раньше строки 17) при любом U-2. U1-0 + U2-A/B/C2 → `P8.allowed_paths`; U1-0 + U2-C1 → принят (оба BLOCKED) |

**Без новых кодов.** Ни один вариант не вводит `reason_code`, итог, код выхода или метку `S3-C*`. Внешнее отображение остаётся тем, что предлагает S3 §3.6.6: `SCHEMA_INVALID` до G0, `UNAPPROVED_BASE` на контрольных точках. У U3-C на контрольной точке используется существующее сообщение `BLOCKED`. `UNRESOLVED`/5 не вводится и не используется.


### 6.4 `[QA44]` Дополнительные векторы для P2-QA44-01 и P2-QA44-02

Это отдельный сборщик. Он не меняет блок §6.1, и 61 исходная запись (длины, SHA-256) и 7 сверяемых хэшей остаются прежними. Векторы — синтетические байты, **не фикстуры**: они не входят в `fixtures/` и не меняют `fixtures/SHA256SUMS`. Блок самодостаточен. Он содержит побайтную копию базы `C` (U-POS-CC) и останавливается, если её хэш не равен `8ef90e8a…46b4`. Три вектора `CE-QA44-*` сверяются с хэшами `[QA44]`. Функция `reduce_path` — документарная иллюстрация шагов (1)–(5) U2-B без проверки символов (то есть поведение R0/R2). Это **не** парсер и **не** валидатор SPEC: она лишь строит байты уровня 1, чтобы показать свёртку. `bad_code_points` перечисляет кодовые точки из набора U2-A и ничего не решает.

Извлечь и запустить (Python ≥ 3.8, только стандартная библиотека, в пустом каталоге; с любым аргументом записываются файлы `<имя>.txt`):

```bash
sed -n '/^<!-- U1U3-QA44-BUILD BEGIN -->$/,/^<!-- U1U3-QA44-BUILD END -->$/p' docs/agents/v2/SPEC3-U1U3-DECISIONS.md | sed '1,2d' | sed '$d' | sed '$d' > build-qa44.py
python3 -I build-qa44.py
```

<!-- U1U3-QA44-BUILD BEGIN -->
```python
import hashlib, sys, unicodedata
# QA44 supplement (Issue #45). Synthetic bytes only. Not a SPEC parser or validator.
SHA = '48b0454d3b68f90e7687bd00b2ccc5a9318f6d70'
C = ['TAXI-ISSUE-SPEC/3', 'task_id: TAXI-PROTOCOL-EXAMPLE-41', 'depends_on:', '- none',
     'work_profile: CODE_CHANGE/1', 'task_role: IMPLEMENTER',
     'base_sha: ' + SHA, 'target_branch: main', 'source_ref: refs/heads/main',
     'source_sha: ' + SHA, 'branch_policy: REQUIRED', 'evidence_policy: none',
     'allowed_actions:', '- git_commit:create', '- git_ref:create', '- repo:read',
     'allowed_paths:', '- docs/example.txt', 'forbidden_paths:', '- .github/**', '- app.py',
     'acceptance.count: 1', 'acceptance.1.id: AC-1', 'acceptance.1.required: true',
     'acceptance.1.text: Example criterion.', 'gates:', '- G0-intake', '- G2-merge']

def sub(base, old, new):
    assert base.count(old) == 1, old
    i = base.index(old)
    return base[:i] + new + base[i + 1:]

def ap(*v): return sub(C, '- docs/example.txt', ['- ' + x for x in v])
def fp(*v): return sub(C, '- app.py', ['- app.py'] + ['- ' + x for x in v])

def reduce_path(p):
    # Documentary illustration of U2-B level-1 steps (1)-(5) only. No character check.
    out = []
    for s in p.split('/'):
        if s in ('', '.'):
            continue
        if s == '..':
            if not out:
                return None          # above root: SPEC not formed
            out.pop()
            continue
        out.append(s)
    return '/'.join(out) or None     # empty result: SPEC not formed

def issue_level(lines):
    # reduce every list element of allowed_paths / forbidden_paths, then v1 dedup + bytewise sort
    res, cur, buf = [], None, []
    def flush():
        if cur is not None:
            res.extend('- ' + x for x in sorted(set(buf), key=lambda s: s.encode('utf-8')))
    for ln in lines:
        if ln in ('allowed_paths:', 'forbidden_paths:'):
            flush(); res.append(ln); cur, buf = ln, []
        elif cur is not None and ln.startswith('- '):
            r = reduce_path(ln[2:])
            assert r is not None, ln
            buf.append(r)
        else:
            flush(); cur, buf = None, []
            res.append(ln)
    flush()
    return res

def bad_code_points(p):
    # code points that the U2-A set of section 4.3 excludes (reported, not judged)
    r = []
    for ch in p:
        o = ord(ch)
        if o <= 0x1F or 0x7F <= o <= 0x9F or ch == '\\' or unicodedata.category(ch) == 'Cf' \
           or (o > 0x7F and unicodedata.category(ch) == 'Zs'):
            r.append('U+%04X/%s' % (o, unicodedata.category(ch)))
    return r

L2 = [  # level 2: canonical bytes as they would be hashed
 ('U-POS-CC', C),
 ('CE-QA44-GLOB3', ap('docs/***/a.md')),
 ('CE-QA44-CANCEL-BIDI', ap('docs/\u202e/../example.txt')),
 ('CE-QA44-CANCEL-ESC', ap('docs/\x1b[31m/../example.txt')),
 ('U45-G2-01', ap('example.txt')),
 ('U45-G2-02', ap('!docs/example.txt')),
 ('U45-G2-03', ap('#example.txt')),
 ('U45-G2-04', ap('docs/\\*.md')),
 ('U45-R-01', ap('docs/\u200b/../example.txt')),
 ('U45-R-02', ap('docs/\x7f/../example.txt')),
 ('U45-R-03', fp('docs/\u2066x/../../app.py')),
 ('U45-R-04', ap('docs/\u202e/x/../example.txt')),
]
L1 = ['CE-QA44-CANCEL-BIDI', 'CE-QA44-CANCEL-ESC', 'U45-R-01', 'U45-R-02', 'U45-R-03', 'U45-R-04']
EXPECT = {
 'U-POS-CC':            '8ef90e8aaf5a610e6488398ed4fbe1ca3d005bac87c9a12924f6cd96e9cc46b4',
 'CE-QA44-GLOB3':       '4a6535492f43cba859a0431456724c23ec88c3af195131fb0ce3ca34b27385c7',
 'CE-QA44-CANCEL-BIDI': '2d09951546bfc6925e919d1cf2eed172559036447928191746aa935ebefa0c67',
 'CE-QA44-CANCEL-ESC':  '1314b59ef0fad468a986bd677d710d5e826f7b28fa1e00e8306aae4971436a8d',
}
def emit(name, lines):
    b = ('\n'.join(lines) + '\n').encode('utf-8')
    d = hashlib.sha256(b).hexdigest()
    if name in EXPECT:
        assert d == EXPECT[name], (name, d)
    if len(sys.argv) > 1:
        open(name + '.txt', 'wb').write(b)
    nfc = unicodedata.is_normalized('NFC', b.decode('utf-8'))
    print(name, len(b), d, *([] if nfc else ['NOT-NFC']))
    return d
seen = {}
for name, lines in L2:
    d = emit(name, lines)
    assert d not in seen, (name, seen.get(d))
    seen[d] = name
for name in L1:
    raw = [x for n, x in L2 if n == name][0]
    elems = [ln[2:] for ln in raw if ln.startswith('- ') and ('..' in ln)]
    d = emit(name + '@L1', issue_level(raw))
    print('  raw', [e.encode('utf-8').hex() for e in elems], 'excluded', [bad_code_points(e) for e in elems],
          'reduced', [reduce_path(e).encode('utf-8').hex() for e in elems], '= ' + seen.get(d, 'new'))
```
<!-- U1U3-QA44-BUILD END -->

Скрипт записан только ASCII-символами (`\uXXXX`, `\x1b`, `\x7f`), поэтому в записке нет буквальных U+202E, U+200B, U+2066, ESC или DEL.

**Уровень 2 — канонические байты (прямой разбор, без формирования):**

| ID | Байт | SHA-256 | Что проверяет |
|---|---:|---|---|
| U-POS-CC | 597 | `8ef90e8aaf5a610e6488398ed4fbe1ca3d005bac87c9a12924f6cd96e9cc46b4` | контроль: тот же вход, что в §6.2; подтверждает, что копия `C` в этом блоке совпадает побайтно |
| CE-QA44-GLOB3 | 594 | `4a6535492f43cba859a0431456724c23ec88c3af195131fb0ce3ca34b27385c7` | P2-QA44-01; allowed `docs/***/a.md`; воспроизведение `[QA44]` |
| CE-QA44-CANCEL-BIDI | 604 | `2d09951546bfc6925e919d1cf2eed172559036447928191746aa935ebefa0c67` | P2-QA44-02; allowed `docs/<U+202E>/../example.txt` (несвёрнутые байты); воспроизведение `[QA44]` |
| CE-QA44-CANCEL-ESC | 606 | `1314b59ef0fad468a986bd677d710d5e826f7b28fa1e00e8306aae4971436a8d` | P2-QA44-02; allowed `docs/<ESC>[31m/../example.txt`; воспроизведение `[QA44]` |
| U45-G2-01 | 592 | `b1d516e947f864b8c073fdf24cbd9fe4882f9192e0700801bd2058b64365e772` | P2-QA44-01; allowed `example.txt` (шаблон без `/`) |
| U45-G2-02 | 598 | `2575d0ce8b5e40ae09af8a5df1c36faea1fe683b025f9adfbd9211e4c034f9eb` | P2-QA44-01; allowed `!docs/example.txt` (ведущий `!`) |
| U45-G2-03 | 593 | `91281f1d62194e7c37b752910ff5891b93b342728ee8eb4399cae3634912df53` | P2-QA44-01; allowed `#example.txt` (ведущий `#`) |
| U45-G2-04 | 591 | `b593c4817b271b7bd0a657cded29595375bfb6f1d14599197a28ce0e821df07d` | P2-QA44-01; allowed `docs/\*.md` (экранирование `\`) |
| U45-R-01 | 604 | `6c0e6009a6e4b4e2ff4aa49b08b00d8eb34b4d7ee104ae840ce8a65fd411f3d1` | P2-QA44-02; allowed `docs/<U+200B>/../example.txt` (`Cf`) |
| U45-R-02 | 602 | `b14671e8ca32daecad379e09c2554a976ac957fbe0a2e4a7e0ebd1cf4c4777ae` | P2-QA44-02; allowed `docs/<U+007F>/../example.txt` (`Cc`) |
| U45-R-03 | 622 | `282edd9d3752b6a0b78b7b7e04e3ff434abc9146096d0dd4ef3e068753357db4` | P2-QA44-02; forbidden + `docs/<U+2066>x/../../app.py` (сторона запретов) |
| U45-R-04 | 606 | `345dd7565f52a02a76b52c6a0b16c556214c21e909993f1c838d3695b06e8494` | P2-QA44-02; allowed `docs/<U+202E>/x/../example.txt` (контроль: символ остаётся) |

**Уровень 1 — байты, которые дало бы формирование из исходного текста Issue при U2-B + R0/R2 (свёртка без проверки символов):**

| ID | Байт | SHA-256 | Итог |
|---|---:|---|---|
| CE-QA44-CANCEL-BIDI@L1 | 597 | `8ef90e8aaf5a610e6488398ed4fbe1ca3d005bac87c9a12924f6cd96e9cc46b4` | = U-POS-CC (намеренный дубликат) |
| CE-QA44-CANCEL-ESC@L1 | 597 | `8ef90e8aaf5a610e6488398ed4fbe1ca3d005bac87c9a12924f6cd96e9cc46b4` | = U-POS-CC (намеренный дубликат) |
| U45-R-01@L1 | 597 | `8ef90e8aaf5a610e6488398ed4fbe1ca3d005bac87c9a12924f6cd96e9cc46b4` | = U-POS-CC (намеренный дубликат) |
| U45-R-02@L1 | 597 | `8ef90e8aaf5a610e6488398ed4fbe1ca3d005bac87c9a12924f6cd96e9cc46b4` | = U-POS-CC (намеренный дубликат) |
| U45-R-03@L1 | 597 | `8ef90e8aaf5a610e6488398ed4fbe1ca3d005bac87c9a12924f6cd96e9cc46b4` | = U-POS-CC (намеренный дубликат) |
| U45-R-04@L1 | 601 | `61be50d4a161321e2b0263decbe5398250e51b143b1ebdb886038e4669cd0432` | новые байты: `docs/<U+202E>/example.txt`; отвергаются на уровне 2 при U2-A/U2-B |

Исходные элементы (hex UTF-8) и их свёртка, как печатает сборщик:

| ID | Исходный элемент (hex) | Кодовая точка вне набора U2-A | После свёртки (hex) |
|---|---|---|---|
| CE-QA44-CANCEL-BIDI | `646f63732fe280ae2f2e2e2f6578616d706c652e747874` | U+202E `Cf` | `646f63732f6578616d706c652e747874` (`docs/example.txt`) |
| CE-QA44-CANCEL-ESC | `646f63732f1b5b33316d2f2e2e2f6578616d706c652e747874` | U+001B `Cc` | `646f63732f6578616d706c652e747874` |
| U45-R-01 | `646f63732fe2808b2f2e2e2f6578616d706c652e747874` | U+200B `Cf` | `646f63732f6578616d706c652e747874` |
| U45-R-02 | `646f63732f7f2f2e2e2f6578616d706c652e747874` | U+007F `Cc` | `646f63732f6578616d706c652e747874` |
| U45-R-03 | `646f63732fe281a6782f2e2e2f2e2e2f6170702e7079` | U+2066 `Cf` | `6170702e7079` (`app.py`, дедупликация) |
| U45-R-04 | `646f63732fe280ae2f782f2e2e2f6578616d706c652e747874` | U+202E `Cf` | `646f63732fe280ae2f6578616d706c652e747874` |

**Дубликаты — честный отчёт.**
- Среди 12 входов уровня 2 повторов нет (сборщик проверяет это `assert`). Ни один из них не совпадает ни с одним из 61 хэша §6.2. Исключение — контроль `U-POS-CC`, который намеренно равен той же записи §6.2.
- Пять выходов уровня 1 (`CE-QA44-CANCEL-BIDI@L1`, `CE-QA44-CANCEL-ESC@L1`, `U45-R-01@L1`, `U45-R-02@L1`, `U45-R-03@L1`) побайтно равны U-POS-CC. Это и есть демонстрируемый эффект: разные исходные тексты дают одни канонические байты. Это не совпадение SHA-256 разных байтов.
- `U45-R-04@L1` (601 байт) — новые байты, ни с чем не совпадают.
- Внутри исходных 61 записи остаются четыре известные пары одинаковых байтов (UV1-04 ≡ CE-QA40-U1, UV1-05 ≡ S3-BLK-01, UV3-02 ≡ S3-BLK-03, UV3-03 ≡ CE-QA40-U3), как и в исходной версии §6.2. 61 запись — это 57 различных байтовых входов.

Первая диагностика для этих векторов условна (§4.4.1, §4.7): на уровне 2 при U2-A/U2-B — `S3-C03 @ P8.allowed_paths` (для U45-R-03 — `P8.forbidden_paths`), подпроверка (б), первый элемент; для векторов G2 — в зависимости от G1/G2-P/G2-I по таблице §4.7. На уровне 1 меток `S3-C*` нет: «SPEC не формируется». Новых меток, `reason_code`, итогов и кодов выхода нет.

---

## 7. AC-7 — что потребуется в будущем при каждом выборе (ничего из этого здесь не делается)

### 7.1 Карта изменений

| Выбор | PROFILES (v2 DRAFT) | SPEC3 (предложение) | F4 (будущая ревизия от Base) | EVIDENCE / LIFECYCLE / QA-REPORT | TEST-CASES / fixtures | Гейты владельца |
|---|---|---|---|---|---|---|
| U1-A / U1-B / U1-C | §2.2 L73 и §2.5: грамматика `target_branch` и R-EXCL. При U1-C ещё вопрос о согласовании `<branch>` §2.4 (K-1) — отдельное решение | строка P8 `target_branch` (L262) из «непусто» → выбранная грамматика; строка U-1 §3.8 снимается; S3-BLK-01 и UV1-* становятся обычными ожидаемыми исходами | при U1-C — сверка с [F4 L177](https://github.com/iprus2026-tech/taxi-dashboard/blob/e97df81117d948f60b15d215916dacffda5c50cd/docs/agents/v2/F4-WIRE.md#L177) | S2 в PROFILES §5 и проверка G0 — без изменений по смыслу | новые строки тестов из §3.3; векторы — **новые** файлы (например `fixtures/spec3-u/`) с отдельным списком хэшей | интеграционная задача: новая SPEC + G0 + независимый QA + G2. При U1-Q2(б) — отдельно поправка v1 |
| U1-D (слой) | реестр целевых веток и порядок его изменения | проверка принадлежности реестру — процедурная или в P8 (решить при интеграции) | — | LIFECYCLE: кто и как меняет реестр | тесты реестра | каждое изменение реестра — решение владельца |
| U2-A | §2.1/§2.2 L79–L80: грамматика пути и glob по U2-G, правило Unicode по U2-N | строки P8 `allowed_paths`/`forbidden_paths` (L268–L269); строка U-2 §3.8 снимается | `path` (F4 L179) выровнять с выбранной грамматикой | EVIDENCE: пути `git_blob` по той же грамматике; QA-REPORT: правило сопоставления (U2-N) | строки из §4.7; новые файлы векторов | то же; при U2-Q5(б) — поправка v1 §4.2 L150–L151 |
| U2-B | как U2-A плюс алгоритм канонизации на уровне 1 с доказательством идемпотентности; `[QA44]` плюс выбранный U2-R (§4.4.1) | как U2-A; §3.5 «источник в тексте Issue» дополняется канонизацией | как U2-A | QA-REPORT/LIFECYCLE: пересчёт SPEC на контрольных точках включает канонизацию | плюс векторы «текст Issue → байты» | то же; при (б) — поправка v1 |
| U2-C1 / U2-C2 | явная запись выбранного прочтения «без `./`» | P8 строки путей с явной пометкой «непрозрачная строка»; U-2 §3.8 переходит из BLOCKED в осознанное ограничение | как выбрано | QA-REPORT: предупреждение о ложной защите в запретах | строки из §4.7 | то же |
| U3-A1 | §1 таблица L22 и §2.2 L87: явная недопустимость G2/G3 для read-only | новая строка X5 после X4 (§3.6.4); U-3 §3.8 снимается | — | — | строки §5.4 и UVM-06 | интеграционная задача |
| U3-A2 | как A1 | в правило поля `gates` (L270) добавляется подпроверка профиля | — | — | строки §5.4 и UVM-06 (другая точка) | то же |
| U3-B | §1 L22: «записанные G2/G3 не имеют эффекта» | P8 без изменений; §3.8: U-3 снимается как осознанное правило | — | LIFECYCLE: машина состояний — `owner-gate` только для применимых гейтов; G2/G3 по read-only недействительны | тесты недействительного G2 по read-only | интеграционная задача |
| U3-C | §1 L22: «G2/G3 для read-only делают задачу невыполнимой» | P8 без изменений | — | LIFECYCLE: явный `BLOCKED` у `owner-gate` | тест fail-late | интеграционная задача |

### 7.2 Что сохраняется при любом выборе

- История и отклонённые HEAD: `141c9ff…` (#36), `0821d1d…` (#39), `e97df81…` (#34) и прочие замороженные ветки не переписываются.
- 30 замороженных фикстур и `fixtures/SHA256SUMS` (`e475e0af…8fd5`) не меняются. Новые векторы — только новыми файлами.
- `issue_spec_sha256` существующих SPEC/1 не меняется ни одним вариантом: `target_branch` в SPEC/1 нет, все исторические пути проходят любой вариант U-2 без изменения (§2.3 п.4), а U-3 к SPEC/1 неприменим.

### 7.3 Когда нужна поправка **действующего v1**, а не только предложение v2

| Случай | Почему | Требуется |
|---|---|---|
| U1-Q2(б): грамматика `target_branch` применяется к строке в G0 по v1 §4.3 | меняет условие действительности G0 действующего протокола | отдельная задача на `docs/agents/PROTOCOL.md` с G0, независимым QA и G2; новые строки Приложения A |
| U2-Q5(б): грамматика путей применяется к SPEC/1 по v1 §4.2 L150–L151 | меняет условие формирования SPEC/1 | то же. При U2-B ещё и меняется алгоритм канонизации SPEC/1. Исторические хэши при этом не меняются (§4.8), но правило — да |
| U-3 | в v1 нет профилей | поправка v1 не нужна |
| Все остальные выборы | касаются только SPEC/2/SPEC/3 (v2 DRAFT, SPEC3 PROPOSAL) | интеграционная задача v2 |

---

## 8. AC-8 — OD-1…OD-7 и Q8/B-07 остаются отдельно и `PENDING`

### 8.1 Статус

OD-1…OD-7 (S3 §10) и Q8/B-07 (S3 §4.3, §10) — открытые вопросы владельца из `[S3-FAILED]`. G0 этой задачи их не решает, и эта записка тоже: ни прямо, ни по умолчанию, ни через вывод. U-1…U-3 не являются вопросами OD-n (S3 §10 говорит то же).

### 8.2 Пересечения

| Вопрос | Пересечение с U-1…U-3 | Вывод |
|---|---|---|
| OD-1 (код для SB-4/SB-5) | нет: относится к отчёту, а не к разбору SPEC | независим |
| OD-2 (SPEC без `required: true`) | нет | независим |
| OD-3 (отчёты для SPEC/2) | нет | независим |
| OD-4 (`reason_code` для необязательного `NOT_RUN`) | нет | независим |
| OD-5 (строка `acceptance_required` в G0) | косвенное: и U1-Q2(б), и OD-5 касаются содержимого `note` G0 | решаются отдельно; один выбор не предрешает другой |
| OD-6 (правило STALE) | косвенное: при U-1 без грамматики выражение `main~1` влияет на то, какой tip читается в S3 и в source-check | U-1 сужает входы, но правило R-STALE не выбирает |
| OD-7 (`NOT_VERIFIED` против позднего `VERIFIED`) | нет | независим |
| Q8/B-07 (Issue правили и вернули к тем же байтам) | **есть** при U2-B: разные тексты Issue (`docs//a` и `docs/a`) дают один хэш. Это расширяет класс «другой текст — тот же хэш», который уже есть в v1 (сортировка, дедупликация, сжатие пробелов) | U2-B не решает Q8. Если владелец выберет U2-B, решение Q8 должно явно сказать, считается ли такая правка «полем, отредактированным» по v1 §4.2 п.4. `[QA44]` При U2-R0/R2 в этот класс попадают и исходные тексты с запрещёнными символами в удаляемых сегментах (§4.4.1) |

### 8.3 Не решается этой запиской

Также не решаются: O-ADJ-1 (§5.6); согласование `<branch>` в PR §2.4 с именами `agent/<agent>/<id>.<step>` (K-1) вне `target_branch`; `UNRESOLVED`/5; принудительное `required: true`; реализация валидатора; QA PASS; PR, G2, merge, deploy; активация v2.

---

## 9. AC-9 — матрица решений владельца

### 9.1 Матрица

| Вопрос | Варианты | Значение по умолчанию | Главный компромисс | Обязательства доказательства для будущей интеграции |
|---|---|---|---|---|
| U1-Q1 | U1-A, U1-B, U1-C (+ слой U1-D) | **PENDING / NO DEFAULT** | широта и совместимость с Git (A) против узости без гомоглифов (B, C); B ломает имена с точкой (K-1) | (1) полный текст грамматики в протоколе без ссылки на версию Git; (2) доказательство, что каждое принятое значение — корректная ветка Git (для B и C — подмножество A) и не является выражением ревизии; (3) векторы §3.3 как тесты; (4) отсутствие изменения исторических хэшей |
| U1-Q2 | (а) только v2; (б) также G0 по v1 | **PENDING / NO DEFAULT** | область действия против цены поправки действующего v1 | при (б) — отдельная задача на v1 с собственным QA |
| U2-Q1 | U2-A, U2-B, U2-C1, U2-C2 | **PENDING / NO DEFAULT** | строгость без молчаливых правок (A) против удобства и защитного смысла канонизации (B); C оставляет ложную защиту | (1) тотальность грамматики; (2) для B — идемпотентность `c(c(x)) = c(x)`, запрет выхода выше корня, порядок дедупликации после канонизации; (3) соответствие политике владельца п.4; (4) векторы §4.7 и §4.4 |
| U2-Q2 | G1, G2-P, G2-I (+ параметры §4.5) `[QA44]` | **PENDING / NO DEFAULT** | закрытость против выразительности; G2-P против G2-I — недопустимость против «обычных звёздочек» и область шаблонов без `/` | точная семантика совпадения, включая `**` с нулём сегментов и файлы-точки; тесты на исторических шаблонах |
| U2-Q3 | N1, N2 (+ проверка коллизий регистра) | **PENDING / NO DEFAULT** | fail-closed против удобства | тест NFD-обхода явного запрета; тест коллизии регистра |
| U2-Q4 | `M`, пробел в сегменте | **PENDING / NO DEFAULT** | — | граничные векторы |
| U2-Q5 | (а) только v2; (б) также SPEC/1 по v1 | **PENDING / NO DEFAULT** | как U1-Q2 | при (б) — отдельная задача на v1 |
| U2-Q6 `[QA44]` | R1, R2, R3 (R0 — сравнение); только при U2-B | **PENDING / NO DEFAULT** | синтаксическая гарантия до свёртки (R1) против процедурного раскрытия (R2) против отказа от свёртки `x/..` (R3) | векторы §4.4.1/§6.4 (CANCEL, U45-R-01…04) как тесты «текст Issue → байты»; для R1 — один список запрещённых кодовых точек на обоих уровнях; для R2 — формат раскрытия исходного текста |
| U3-Q1 | U3-A1, U3-A2, U3-B, U3-C | **PENDING / NO DEFAULT** | ранний отказ (A) против мёртвых (B) или блокирующих (C) записей; A1 против A2 — только порядок первой диагностики | (1) правило в одном месте (X5 или поле); (2) векторы §5.4 и UVM-06/07; (3) для B/C — правка машины состояний и тест недействительного G2 |

Записка остаётся верной при любом выборе: каждая таблица перечисляет ожидания для всех вариантов. Ни один раздел не опирается на то, что выбран какой-то конкретный вариант.

### 9.2 Ранжирование рисков, если вопрос останется нерешённым

| Ранг | Вопрос | Почему | Наибольший остаточный риск по вариантам |
|---|---|---|---|
| 1 | U-1 | значение подставляется в команды Git контрольных точек (v1 §4.3 п.5, PR §5 S3). Выражение ревизии подменяет tip при проверке предка (§2.3 п.2); шаблон `ls-remote` совпадает по хвосту и glob (§2.3 п.3). Равенство SPEC ↔ G0 от этого не защищает: одинаково плохие значения равны | U1-A: гомоглифы при утверждении G0. U1-B: совместимость имён с точкой. U1-C: расхождение с PR §2.4 |
| 2 | U-2 | ложная защита в запретах (`docs//app.py`, `docs/../app.py` при C1); обход в запрещённое через `..` при канонизирующих инструментах; подмена отображения (bidi, ESC); `[QA44]` исчезновение запрещённых символов в удаляемых свёрткой сегментах (U2-B без R1/R3); неоднозначность G2-P/G2-I; NFD-обход явного запрета | U2-C1 > U2-C2 > U2-B (молчаливые свёртки, Q8) > U2-A (неудобство) |
| 3 | U-3 | нет прав на запись (X2/X3 уже закрывают запись для read-only); риск — неясность утверждённого текста и невыполнимые задачи | U3-C (fail-late) > U3-B (мёртвые записи) > U3-A2 ≈ U3-A1 |

Ранжирование — мнение автора для ориентира владельца, а не решение. Автор не независим (§0).

### 9.3 Предлагаемый путь дальнейших разрешений

1. **Независимый READ_ONLY дизайн-QA этой записки.** Отдельная задача, личный G0 владельца, свежая сессия проверяющего (не `claude-code`), CLAIM/ASSIGN. Проверяющий заново собирает векторы §6 и проверяет матрицу доказательств §2. Автор свою записку не проверяет.
2. **Личное решение владельца G1-design.** По каждому из вопросов U1-Q1, U1-Q2, U2-Q1…U2-Q6 (`[QA44]`: U2-Q6 добавлен), U3-Q1 — явный выбор с указанием SHA-256 этой записки, утверждённого после QA. Решение не может выводиться из отчёта агента или из этой записки.
3. **Интеграционная задача** (отдельная SPEC и G0). Она переносит выбранные правила в черновики v2 и в исправленное предложение SPEC3 (после #41) с новыми векторами-файлами, не трогая 30 замороженных фикстур.
4. **Независимый QA интеграции**, затем личный G2 и ручной merge владельцем.
5. **Поправки действующего v1**, если выбраны U1-Q2(б) или U2-Q5(б): отдельная задача с G0, QA и G2.
6. **Отдельно:** валидатор и исполняемые тесты; отдельно — решение об активации v2.

---

## 10. AC-10 — ограничения, NOT_RUN и раскрытие

- **NOT_RUN:** исполняемый валидатор SPEC/2 или SPEC/3, парсер pathspec/gitignore, сопоставление шаблонов Git (`wildmatch`), CI, runtime, browser, production, тесты приложения. Ожидаемые исходы §3–§6 выведены из текста.
- `[QA44]` **Выполнено в сессии ревизии #45 (`session_01UHQjybuJHfkZZe4pGnyDDM`; только чтение и сборка байтов):**
  - пересчёт SPEC/1 #45 по v1 §4.2 и сверка G0, CLAIM, ASSIGN, lease;
  - `git ls-remote`, `git cat-file` для исходного файла #42, `sha256sum -c` для `fixtures/SHA256SUMS`;
  - чтение публичного REST API Issues и комментариев (в том числе повторный подсчёт §2.3 п.4 и проверка тела QA44);
  - загрузка пакета Ubuntu `git-doc` 2.43.0 и чтение двух текстовых файлов документации (`[GIT-DOC]`); сам Git для сопоставления шаблонов не запускался;
  - запуск обоих сборщиков (§6.1 и §6.4), которые только строят байты и хэши и ничего не разбирают.
- **Выполнено в сессии исходной версии #42 (перенесено без изменений):**
  - пересчёт SPEC/1 по v1 §4.2;
  - `git ls-remote`, `git show`, `git diff --name-status` и `sha256sum -c` для `fixtures/SHA256SUMS`;
  - наблюдения `git check-ref-format --branch`, `git rev-parse --verify` и `git ls-remote <шаблон>` (§2.3);
  - чтение публичного REST API Issues;
  - сборщик §6.1, который только строит байты и хэши и ничего не разбирает.
- **Изменения в репозитории:** ровно один новый файл `docs/agents/v2/SPEC3-U1U3-DECISIONS.md` в ветке задачи #45 от Base. Существующие файлы не правились. Ветка и HANDOFF #42 не менялись.
- **Самопроверка не является QA.** Требуется независимый READ_ONLY дизайн-QA (`codex-qa`, новый личный G0, точный HEAD ревизии) и затем личное решение владельца G1-design (§9.3). Автор ревизии не может проверять её сам.
- **Граница доверия:** общий логин GitHub не подтверждает личность (v1 §0.1). Хэш подтверждает неизменность байтов, но не автора.

### 10.1 Трассировка AC-1…AC-10 Issue #42 (исходная версия, перенесено без изменений)

| AC | Где |
|---|---|
| AC-1 | §0, §1; CLAIM #6877932024, ASSIGN #6878416032; HANDOFF — в Issue #42 |
| AC-2 | §0.1, §2 |
| AC-3 | §3 |
| AC-4 | §4 |
| AC-5 | §5 |
| AC-6 | §6 (сборщик, 61 запись, из них 7 сверяются с ранее опубликованными хэшами; §6.3 — первая диагностика) |
| AC-7 | §7 |
| AC-8 | §8 |
| AC-9 | §9 |
| AC-10 | §10; SHA-256 файла и permalink — в HANDOFF/1 |

### 10.2 `[QA44]` Трассировка AC-1…AC-10 Issue #45

| AC | Где |
|---|---|
| AC-1 | §0, §1; CLAIM #6881830732, ASSIGN #6881975950; HANDOFF — в Issue #45 |
| AC-2 | §0 (исходная версия и основание), §0.1 (`[GIT-DOC]`, `[QA44]`), §11.1 |
| AC-3 | §4.5 (G2-P/G2-I), §4.7 (UV2-21, CE-QA44-GLOB3 и др.), §6.4 |
| AC-4 | §4.1, §4.3 (U2-B, шаг 0), §4.4, §4.4.1 (U2-R, U2-Q6), §4.8, §6.4 |
| AC-5 | §2.3 п.4 (десять файлов, правило отсечки, манифест) |
| AC-6 | §6.2 (61 запись без изменений), §4.7 (исправленные ожидания), §6.4 (новые векторы, дубликаты) |
| AC-7 | §11.2 (карта изменений относительно #42) |
| AC-8 | §4.9, §9.1 (всё `PENDING / NO DEFAULT`, добавлен U2-Q6), §8, §11.4 |
| AC-9 | §11.1, §11.3, §11.5; §10 (NOT_RUN) |
| AC-10 | §10; SHA-256 файла, HEAD и permalink — в HANDOFF/1 Issue #45 |

---

## 11. `[QA44]` Трассировка находок QA44, карта изменений, самопроверка

### 11.1 Находка → изменение → доказательство

| Находка `[QA44]` | Что было в #42 | Что изменено | Доказательство |
|---|---|---|---|
| **P2-QA44-01** — G2 объединяет разные грамматики; ожидание UV2-21 необоснованно | один вариант «G2 — wildmatch Git (как в pathspec `:(glob)` / gitignore)» ([#42 L231](https://github.com/iprus2026-tech/taxi-dashboard/blob/dcf9854687c7174ac55d4d8d94713cdd078533f0/docs/agents/v2/SPEC3-U1U3-DECISIONS.md#L231)); UV2-21 «acc (G2: `**` как `*`)» ([L275](https://github.com/iprus2026-tech/taxi-dashboard/blob/dcf9854687c7174ac55d4d8d94713cdd078533f0/docs/agents/v2/SPEC3-U1U3-DECISIONS.md#L275)) | G2 снят; два отдельных варианта G2-P и G2-I с явной неэквивалентностью и таблицей несовместимостей (§4.5); условные ожидания UV2-08/09/10/15/16/19/21 разделены (§4.7); новые векторы CE-QA44-GLOB3, U45-G2-01…04 (§4.7, §6.4); U2-Q2 расширен (§4.9, §9.1). Грамматика не выбрана | `[GIT-DOC]` glossary L425 «considered invalid» и gitignore L131 «considered regular asterisks» (файлы и хэши — §0.1); привязка без `/`, `!`, `#`, завершающий `/` — gitignore L75–L101; CE-QA44-GLOB3 594 байт / `4a653549…85c7` = `[QA44]` |
| **P2-QA44-02** — при U2-B запрещённые символы удаляются свёрткой до проверки | порядок «свёртка → U2-A» ([#42 L208](https://github.com/iprus2026-tech/taxi-dashboard/blob/dcf9854687c7174ac55d4d8d94713cdd078533f0/docs/agents/v2/SPEC3-U1U3-DECISIONS.md#L208)); «Подмена отображения … U2-B: отвергается» без уровня ([L284](https://github.com/iprus2026-tech/taxi-dashboard/blob/dcf9854687c7174ac55d4d8d94713cdd078533f0/docs/agents/v2/SPEC3-U1U3-DECISIONS.md#L284)) | явная граница уровней (§4.1); шаг (0) и риск в определении U2-B (§4.3); новые строки §4.4; подвыбор U2-R: R0 (сравнение), R1 (отказ до нормализации), R2 (точно суженная проверка канонических байтов с раскрытием), R3 (без свёртки `x/..`) с рисками и условными исходами (§4.4.1); строка §4.8 разделена по уровням; U2-Q6 (§4.9, §9.1); перекрёстные ссылки §7.1, §8.2, §9.2. Политика не выбрана | CE-QA44-CANCEL-BIDI 604 / `2d099515…0c67`, CE-QA44-CANCEL-ESC 606 / `1314b59e…6a8d` = `[QA44]`; при R0/R2 их формирование даёт U-POS-CC 597 / `8ef90e8a…46b4`; независимые U45-R-01…04 (§6.4) с hex исходного текста и свёртки |
| **P3-QA44-03** — 10 файлов, а не 9 | «девять файлов `docs/agents/v2/*.md`» ([#42 L106](https://github.com/iprus2026-tech/taxi-dashboard/blob/dcf9854687c7174ac55d4d8d94713cdd078533f0/docs/agents/v2/SPEC3-U1U3-DECISIONS.md#L106)) | «десять», явный перечень, правило выборки и отсечки, манифест; пометка «снимок, не инвариант» (§2.3 п.4); уточнена строка `[HIST-OBS]` (§0.1) | повторный подсчёт: 352 комментария до `2026-11-14T14:13:59Z`, манифест `b4ce7200…08a5` = `[QA44]`; 35/11, 39 блоков, 39/2/7 совпали |

QA44 отметил и соседний конфликт: экранирование `\` в G2 против запрета `\` в U2-A. Исходная версия его уже называла. Здесь он показан вектором U45-G2-04 и пунктом (3) обязательств интеграции (§4.5), но не разрешён. Прочие выводы QA44 (AC-1, AC-2, AC-4, AC-6…AC-10 PASS; U-1, U-3, первая диагностика §6.3) этой ревизией не затрагиваются.

### 11.2 Карта изменений относительно исходной версии #42

Исходник: `git show dcf9854687c7174ac55d4d8d94713cdd078533f0:docs/agents/v2/SPEC3-U1U3-DECISIONS.md` (95102 байт, `86df1eba…4959`). Воспроизвести побайтное сравнение:

```bash
git diff --no-index --stat <(git show dcf9854687c7174ac55d4d8d94713cdd078533f0:docs/agents/v2/SPEC3-U1U3-DECISIONS.md) <(git show HEAD:docs/agents/v2/SPEC3-U1U3-DECISIONS.md)
diff <(git show dcf9854687c7174ac55d4d8d94713cdd078533f0:docs/agents/v2/SPEC3-U1U3-DECISIONS.md) <(git show HEAD:docs/agents/v2/SPEC3-U1U3-DECISIONS.md)
```

Числовые итоги сравнения (строки и байты) приведены в HANDOFF/1, потому что документ не может содержать хэш самого себя.

| Место | Характер изменения | Причина |
|---|---|---|
| шапка | добавлен абзац «Ревизия #45» | необходимая ссылка на источник и находки |
| §0 таблица, раскрытие | строки задачи, SPEC, G0, CLAIM/ASSIGN, автора и ветки → #45; добавлены строки «Исходная версия» и «Основание переработки»; дополнено раскрытие независимости | происхождение ревизии (AC-1, AC-2) |
| §0.1 | `[GIT-OBS]` уточнён; добавлены `[GIT-DOC]`, `[QA44]`; уточнена отсечка `[HIST-OBS]` | источники P2-QA44-01 и P3-QA44-03 |
| §1 | новые предусловия #45; прежние 7 пунктов перенесены дословно в §1.1 | AC-1, AC-10 |
| §2.3 п.4 | «девять» → «десять»; добавлены перечень, способ выборки, манифест, «снимок» | **P3-QA44-03** |
| §4.1, §4.3 (U2-B), §4.4, §4.4.1 (новый), §4.8 | граница уровней, шаг (0), U2-R, условные исходы, разделённая строка | **P2-QA44-02** |
| §4.5, §4.7, §4.8 (строка совместимости) | G2 → G2-P/G2-I, таблица несовместимостей, исправленные строки, дополнительные векторы | **P2-QA44-01** |
| §4.9, §7.1 (U2-B), §8.2 (Q8), §9.1, §9.2, §9.3 | U2-Q2 расширен, U2-Q6 добавлен; перекрёстные ссылки | необходимые ссылки, все `PENDING` |
| §6.2 | одно примечание после таблицы; строки таблицы не менялись | AC-6 |
| §6.4 (новый) | отдельный сборщик QA44 и таблицы | AC-6 |
| §10, §10.1 | перечень выполненного дополнен для ревизии; заголовок §10.1 помечен как исторический | AC-9, AC-10 |
| §10.2, §11 (новые) | трассировка #45, эта карта, самопроверка, риски | AC-7, AC-9 |

**Без изменений:** §2.1, §2.2, §2.3 п.1–3, §3 (U-1) целиком, §4.2, §4.6, §5 (U-3) целиком, §6.1 (байты сборщика), строки §6.2, §6.3, §7.2, §7.3, §8.1, §8.3. Ссылки на источники и исторические SHA сохранены. Варианты U-1 и U-3 и незатронутые ветви U-2 (U2-A, U2-C1/C2, U2-N, параметры §4.5) не изменились по смыслу.

### 11.3 Самопроверка автора ревизии (не QA)

- Блок §6.1, извлечённый из этого файла, побайтно равен блоку #42. Он печатает те же 61 строку, и все 61 строки таблицы §6.2 совпадают с его выводом по длине и SHA-256. Семь сверяемых хэшей (U-POS-RO, CE-QA40-U1…U3, S3-BLK-01…03) воспроизводятся.
- Блок §6.4, извлечённый из этого файла, воспроизводит три хэша `CE-QA44-*` и печатает значения таблиц §6.4.
- Файл: UTF-8 NFC, LF, один завершающий LF, без CR, TAB, BOM; нет кодовых точек `Cc` (кроме LF) и `Cf`. Подробности — в HANDOFF/1.
- Base..HEAD: один коммит, один добавленный файл (проверяется перед HANDOFF).
- U1-Q1, U1-Q2, U2-Q1…U2-Q6, U3-Q1, OD-1…OD-7, Q8/B-07 — `PENDING / NO DEFAULT`. Новых `reason_code`, итогов, кодов выхода и меток `S3-C*` нет. `required: true` не навязывается. `UNRESOLVED`/5 не вводится.
- Эта самопроверка **не является** независимым QA PASS и не является выбором владельца.

### 11.4 Последствия для будущей работы (здесь ничего не меняется)

- **Действующий v1.** Если при U2-Q5(б) правило путей будет применяться к SPEC/1, выбор U2-Q2 (G1/G2-P/G2-I) и U2-Q6 станет частью поправки v1 §4.2 L150–L151 (§7.3). Отдельная задача: G0, независимый QA, G2.
- **v2 DRAFT `PROFILES.md`.** §2.1/§2.2 L79–L80 должны будут назвать ровно одну грамматику glob, без ссылки на версию Git, а при U2-B — и порядок проверки исходного текста (U2-R).
- **SPEC3 (предложение) и F4.** Строки P8 `allowed_paths`/`forbidden_paths` и `path` F4 L179 выравниваются с выбором. Метки остаются `S3-C02`/`S3-C03`. Уровень 1 (формирование) меток не имеет.
- **Будущая интеграция и QA.** Векторы §4.7 и §6.4 становятся тестами — новыми файлами, без изменения 30 замороженных фикстур. Для G2-P/G2-I тесты должны проверять записанный текст правила, а не поведение конкретной версии Git.

### 11.5 Риски и контраргументы

| Тема | Риск или контраргумент | Ответ записки |
|---|---|---|
| Неоднозначность glob | «Реализация Git на деле трактует `**` в pathspec как `*`, значит G2-P = G2-I» | Не проверялось (`NOT_RUN`). Даже если так, документированные контракты расходятся, а протокол не должен зависеть от недокументированного поведения. Именно поэтому любая G2 должна быть переписана в протокол целиком (§4.5) |
| Неоднозначность glob | «G2-I удобнее: так пишут `.gitignore`» | Удобство — довод для выбора владельца. Но G2-I меняет область шаблонов без `/` и вводит `!`/`#`. Это последствия, а не ошибки |
| Обход через `..` | «R2 достаточно: проверяющий увидит исходный текст Issue» | Это процедурная защита, она не входит в хэш (§4.4.1). Владелец вправе её принять, но риск раскрыт |
| Обход через `..` | «R1 дублирует проверку U2-A» | Да, набор символов проверяется дважды. Зато обещание отказа становится верным на обоих уровнях |
| Удаление запрещённых символов | при R0/R2 исходный текст с U+202E/ESC/U+200B/U+007F/U+2066 в удаляемом сегменте даёт те же байты, что и без него (§6.4) | показано векторами; выбор за владельцем (U2-Q6) |
| Unicode-нормализация | NFC применяется к тексту SPEC до правил пути; коллизии NFC/NFD и регистра — U2-N (§4.6) | ревизия это не меняет; U2-R касается только запрещённых категорий, а не NFC |
| Условная первая диагностика | метка `S3-C03 @ P8.allowed_paths` не различает, что внутри элемента сработало первым (`..` или символ) | так задано правилом первой диагностики `[S3-FAILED §3.6.1]`; ревизия его не меняет |
| Независимость | автор ревизии — та же роль, что и автор #42 | раскрыто (§0); нужен отдельный QA `codex-qa` |
