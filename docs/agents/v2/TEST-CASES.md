# v2 — Положительные и отрицательные проверочные случаи (документация)

> **Статус: `DRAFT / NOT ACTIVE`.** Это **описание** тестов для будущего валидатора, а не результат его работы. Валидатора v2 не существует. Код валидатора и его прогон — отдельная будущая задача (G0 #6831274083: `formal_validator_tests: separate_future_task`). Байтовые факты (длины и SHA-256 файлов `fixtures/`) пересчитаны автором и перечислены в [`fixtures/SHA256SUMS`](fixtures/SHA256SUMS). Ожидаемые исходы ниже выведены из текста контракта и **не** проверялись исполняемым кодом.

Покрывает: **AC-6** (обязательные категории: двойной CLAIM, истёкший lease, устаревший ASSIGN, самопроверка, отредактированный комментарий, HTTP 403, неверный digest, неверная база, неверная сериализация) и сценарии для AC-1–AC-5, AC-7, AC-8.

Столбцы исхода: `reason_code`; `result / execution_status / verification_status` для check; `report_validity / verdict`; статус задачи. Прочерк означает, что данные check не принимаются (отчёт или сообщение отвергнуты целиком).

Синтетический контекст для фикстур RESUME/2 описан в [RESUME2-FIXTURE.md §2](RESUME2-FIXTURE.md).

> **Ревизия `TAXI-AGENT-PROTOCOL-V2-F4-WIRE-01`** ([Issue #32](https://github.com/iprus2026-tech/taxi-dashboard/issues/32)). Добавлены §5 (векторы проводной формы F4) и §6 (матрица приёмки будущего валидатора). §1–§4 и все фикстуры не менялись. Матрица описывает ожидаемое поведение кода, которого нет; это не прогон.

---

## 1. Положительные случаи

| ID | Вход | Ожидаемый исход |
|---|---|---|
| POS-01 | [`resume2-canonical-pt12h.txt`](fixtures/resume2-canonical-pt12h.txt) в синтетическом контексте | принят; 757 байт; SHA-256 `55709c807e386edf0a58edf558801b00aa0856c3954123a938d5b1e5a49aaaa6`; синтаксически валиден, **но** в реальности требует существующих ссылок, свежего G0 и снимка refs |
| POS-02 | [`spec2-example-499.txt`](fixtures/spec2-example-499.txt) | 499 байт; `1af6f8e4148697a85f6970ac9fb98bf0bde97a543203a1d4a77cb5e8265fe559`; сочетание `READ_ONLY_EVIDENCE_QA/1` + `EVIDENCE_REVIEWER` + `FORBIDDEN` допустимо |
| POS-03 | [`refs-snapshot-example.txt`](fixtures/refs-snapshot-example.txt) | 78 байт; `032e90d80bbec3b3c125886c50216d059d306ebd9101fee1a7a1a728cdedd47c` |
| POS-04 | [`evidence-comment-lf.txt`](fixtures/evidence-comment-lf.txt) как декодированное `body` | `body_sha256` `e0f467e8…a0e8d` (79 байт); payload = [`evidence-payload.txt`](fixtures/evidence-payload.txt), `excerpt_sha256` `e49c81e2…78ee` (11 байт); `evidence_outcome: VERIFIED` при неизменных F1/F3 |
| POS-05 | [`evidence-comment-crlf.txt`](fixtures/evidence-comment-crlf.txt) как декодированное `body` | тот же payload и `excerpt_sha256`; **другой** `body_sha256` `1f0a005a…a240` (83 байта) |
| POS-06 | Read-only задача; между `before` и `after` `main` продвинулась fast-forward, `base_sha` и `source_sha` доступны | `STALE_SOURCE` **не** выставляется; старый и новый SHA записаны; отчёт может быть `VALID` |
| POS-07 | `CODE_CHANGE/1`: ветка `agent/<agent>/<id>` от `base_sha`, HANDOFF/2 с `head_sha`; HEAD = `head_sha` до и после QA; diff ⊆ `allowed_paths` | правила v1 §6 выполнены; check могут быть `PASS` |
| POS-08 | Обязательный check выполнен, доказательство пересчитано и показывает провал | `COMPLETED / VERIFIED / FAIL`; `VALID / FAIL`; задача → решение владельца или `in-progress` |
| POS-09 | Все обязательные check `COMPLETED / VERIFIED / PASS` с `evidence` и пересчитанными SHA-256; необязательных провалов нет | `VALID / PASS` |
| POS-10 | `updated_at` = `2026-11-12T16:55:03Z` | `2026-11-12T16:55:03.000Z` (остальные векторы — [EVIDENCE.md §6.5](EVIDENCE.md)) |

## 2. Обязательные отрицательные категории AC-6

| ID | Категория | Вход | reason_code | check | отчёт | задача |
|---|---|---|---|---|---|---|
| NEG-01 | двойной CLAIM | две сессии публикуют CLAIM/2 почти одновременно | — (решение координатора) | — | — | один ASSIGN/2 с `claim_ref` выбранной заявки; вторая сессия прав не получает и публикует `RELEASE/2` |
| NEG-02 | двойной CLAIM, работа невыбранной сессии | невыбранная сессия публикует HANDOFF/2 | `SESSION_STALE` | FAIL / HALTED / NOT_VERIFIED | STALE / VOID | `blocked` для её артефакта; назначение выбранной сессии не меняется |
| NEG-03 | двойной ASSIGN | координатор по ошибке опубликовал два ASSIGN/2 | `ASSIGN_FENCE_STALE` для старшего токена | — | — | действует только новейший; задача `blocked` до явного подтверждения исполнителя |
| NEG-04 | истёкший lease | исполнитель публикует артефакт после `lease_until` | `LEASE_EXPIRED` | FAIL / HALTED / NOT_VERIFIED | STALE / VOID | `blocked`; без автоматического продолжения |
| NEG-05 | истёкший lease, попытка продления | координатор публикует CHECKPOINT/2 или ASSIGN/2 с новым `lease_until` без нового назначения | `SCHEMA_INVALID` | — | — | lease не продлён; продолжение только через личный G0 + RESUME/2 (read-only) или новый ASSIGN/2 (code) |
| NEG-06 | устаревший ASSIGN | сессия со старым `assign_ref` пишет после нового RESUME/2 или REASSIGN | `ASSIGN_FENCE_STALE` | FAIL / HALTED / NOT_VERIFIED | STALE / VOID | `blocked` для артефакта |
| NEG-07 | устаревший ASSIGN в RESUME/2 | [`negative/sem-11-stale-assign-ref.txt`](fixtures/negative/sem-11-stale-assign-ref.txt): `previous_assign_ref: 12345669` вместо последнего токена `12345671` | `ASSIGN_FENCE_STALE` | — | — | RESUME/2 не публикуется |
| NEG-08 | самопроверка (код) | автор реализации публикует QA-REPORT/2 на свою задачу | `CONFLICT_OF_INTEREST` | — | INVALID / нет verdict | `blocked`; владелец назначает другого проверяющего |
| NEG-09 | самопроверка (дизайн) | автор DESIGN_NOTE публикует QA-REPORT/2 на свой дизайн | `CONFLICT_OF_INTEREST` | — | INVALID / нет verdict | `blocked` |
| NEG-10 | отредактированный комментарий-доказательство | `updated_at` или `body_sha256` в F3 ≠ F1 (payload может совпадать) | `STALE_EVIDENCE` | FAIL / HALTED / NOT_AVAILABLE | STALE / VOID | `blocked`; ссылку не использовать повторно |
| NEG-11 | отредактированное сообщение протокола | у ASSIGN/2 или HANDOFF/2 `updated_at` ≠ `created_at` | `SCHEMA_INVALID` | — | — | сообщение недействительно; нужно новое |
| NEG-12 | удалённый комментарий | ранее закреплённый комментарий отдаёт 404 | `EVIDENCE_DELETED` | FAIL / HALTED / NOT_AVAILABLE | STALE / VOID | `blocked` |
| NEG-13 | HTTP 403, вложение | вложение `user-attachments` отдаёт 403 при попытке скачать | `ATTACHMENT_403` | FAIL / COMPLETED / NOT_VERIFIED | VALID / FAIL | `handoff` для решения владельца; обход прав запрещён |
| NEG-14 | HTTP 403, API комментария | GET комментария отдаёт 403 | `EVIDENCE_NOT_ACCESSIBLE` | FAIL / COMPLETED / NOT_VERIFIED | VALID / FAIL | `handoff` |
| NEG-15 | неверный digest доказательства | заявленный `excerpt_sha256` ≠ пересчитанному; комментарий не менялся (F1 = F3) | — (провал подтверждён) | FAIL / COMPLETED / VERIFIED | VALID / FAIL | возврат исполнителю |
| NEG-16 | неверный digest спецификации | HANDOFF/2 или ASSIGN/2 указывает `spec_sha256` ≠ пересчёту текущего Issue или ≠ G0 | `UNAPPROVED_BASE` | — | INVALID / нет verdict | `blocked` (нужны новые SPEC + G0) |
| NEG-17 | неверный digest в RESUME/2 | [`negative/sem-10-wrong-spec-digest.txt`](fixtures/negative/sem-10-wrong-spec-digest.txt): исторический хэш 480-байтного вектора `02e19f6d…` | `UNAPPROVED_BASE` | — | — | RESUME/2 не публикуется |
| NEG-18 | неверная база | [`negative/sem-09-incorrect-base.txt`](fixtures/negative/sem-09-incorrect-base.txt): `base_sha` = `9297081…` ≠ базе SPEC/2 | `UNAPPROVED_BASE` | — | — | RESUME/2 не публикуется |
| NEG-19 | неверная база, ancestry | `base_sha` не предок `origin/<target_branch>` | `UNAPPROVED_BASE` при ASSIGN; `STALE_SOURCE` в ходе проверки | — / FAIL / HALTED / NOT_AVAILABLE | INVALID или STALE / VOID | `blocked` |
| NEG-20 | неверная база, цель | `target_branch` в SPEC/2 ≠ строке в `note` G0, или строки нет | `UNAPPROVED_BASE` | — | — | без ASSIGN/RESUME |
| NEG-21 | неверная сериализация | любая фикстура `negative/ser-*` (§3) | `CANONICALIZATION_ERROR` или `SCHEMA_INVALID` | — | — | сообщение отвергнуто |

## 3. Отрицательные фикстуры RESUME/2

Каждый файл получен из [`resume2-canonical-pt12h.txt`](fixtures/resume2-canonical-pt12h.txt) одной описанной мутацией. Длины и SHA-256 — в [`fixtures/SHA256SUMS`](fixtures/SHA256SUMS).

### 3.1 Сериализация (`ser-*`)

| Файл | Мутация | Байт | Ожидание |
|---|---|---|---|
| `ser-01-crlf.txt` | все LF → CRLF | 781 | `CANONICALIZATION_ERROR` |
| `ser-02-bom.txt` | BOM `EF BB BF` в начале | 760 | `CANONICALIZATION_ERROR` |
| `ser-03-no-terminal-lf.txt` | удалён завершающий LF | 756 | `CANONICALIZATION_ERROR` |
| `ser-04-extra-blank-line.txt` | лишний LF в конце (пустая строка) | 758 | `CANONICALIZATION_ERROR` |
| `ser-05-swapped-key-order.txt` | строки `claim_ref` и `previous_assign_ref` переставлены | 757 | `SCHEMA_INVALID` (порядок ключей; длина та же, хэш другой) |
| `ser-06-missing-field.txt` | удалена строка `refs_snapshot_sha256` | 670 | `SCHEMA_INVALID` |
| `ser-07-extra-field.txt` | добавлена `note: extra` перед `lease_until` | 769 | `SCHEMA_INVALID` |
| `ser-08-duplicate-key.txt` | строка `session` повторена | 786 | `SCHEMA_INVALID` |
| `ser-09-missing-title-line.txt` | удалена первая строка `agent-msg` | 747 | `SCHEMA_INVALID` |
| `ser-10-uppercase-hex.txt` | `issue_spec_sha256` в верхнем регистре | 757 | `SCHEMA_INVALID` |
| `ser-11-trailing-space.txt` | пробел в конце строки `task` | 758 | `CANONICALIZATION_ERROR` |
| `ser-12-tab-separator.txt` | после `task:` табуляция вместо пробела | 757 | `CANONICALIZATION_ERROR` |
| `ser-13-ts-seconds.txt` | `ts: 2026-11-12T15:00:00Z` (без `.sss`) | 753 | `SCHEMA_INVALID` (поля времени v2 требуют `.sssZ`) |

### 3.2 Смысловые (`sem-*`, синтаксис формально похож на верный)

| Файл | Мутация | Ожидание |
|---|---|---|
| `sem-01-unbound-session.txt` | `session: synth-attacker-9999`; `claim_ref` и G0 прежние | `AUTH_ATTESTATION_UNVERIFIED`: сессия не совпадает с `new_session` G0 и с CLAIM/2. Координатор отвергает до публикации, токена нет (N1 эррата) |
| `sem-02-mixed-triple.txt` | `last_artifact_ref: 12345673`, остальные два поля `none` | `SCHEMA_INVALID` (смешанная тройка, N2 эррата) |
| `sem-03-lease-24h-erratum.txt` | `lease_until` = `ts + 24 ч` (вариант эррата, SHA-256 `515c1d2d…3491`) | `SCHEMA_INVALID`: нарушена политика PT12H |
| `sem-04-lease-not-after-ts.txt` | `lease_until` = `ts` | `SCHEMA_INVALID` |
| `sem-05-branch-not-none.txt` | `branch: agent/deepseek-qa/taxi-protocol-example-01` | `SCHEMA_INVALID`; при попытке создать ref — `SCOPE_VIOLATION` |
| `sem-06-self-resume-agent.txt` | `agent: deepseek-qa` (возобновление самим агентом) | `SCHEMA_INVALID`: `agent` должен быть `gpt`, самостоятельный RESUME запрещён |
| `sem-07-v1-crossover.txt` | `v: 1` | `SCHEMA_INVALID`: v1 и v2 не смешиваются |
| `sem-08-coord-eq-session.txt` | `coordinator_session` = `session` | `SCHEMA_INVALID` |
| `sem-09-incorrect-base.txt` | см. NEG-18 | `UNAPPROVED_BASE` |
| `sem-10-wrong-spec-digest.txt` | см. NEG-17 | `UNAPPROVED_BASE` |
| `sem-11-stale-assign-ref.txt` | см. NEG-07 | `ASSIGN_FENCE_STALE` |

## 4. Прочие отрицательные случаи

| ID | AC | Вход | Ожидание |
|---|---|---|---|
| NEG-AC1-01 | AC-1 | Read-only задача пытается использовать `git_commit:create` или писать файл | SPEC/2 с таким токеном → `SCHEMA_INVALID`; фактическая запись → `SCOPE_VIOLATION`, VALID / VOID, `blocked` |
| NEG-AC1-02 | AC-1 | Сессия, назначенная на code-задачу, ссылается на свои права в read-only задаче | права не переносятся; артефакт в read-only задаче без собственного назначения → `SESSION_STALE` |
| NEG-AC1-03 | AC-1 | Агент меняет `work_profile` или `task_role` после G0 | хэш SPEC/2 изменился → `UNAPPROVED_BASE`, `blocked` |
| NEG-AC3-01 | AC-3 | `CODE_CHANGE/1` без реальной ветки ссылается на правила read-only | `UNAPPROVED_BASE`, `blocked` |
| NEG-AC3-02 | AC-3 | Read-only задача: в снимке `after` появился новый ref; независимое доказательство записи этой сессией есть | `SCOPE_VIOLATION`, VALID / VOID |
| NEG-AC3-03 | AC-3 | Read-only задача: изменился посторонний ref, доказательства авторства нет | `REF_DRIFT_UNEXPLAINED`, STALE / VOID; не `SCOPE_VIOLATION` |
| NEG-AC3-04 | AC-3 | `source_sha` больше не читается | `STALE_SOURCE`, STALE / VOID |
| NEG-AC4-01 | AC-4 | Конверт внутри Markdown-fence или с текстом до BEGIN | `CANONICALIZATION_ERROR` |
| NEG-AC4-02 | AC-4 | Вложенная строка `BEGIN-EVIDENCE-TEXT/…` в payload | `CANONICALIZATION_ERROR` |
| NEG-AC4-03 | AC-4 | Одиночный CR или BOM в `body` | `CANONICALIZATION_ERROR` |
| NEG-AC4-04 | AC-4 | Payload состоит только из `\n` | `CANONICALIZATION_ERROR` |
| NEG-AC4-05 | AC-4 | Digest доказательства известен только со слов исполнителя | `provenance: AGENT_REPORTED`, `NOT_VERIFIED`; обязательный check не PASS |
| NEG-AC5-01 | AC-5 | check `result: PASS`, `evidence: null` для check, где нужно доказательство | нарушен I1 → `SCHEMA_INVALID`, INVALID / нет verdict |
| NEG-AC5-02 | AC-5 | check `PASS` с `provenance: INFERRED` или `RELAYED_OWNER_STATEMENT` | нарушен I6 → `SCHEMA_INVALID` |
| NEG-AC5-03 | AC-5 | Обязательный check `NOT_RUN` без `reason` | `SCHEMA_INVALID` |
| NEG-AC5-04 | AC-5 | Отчёт `{verdict: PASS}` без обязательных полей | внешний валидатор: INVALID, принятого verdict нет |
| NEG-AC5-05 | AC-5 | Обязательный check не начинался | `UNRUN_REQUIRED`: NOT_RUN / NOT_RUN / NOT_AVAILABLE; VALID / FAIL |
| NEG-AC5-06 | AC-5 | `report_validity: STALE` вместе с `verdict: PASS` | недопустимая пара → `SCHEMA_INVALID` |
| NEG-AC7-01 | AC-7 | RESUME/2 без нового личного G0 для этого события (переиспользуется прежний G0) | `AUTH_ATTESTATION_UNVERIFIED`; RESUME/2 не публикуется |
| NEG-AC7-02 | AC-7 | G0 без `approve_one_RESUME/2: true` или без привязки lease `resume2_lease_duration: PT12H` | G0 недостаточен; `AUTH_ATTESTATION_UNVERIFIED` |
| NEG-AC7-03 | AC-7 | Блок OWNER-DECISION пришёл в relay от агента | недействителен (v1 §5.6); `AUTH_ATTESTATION_UNVERIFIED` |
| NEG-AC7-04 | AC-7 | `updated_at` = `2026-11-12T16:55:03.123Z` или `+00:00` | отвергается, не округляется; ссылка `NOT_VERIFIED` |
| NEG-AC7-05 | AC-7 | Отчёт называет `body_sha256` «сырыми байтами GitHub» | нарушена граница провенанса [EVIDENCE.md §3](EVIDENCE.md); формулировка недопустима; check не может опираться на неё как на аттестацию хранилища |
| NEG-AC8-01 | AC-8 | v1 CLAIM, ASSIGN или исторический NONWIRE-сеанс выдаётся за основание RESUME/2 | `SCHEMA_INVALID`; v1 → v2 запрещено |
| NEG-AC8-02 | AC-8 | Сообщение v2 публикуется по реальной задаче до активации v2 | недействительно: v2 не активирован ([README.md §2](README.md)); действует только v1 |
| NEG-AC8-03 | AC-8 | Общий логин `iprus2026-tech` принимается за доказательство личности владельца | недопустимо (v1 §0.1); `AUTH_ATTESTATION_UNVERIFIED` |

## 5. Векторы проводной формы F4

Нормативный текст векторов и способ их воспроизведения — [F4-WIRE.md §13–§15](F4-WIRE.md). Это документарные синтетические примеры, а не файлы `fixtures/`, не реальные сообщения и не прогон.

| Группа | ID | Что показывает |
|---|---|---|
| положительные | POS-F4-01 | `HANDOFF/2`, `READ_ONLY_EVIDENCE_QA/1`: `branch: none`, без `head_sha`, `changed_files.count: 0`, `source_checks` до и после, `EvidenceRef/2` типа `github_issue_text` |
| положительные | POS-F4-02 | `QA-REPORT/2` `VALID` / `PASS`: check D01 с пересчитанным доказательством |
| положительные | POS-F4-03 | `HANDOFF/2`, `CODE_CHANGE/1`: `branch`, `head_sha`, `changed_files` с permalink, `git_blob` |
| положительные | POS-F4-04 | `QA-REPORT/2` `VALID` / `FAIL`: пустое `comment_updated_at` → D06 на уровне check, отчёт **не** `INVALID` |
| байты | NEG-F4-01..07 | CRLF, BOM, нет завершающего LF, лишний LF, TAB, не NFC, некорректный UTF-8 |
| строки и ключи | NEG-F4-08..11, 19, 20, 24 | повтор, перестановка, недостающий элемент списка, ведущий ноль индекса, отсутствующий `verdict`, `head_sha` в read-only, двойной пробел |
| значения | NEG-F4-12..15, 17, 18, 21, 23 | верхний регистр hex, превышение длины, версия схемы, время без `.sss`, код парсера в `checks[]`, пустое значение, непустой `changed_files` read-only, адрес на ветку |
| инварианты | NEG-F4-16, 22 | неизвестный тип ссылки при PASS (I10), `required: false` |
| обёртка | W-NEG-01..04 | текст до fence, два блока, нет закрывающей строки, CRLF в теле |
| метаданные и привязка | M-NEG-01..02, X-NEG-01..08 | отредактированный комментарий, неверное время GitHub, выдуманные ссылки, чужая сессия, сдвиг HEAD, истёкший lease, самопроверка, время позже публикации, подделанный хэш файла |

## 6. Матрица приёмки будущего валидатора

Матрица связывает каждый случай этого файла и векторы F4 с детерминированным результатом по контракту [F4-WIRE.md §16](F4-WIRE.md). Валидатора нет: всё ниже — ожидания, выведенные из текста.

Обозначения:

- **Результат и выход** — по F4-WIRE.md §16.3: `ACCEPT` (0), `REJECT` (1), `ACCEPT_STRUCTURAL` (3; уровни M или X не прогонялись). «Отчёт: форма ACCEPT» означает, что отчёт, верно записавший описанную ситуацию, проходит форму, а его итог (`report_validity` / `verdict`) указан рядом.
- **Ошибка** — диагностический код `F4-*` для `HANDOFF/2` и `QA-REPORT/2`. Для FLAT-сообщений (`RESUME/2` и другие) действуют правила [LIFECYCLE.md §1, §6.3](LIFECYCLE.md); F4 их диагностические коды не определяет, и в столбце стоит `FLAT` с ближайшим аналогом F4 для справки. `PROC` — решение координатора, а не проверка байтов сообщения.
- **Вне F4.** Контракт `F4-RESULT/1` и коды выхода (F4-WIRE.md §16.3) относятся только к `HANDOFF/2` и `QA-REPORT/2`. Для FLAT-сообщений, SPEC/2, снимка refs и нормализации времени матрица задаёт только ожидаемую классификацию («принят» или «отвергнут» и `reason_code`), а интерфейс и коды выхода определит SPEC задачи валидатора (F4-WIRE.md §16.5 п.1). В таких строках код выхода не указан.
- **Провенанс ожидания** — словарь [QA-REPORT.md §2](QA-REPORT.md): исход выведен из текста (`INFERRED`), длины и SHA-256 пересчитаны автором (`AGENT_REPORTED` для проверяющего, пока он не пересчитает их сам).
- **Воспроизведение:** `OFFLINE` — только байты из `fixtures/` или F4-WIRE.md; `CONTEXT` — нужен синтетический контекст (RESUME2-FIXTURE.md §2 или F4-WIRE.md §13) с записанными ответами API и Git; сеть в тестах не используется.

### 6.1 Положительные случаи и векторы F4

| ID | Объект | Результат / выход | Ошибка | `reason_code` → строка | Провенанс | Воспроизведение |
|---|---|---|---|---|---|---|
| POS-01 | RESUME/2, фикстура 757 байт | вне F4: принят (синтаксис офлайн; ссылки — в контексте RESUME2-FIXTURE.md §2) | `FLAT` | `none` | `INFERRED`; байты `AGENT_REPORTED` | `OFFLINE`, `CONTEXT` |
| POS-02 | SPEC/2, 499 байт | вне F4: принята (каноническая форма и сочетание профиля) | — | `none` | то же | `OFFLINE` |
| POS-03 | снимок refs, 78 байт | вне F4: принят | — | `none` | то же | `OFFLINE` |
| POS-04, POS-05 | тело доказательства LF и CRLF | E1–E8: `VERIFIED`; один payload, разные `body_sha256` | — | `none` → D01 | то же | `CONTEXT` |
| POS-06 | read-only, fast-forward цели | отчёт: форма `ACCEPT`; `after.s5: TARGET_FAST_FORWARD`, `STALE_SOURCE` не выставляется | — | `none` | `INFERRED` | `CONTEXT` |
| POS-07 | `HANDOFF/2` `CODE_CHANGE/1` (= POS-F4-03) | `ACCEPT_STRUCTURAL` / 3; `ACCEPT` / 0 в контексте F4-WIRE.md §13 | — | `none` | то же | `OFFLINE`, `CONTEXT` |
| POS-08 | обязательный check COMPLETED / VERIFIED / FAIL | отчёт: форма `ACCEPT`; `VALID` / `FAIL` (§9.3, строка D02) | — | `none` → D02 | `INFERRED` | `OFFLINE` |
| POS-09 | все обязательные check PASS (= POS-F4-02) | `ACCEPT_STRUCTURAL` / 3; `ACCEPT` / 0 в контексте; `VALID` / `PASS` | — | `none` → D01 | то же | `OFFLINE`, `CONTEXT` |
| POS-10 | `updated_at` `2026-11-12T16:55:03Z` | вне F4: нормализация в `2026-11-12T16:55:03.000Z` (используется уровнями M и X) | — | `none` | `INFERRED` | `OFFLINE` |
| POS-F4-01 | `HANDOFF/2` read-only | `ACCEPT_STRUCTURAL` / 3; `ACCEPT` / 0 в контексте | — | `none` | `INFERRED`; байты `AGENT_REPORTED` | `OFFLINE`, `CONTEXT` |
| POS-F4-02 | `QA-REPORT/2` `VALID` / `PASS` | `ACCEPT_STRUCTURAL` / 3; `ACCEPT` / 0 в контексте | — | `none` | то же | `OFFLINE`, `CONTEXT` |
| POS-F4-03 | `HANDOFF/2` `CODE_CHANGE/1` | `ACCEPT_STRUCTURAL` / 3; `ACCEPT` / 0 в контексте | — | `none` | то же | `OFFLINE`, `CONTEXT` |
| POS-F4-04 | `QA-REPORT/2` `VALID` / `FAIL` | `ACCEPT_STRUCTURAL` / 3; check D06 на уровне доказательства | — | check: `EVIDENCE_REF_INVALID` → D06 | то же | `OFFLINE` |
| BODY-POS-F4-02, BODY-POS-F4-02-ANNEX | тело комментария | обёртка принята; `canonical_sha256` = POS-F4-02 | — | `none` | то же | `OFFLINE` |

### 6.2 Обязательные отрицательные категории (§2)

| ID | Результат / выход | Ошибка | `reason_code` → строка / итог | Воспроизведение |
|---|---|---|---|---|
| NEG-01 | `PROC`: один ASSIGN/2; артефакты невыбранной сессии → как NEG-02 | — | — | `CONTEXT` |
| NEG-02 | `REJECT` / 1 | `F4-X12` | `SESSION_STALE`; отчёт по такому `HANDOFF/2` `STALE` / `VOID` | `CONTEXT` |
| NEG-03 | `PROC`; артефакты со старшим токеном → `REJECT` / 1 | `F4-X11` | `ASSIGN_FENCE_STALE` | `CONTEXT` |
| NEG-04 | `REJECT` / 1 | `F4-X13` | `LEASE_EXPIRED`; `STALE` / `VOID` | `CONTEXT` |
| NEG-05 | вне F4: отвергнут | `FLAT` | `SCHEMA_INVALID` (LIFECYCLE.md §5.1 п.1) | `CONTEXT` |
| NEG-06 | `REJECT` / 1 | `F4-X11` | `ASSIGN_FENCE_STALE`; `STALE` / `VOID` | `CONTEXT` |
| NEG-07 | вне F4: отвергнут | `FLAT` | `ASSIGN_FENCE_STALE` | `CONTEXT` |
| NEG-08, NEG-09 | `REJECT` / 1 | `F4-X10` | `CONFLICT_OF_INTEREST`; `INVALID`, verdict отсутствует | `CONTEXT` |
| NEG-10 | E4 или E7: `STALE` / `STALE_EVIDENCE`; отчёт: форма `ACCEPT`, `STALE` / `VOID` (§9.4 R2). Отчёт с `VERIFIED` для такой ссылки → `REJECT` / 1 | `F4-X09` (только при неверной записи) | `STALE_EVIDENCE` → D08 | `CONTEXT` |
| NEG-11 | `REJECT` / 1 | `F4-M02` для `HANDOFF/2`; `FLAT` для `ASSIGN/2`; как основание — `F4-X03` | `SCHEMA_INVALID` → D12 | `CONTEXT` |
| NEG-12 | E2: `STALE` / `EVIDENCE_DELETED`; отчёт: форма `ACCEPT`, `STALE` / `VOID` | `F4-X09` (только при неверной записи) | `EVIDENCE_DELETED` → D09 | `CONTEXT` |
| NEG-13 | E2: `NOT_VERIFIED`; отчёт: форма `ACCEPT`, `VALID` / `FAIL` | `F4-X09` (только при неверной записи) | `ATTACHMENT_403` → D03 | `CONTEXT` |
| NEG-14 | то же | то же | `EVIDENCE_NOT_ACCESSIBLE` → D03 | `CONTEXT` |
| NEG-15 | E6: `VERIFIED`, check FAIL / COMPLETED / VERIFIED; отчёт: форма `ACCEPT`, `VALID` / `FAIL` | `F4-X09` (только при неверной записи) | `none` → D02 | `CONTEXT` |
| NEG-16 | `REJECT` / 1 | `F4-X04` (`HANDOFF/2`), `F4-X08` (`QA-REPORT/2`) | `UNAPPROVED_BASE`; `INVALID` | `CONTEXT` |
| NEG-17, NEG-18 | вне F4: отвергнут | `FLAT` | `UNAPPROVED_BASE` | `CONTEXT` |
| NEG-19 | `PROC`: при ASSIGN координатор не выдаёт назначение; в ходе проверки `after.s3: STALE_SOURCE` → отчёт: форма `ACCEPT`, `STALE` / `VOID` | `PROC` / — | `UNAPPROVED_BASE` / `STALE_SOURCE` | `CONTEXT` |
| NEG-20 | `REJECT` / 1 | `F4-X04` | `UNAPPROVED_BASE` | `CONTEXT` |
| NEG-21 | вне F4: отвергнут, см. §6.3 | `FLAT` | `CANONICALIZATION_ERROR` или `SCHEMA_INVALID` | `OFFLINE` |

### 6.3 Фикстуры RESUME/2 (§3)

Все — вне F4 (FLAT): ожидается «отвергнут» с указанным `reason_code`; код выхода определит задача валидатора. Провенанс: `INFERRED`, байты `AGENT_REPORTED` (`fixtures/SHA256SUMS`).

| ID | Ошибка (аналог F4 — справочно) | `reason_code` | Воспроизведение |
|---|---|---|---|
| ser-01 | `FLAT` (`F4-B04`) | `CANONICALIZATION_ERROR` | `OFFLINE` |
| ser-02 | `FLAT` (`F4-B03`) | `CANONICALIZATION_ERROR` | `OFFLINE` |
| ser-03 | `FLAT` (`F4-B08`) | `CANONICALIZATION_ERROR` | `OFFLINE` |
| ser-04 | `FLAT` (`F4-B09`) | `CANONICALIZATION_ERROR` | `OFFLINE` |
| ser-05 | `FLAT` (`F4-K03`) | `SCHEMA_INVALID` | `OFFLINE` |
| ser-06 | `FLAT` (`F4-K04`) | `SCHEMA_INVALID` | `OFFLINE` |
| ser-07 | `FLAT` (`F4-K02`) | `SCHEMA_INVALID` | `OFFLINE` |
| ser-08 | `FLAT` (`F4-K01`) | `SCHEMA_INVALID` | `OFFLINE` |
| ser-09 | `FLAT` (`F4-L01`) | `SCHEMA_INVALID` | `OFFLINE` |
| ser-10 | `FLAT` (`F4-S03`) | `SCHEMA_INVALID` | `OFFLINE` |
| ser-11 | `FLAT` (`F4-B10`) | `CANONICALIZATION_ERROR` | `OFFLINE` |
| ser-12 | `FLAT` (`F4-B05`) | `CANONICALIZATION_ERROR` | `OFFLINE` |
| ser-13 | `FLAT` (`F4-S05`) | `SCHEMA_INVALID` | `OFFLINE` |
| sem-01 | `FLAT` (сессия ≠ `new_session` G0 и CLAIM/2) | `AUTH_ATTESTATION_UNVERIFIED` | `CONTEXT` |
| sem-02, sem-04, sem-05, sem-06, sem-07, sem-08 | `FLAT` | `SCHEMA_INVALID` | `OFFLINE` |
| sem-03 | `FLAT` (`lease_until` ≠ `ts` + PT12H) | `SCHEMA_INVALID` | `OFFLINE` |
| sem-09 | `FLAT` (`F4-X05`) | `UNAPPROVED_BASE` | `CONTEXT` |
| sem-10 | `FLAT` (`F4-X04`) | `UNAPPROVED_BASE` | `CONTEXT` |
| sem-11 | `FLAT` (`F4-X11`) | `ASSIGN_FENCE_STALE` | `CONTEXT` |

### 6.4 Прочие отрицательные случаи (§4, EVIDENCE.md §2.3–§2.5, QA-REPORT.md §7)

| ID | Результат / выход | Ошибка | `reason_code` → строка / итог | Воспроизведение |
|---|---|---|---|---|
| NEG-AC1-01 | вне F4: SPEC/2 отвергнута; фактическая запись — содержание QA: `SCOPE_VIOLATION`, `VALID` / `VOID` | — | `SCHEMA_INVALID` / `SCOPE_VIOLATION` | `OFFLINE` / `CONTEXT` |
| NEG-AC1-02 | `REJECT` / 1 | `F4-X12` | `SESSION_STALE` | `CONTEXT` |
| NEG-AC1-03 | `REJECT` / 1 | `F4-X04` | `UNAPPROVED_BASE` | `CONTEXT` |
| NEG-AC3-01 | `REJECT` / 1: `branch: none`, другое имя или несуществующая ветка при `CODE_CHANGE/1` | `F4-X05` | `UNAPPROVED_BASE` | `CONTEXT` |
| NEG-AC3-02 | отчёт: форма `ACCEPT`, `after.s5: SCOPE_VIOLATION` → `VALID` / `VOID` (R3) | — | `SCOPE_VIOLATION` | `CONTEXT` |
| NEG-AC3-03 | отчёт: форма `ACCEPT`, `after.s5: REF_DRIFT_UNEXPLAINED` → `STALE` / `VOID` (R2) | — | `REF_DRIFT_UNEXPLAINED` | `CONTEXT` |
| NEG-AC3-04 | отчёт: форма `ACCEPT`, `after.s4: STALE_SOURCE` → `STALE` / `VOID` | — | `STALE_SOURCE` | `CONTEXT` |
| NEG-AC4-01..04 | E5: `REJECTED`; отчёт: форма `ACCEPT`, `VALID` / `FAIL` | `F4-X09` (только при неверной записи) | `CANONICALIZATION_ERROR` (доказательство) → D07 | `CONTEXT` |
| NEG-AC4-05 | `NOT_VERIFIED`; отчёт: форма `ACCEPT`, `VALID` / `FAIL` | то же | `PRIMARY_SOURCE_UNKNOWN` → D04 | `CONTEXT` |
| NEG-AC5-01 | `REJECT` / 1 | `F4-Q04` | `SCHEMA_INVALID` → D15 | `OFFLINE` |
| NEG-AC5-02 | `REJECT` / 1 | `F4-Q06` (PASS требует `VERIFIED`, а `INFERRED` и `RELAYED_OWNER_STATEMENT` его запрещают; I6) | `SCHEMA_INVALID` → D15 | `OFFLINE` |
| NEG-AC5-03 | `REJECT` / 1 | `F4-Q05` | `SCHEMA_INVALID` → D15 | `OFFLINE` |
| NEG-AC5-04 | `REJECT` / 1 | `F4-L01` (нет строки `agent-msg`) или `F4-K04` | `SCHEMA_INVALID` → D15 | `OFFLINE` |
| NEG-AC5-05 | отчёт: форма `ACCEPT`, `VALID` / `FAIL` (строка `UNRUN_REQUIRED` §9.3) | — | `UNRUN_REQUIRED` | `OFFLINE` |
| NEG-AC5-06 | `REJECT` / 1 | `F4-Q08` | `SCHEMA_INVALID` → D15 | `OFFLINE` |
| NEG-AC7-01..03 | RESUME/2 вне F4: отвергнут; для оснований `HANDOFF/2` и `QA-REPORT/2` — `REJECT` / 1 | `FLAT` / `F4-X02` | `AUTH_ATTESTATION_UNVERIFIED` | `CONTEXT` |
| NEG-AC7-04 | для доказательства E3: `NOT_VERIFIED` / `EVIDENCE_TS_UNVERIFIABLE` (D05); для сообщения `F4-M01` → `REJECT` / 1 | `F4-M01` | D05 / D13 | `CONTEXT` |
| NEG-AC7-05 | вне валидатора: формулировка текста проверяется проверяющим | — | — | — |
| NEG-AC8-01 | `REJECT` / 1 для `HANDOFF/2` и `QA-REPORT/2`; FLAT вне F4: отвергнут | `F4-S01` (`v: 1`) / `FLAT` | `SCHEMA_INVALID` | `OFFLINE` |
| NEG-AC8-02 | вне формы: `ACCEPT` валидатора до активации v2 не делает сообщение действительным ([README.md §1](README.md)) | — | — | — |
| NEG-AC8-03 | `REJECT` / 1 | `F4-X02` | `AUTH_ATTESTATION_UNVERIFIED` | `CONTEXT` |
| NEG-F1-01, NEG-F1-02 | `REJECT` / 1, если пара нарушена; согласованная, но ложная пара — `F4-X09` | `F4-Q04` / `F4-X09` | `SCHEMA_INVALID` → D15 | `OFFLINE` / `CONTEXT` |
| NEG-F1-03 | `REJECT` / 1: `INVALID` не выводится из содержания | `F4-Q08` | `SCHEMA_INVALID` → D15 | `OFFLINE` |
| NEG-F1-04, NEG-F1-06, NEG-F1-07, NEG-F1-08 | `REJECT` / 1 | `F4-Q04`; если ссылка не проходит E1 — раньше `F4-Q03` | `SCHEMA_INVALID` → D15 | `OFFLINE` |
| NEG-F1-05 | неверная запись `INVALID` → `REJECT` / 1 (`F4-Q08`); правильная `VALID` / `FAIL` → форма `ACCEPT` | `F4-Q08` | D07 в check; отчёт `VALID` / `FAIL` | `OFFLINE` |
| NEG-F2-01, NEG-F2-04 | `REJECT` / 1 | `F4-Q03` (некорректный `comment_updated_at` не проходит E1, а check записан с `SCHEMA_INVALID` вместо `EVIDENCE_REF_INVALID`) | `SCHEMA_INVALID` → D15 | `OFFLINE` |
| NEG-F2-02 | `REJECT` / 1, если отчёт записал `VERIFIED` для округлённого значения | `F4-X09` | `SCHEMA_INVALID`; правильно D05 | `CONTEXT` |
| NEG-F2-03 | `REJECT` / 1 | `F4-S05` в основании → `F4-X03` | `SCHEMA_INVALID` → D11 | `CONTEXT` |
| NEG-F2-05 | `REJECT` / 1 (= NEG-F4-15) | `F4-S05` | `SCHEMA_INVALID` → D15 | `OFFLINE` |
| NEG-F2-06 | `REJECT` / 1 | `F4-X03` (основание отредактировано) | `SCHEMA_INVALID` → D12 | `CONTEXT` |
| NEG-F2-07 | `REJECT` / 1 | `F4-Q02` (необязательных AC в SPEC/2 нет); по смыслу QA-REPORT.md §6 п.6 — `F4-Q08` | `SCHEMA_INVALID` → D15 | `OFFLINE` |
| NEG-D14-01 | форма проходит `F4-Q04` (строка D02); ошибку выявляет повторная оценка E5 по телу комментария из контекста → `REJECT` / 1 | `F4-X09` | `SCHEMA_INVALID` → D15 (I10); правильно D14 через E5 = D07 | `CONTEXT` |

### 6.5 Отрицательные векторы F4

Все `REJECT` / 1. Ожидаемый код, строка и `reason_code` — в [F4-WIRE.md §15](F4-WIRE.md). Провенанс: `INFERRED`, байты `AGENT_REPORTED`.

| ID | Ошибка | `reason_code` → строка | Воспроизведение |
|---|---|---|---|
| NEG-F4-01..07 | `F4-B04`, `F4-B03`, `F4-B08`, `F4-B09`, `F4-B05`, `F4-B07`, `F4-B02` | `CANONICALIZATION_ERROR` → D16 | `OFFLINE` |
| NEG-F4-08..15 | `F4-K01`, `F4-K03`, `F4-K04`, `F4-L03`, `F4-S03`, `F4-S08`, `F4-S01`, `F4-S05` | `SCHEMA_INVALID` → D15 | `OFFLINE` |
| NEG-F4-16 | `F4-Q03` | `SCHEMA_INVALID` → D15 | `OFFLINE` |
| NEG-F4-17, 18, 19 | `F4-S02`, `F4-S08`, `F4-K04` | `SCHEMA_INVALID` → D15 | `OFFLINE` |
| NEG-F4-20, 21, 23 | `F4-K02`, `F4-S10`, `F4-S09` | `SCHEMA_INVALID`; как основание → D11 | `OFFLINE` |
| NEG-F4-22, 24 | `F4-Q02`, `F4-L02` | `SCHEMA_INVALID` → D15 | `OFFLINE` |
| W-NEG-01, 04 | `F4-W01` | `CANONICALIZATION_ERROR` → D16 | `OFFLINE` |
| W-NEG-02 | `F4-W04` | `CANONICALIZATION_ERROR` → D16 | `OFFLINE` |
| W-NEG-03 | `F4-W03` | `CANONICALIZATION_ERROR` → D16 | `OFFLINE` |
| M-NEG-01 | `F4-M02`; для отчёта — `F4-X03` | `SCHEMA_INVALID` → D12 | `CONTEXT` |
| M-NEG-02 | `F4-M01` | `SCHEMA_INVALID`, итог как D15 | `CONTEXT` |
| X-NEG-01, 02 | `F4-X01` | `AUTH_ATTESTATION_UNVERIFIED` | `CONTEXT` |
| X-NEG-03 | `F4-X12` | `SESSION_STALE` | `CONTEXT` |
| X-NEG-04 | `F4-X14` | `STALE_SOURCE` | `CONTEXT` |
| X-NEG-05 | `F4-X13` | `LEASE_EXPIRED` | `CONTEXT` |
| X-NEG-06 | `F4-X10` | `CONFLICT_OF_INTEREST` | `CONTEXT` |
| X-NEG-07 | `F4-X06` | `SCHEMA_INVALID` → D11 | `CONTEXT` |
| X-NEG-08 | `ACCEPT` для формы `HANDOFF/2`; проверяющий записывает D02 | — | `CONTEXT` |
