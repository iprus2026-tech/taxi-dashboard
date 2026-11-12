# v2 — Положительные и отрицательные проверочные случаи (документация)

> **Статус: `DRAFT / NOT ACTIVE`.** Это **описание** тестов для будущего валидатора, а не результат его работы. Валидатора v2 не существует. Код валидатора и его прогон — отдельная будущая задача (G0 #6831274083: `formal_validator_tests: separate_future_task`). Байтовые факты (длины и SHA-256 файлов `fixtures/`) пересчитаны автором и перечислены в [`fixtures/SHA256SUMS`](fixtures/SHA256SUMS). Ожидаемые исходы ниже выведены из текста контракта и **не** проверялись исполняемым кодом.

Покрывает: **AC-6** (обязательные категории: двойной CLAIM, истёкший lease, устаревший ASSIGN, самопроверка, отредактированный комментарий, HTTP 403, неверный digest, неверная база, неверная сериализация) и сценарии для AC-1–AC-5, AC-7, AC-8.

Столбцы исхода: `reason_code`; `result / execution_status / verification_status` для check; `report_validity / verdict`; статус задачи. Прочерк означает, что данные check не принимаются (отчёт или сообщение отвергнуты целиком).

Синтетический контекст для фикстур RESUME/2 описан в [RESUME2-FIXTURE.md §2](RESUME2-FIXTURE.md).

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
