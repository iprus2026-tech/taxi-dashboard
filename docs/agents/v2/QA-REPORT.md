# v2 — QA-REPORT/2: независимые измерения результата, reason_code и независимость проверяющего

> **Статус: `DRAFT / NOT ACTIVE`.** Действует `docs/agents/PROTOCOL.md` v1. Исторические `QA-REPORT/1` сохраняются без семантических изменений. См. [README.md](README.md).

Покрывает: **AC-5** (`execution_status`, `verification_status`, `report_validity` и `verdict` независимы; отсутствующее или непроверенное доказательство не может дать PASS).

> **Ревизия `TAXI-AGENT-PROTOCOL-V2-REWORK-01`** ([Issue #28](https://github.com/iprus2026-tech/taxi-dashboard/issues/28)). Документарная доработка замечаний F1 и F2 из [QA-REPORT/1 #6835645843](https://github.com/iprus2026-tech/taxi-dashboard/issues/26#issuecomment-6835645843). Изменены §2 (поле `evidence_outcome`), §3 (I1, новый I10), §4 (субъект кодов, новые коды `EVIDENCE_REF_INVALID` и `EVIDENCE_TS_UNVERIFIABLE`, §4.1–§4.2) и §6 (п.1, новый п.6). Добавлены §7 (отрицательные случаи) и §8 (межфайловые проверки согласованности). Таблица решений §4.2 побайтно совпадает с [EVIDENCE.md §2.2](EVIDENCE.md). Проводная форма QA-REPORT/2 по-прежнему отложена (F4, [README.md §5](README.md) п.6). Это только документация: исполняемого валидатора v2 нет.

> **Исправление P2-QA29-01** (независимый [QA #6844821824](https://github.com/iprus2026-tech/taxi-dashboard/issues/28#issuecomment-6844821824), [решение координатора #6844912455](https://github.com/iprus2026-tech/taxi-dashboard/issues/28#issuecomment-6844912455)). D14 ограничен: сообщение-предмет оценивается шагами E1–E8 без исключений и не получает `VERIFIED` ([EVIDENCE.md §2.2](EVIDENCE.md) правило 6). Изменены строка D14 (одинаково с EVIDENCE.md), строка «сообщение — предмет check» в §4.1; добавлены NEG-D14-01 в §7 и C-10 в §8. I1–I10 и словарь не менялись.

> **Ревизия `TAXI-AGENT-PROTOCOL-V2-F4-WIRE-01`** ([Issue #32](https://github.com/iprus2026-tech/taxi-dashboard/issues/32)). Проводная форма QA-REPORT/2 определена в [F4-WIRE.md](F4-WIRE.md) §8–§9. Добавлены только абзац в конце §2, абзац после таблицы решений §4.2 и проверки C-11–C-17 в §8. Таблица решений D01–D16 (байты блока), I1–I10, словарь `reason_code`, §4.1 и порядок §6 не менялись. Коды разбора `F4-*` — диагностика валидатора, а не значения `reason_code`. Это только документация: валидатора нет, v2 не активирован.

---

## 1. Четыре независимых измерения

| Поле | Уровень | Значения | Что означает |
|---|---|---|---|
| `execution_status` | check | `COMPLETED` \| `NOT_RUN` \| `HALTED` | была ли проверка выполнена до конца |
| `verification_status` | check | `VERIFIED` \| `NOT_VERIFIED` \| `NOT_AVAILABLE` | подтверждено ли доказательство напрямую ([EVIDENCE.md §2](EVIDENCE.md)) |
| `report_validity` | отчёт | `VALID` \| `STALE` \| `INVALID` | можно ли вообще принимать отчёт |
| `verdict` | отчёт | `PASS` \| `FAIL` \| `VOID` | итог приёмки |

Кроме них у каждого check есть `result: PASS | FAIL | NOT_RUN` и `provenance`.

**Независимость:** каждое поле записывается отдельно. Ни одно поле не подменяет другое и не выводится агентом «по умолчанию» из другого. `reason_code` никогда не заменяет `verdict`. `confidence_label` (`HIGH | MEDIUM | LOW | UNKNOWN`) описывает неуверенность и **никогда** не заменяет `verification_status: VERIFIED`. Зависимости между полями задаются **только** инвариантами §3 и порядком §6. Агент не может переписать `HALTED` в `COMPLETED`.

## 2. Поля QA-REPORT/2

| Поле | Правило |
|---|---|
| `schema` | `QA-REPORT/2` |
| `task`, `agent`, `session`, `ts` | задача проверяющего, его агент и фактическая сессия; время v2 |
| `assign_ref` | токен назначения **проверяющего** ([LIFECYCLE.md §4](LIFECYCLE.md)) |
| `reviews` | Task ID проверяемой задачи |
| `handoff_ref` | ID комментария проверяемого HANDOFF/2 (фиксирует координатор, [LIFECYCLE.md §7](LIFECYCLE.md)) |
| `spec_sha256` | утверждённый на G0 хэш проверяемой задачи, пересчитанный до и после |
| `head_sha` | только для `CODE_CHANGE/1`; до и после = `git ls-remote origin <branch>` |
| `source_checks.before`, `source_checks.after` | только для `READ_ONLY_EVIDENCE_QA/1`: результаты S1–S6 и `refs_snapshot_sha256` ([PROFILES.md §5](PROFILES.md)) |
| `checks[]` | §3 |
| `report_validity` | §6 |
| `verdict` | §6; **отсутствует** при `INVALID` |
| `environment` | только для проверок с запуском: ОС, `qa_port` вне 5000/5001/5002, `isolated_storage: true` (v1 §7.3–7.4) |

Каждый элемент `checks[]`: `id`, `required`, `result`, `execution_status`, `verification_status`, `evidence`, `evidence_outcome`, `provenance`, `reason_code`, `reason`.

- `id` совпадает с AC утверждённой SPEC.
- `required` берётся из неизменной утверждённой SPEC. Агент его не выбирает.
- `evidence` — `EvidenceRef/2` или `null`.
- `evidence_outcome` — итог оценки этой ссылки по [EVIDENCE.md §2, §2.1](EVIDENCE.md): `VERIFIED` | `NOT_VERIFIED` | `REJECTED` | `STALE` | `none`. `none` — только если `evidence: null` или check остановлен до оценки ссылки.
- `provenance`: `DIRECT_SOURCE` | `CODE_DERIVED` | `AGENT_REPORTED` | `INFERRED` | `OWNER_ATTESTED` | `RELAYED_OWNER_STATEMENT`.
- `reason_code` и текст `reason` обязательны всегда, когда check не полностью подтверждён, пропущен, выведен или не выполнен.

**Проводная форма** ([F4-WIRE.md §8](F4-WIRE.md)). Поля идут в порядке этой таблицы, поля элемента `checks[]` — в порядке списка выше. Поле «только для» профиля проверяемой задачи (`head_sha` или `source_checks`) и `verdict` при `INVALID` опускаются. `evidence: null` записывается строкой `checks.<i>.evidence: none`, «—» в `reason_code` — значением `none`. `EvidenceRef/2` записывается группой ключей, содержимое которой оценивает шаг E1 ([EVIDENCE.md §2.1](EVIDENCE.md)), а не схема отчёта: некорректная ссылка остаётся D06 и не делает отчёт `INVALID`. Грамматика SPEC/2 не знает необязательных AC, поэтому `required` для каждого AC SPEC/2 равно `true`, а `checks` содержит ровно AC-1..AC-k проверяемой SPEC ([F4-WIRE.md §9.2](F4-WIRE.md) `F4-Q01`, `F4-Q02`). Положительные векторы — POS-F4-02 (`VALID` / `PASS`) и POS-F4-04 (`VALID` / `FAIL` из-за D06).

## 3. Инварианты check

| # | Инвариант |
|---|---|
| I1 | `result: PASS` ⇒ `execution_status: COMPLETED` **и** `verification_status: VERIFIED`; для check, где нужно доказательство, ещё и `evidence ≠ null` с SHA-256, который проверяющий пересчитал сам, и `evidence_outcome: VERIFIED` |
| I2 | Check выполнен, но доказательство не подтверждено независимо ⇒ `COMPLETED + NOT_VERIFIED + FAIL`. Записывать его как `NOT_RUN` запрещено |
| I3 | Check действительно не выполнялся ⇒ `NOT_RUN + NOT_AVAILABLE + NOT_RUN` с причиной |
| I4 | Наблюдаемый провал ⇒ `COMPLETED + VERIFIED + FAIL` допустим |
| I5 | `evidence: null` допустим только для действительно недоступных или невыполненных пунктов и только с `reason`. Для `PASS` — никогда |
| I6 | `provenance` `AGENT_REPORTED`, `INFERRED` или `RELAYED_OWNER_STATEMENT` ⇒ `verification_status ≠ VERIFIED` ⇒ `result ≠ PASS` |
| I7 | `OWNER_ATTESTED` — только для оформленного личного заявления владельца. Пересказ агентом и подпись общим логином GitHub — это `RELAYED_OWNER_STATEMENT` |
| I8 | Любой обязательный check не в состоянии `PASS` ⇒ общий `verdict ≠ PASS` |
| I9 | Заглушки, выдуманные хэши и «ожидаемые» значения вместо пересчитанных запрещены |
| I10 | `evidence_outcome`, `reason_code` и тройка check согласованы по таблице решений §4.2. `REJECTED` ⇔ `reason_code` ∈ {`CANONICALIZATION_ERROR`, `EVIDENCE_REF_INVALID`}, тройка `FAIL + COMPLETED + NOT_VERIFIED`. `NOT_VERIFIED` ⇒ `reason_code` ∈ {`EVIDENCE_NOT_ACCESSIBLE`, `ATTACHMENT_403`, `EVIDENCE_TS_UNVERIFIABLE`, `PRIMARY_SOURCE_UNKNOWN`}, тройка `FAIL + COMPLETED + NOT_VERIFIED`; обратно `EVIDENCE_NOT_ACCESSIBLE`, `ATTACHMENT_403`, `EVIDENCE_TS_UNVERIFIABLE` ⇒ `NOT_VERIFIED`, а `PRIMARY_SOURCE_UNKNOWN` ⇒ `NOT_VERIFIED`, если попытка была, и `none`, если её не было (§4). `STALE` ⇔ `reason_code` ∈ {`STALE_EVIDENCE`, `EVIDENCE_DELETED`}, тройка `FAIL + HALTED + NOT_AVAILABLE`. `VERIFIED` ⇒ `verification_status: VERIFIED`. `evidence_outcome` ≠ `VERIFIED` ⇒ `result` ≠ PASS. `SCHEMA_INVALID` в `checks[]` запрещён |

Следствие: **отсутствующее, непроверенное, отвергнутое или устаревшее доказательство не может дать PASS** ни на уровне check (I1, I5, I6, I10), ни на уровне отчёта (I8).

## 4. Закрытый словарь `reason_code` и детерминированные исходы

Допустимы только перечисленные значения. Любая другая строка → `SCHEMA_INVALID`, если SPEC не вводит новую версию словаря.

| reason_code | `result` | `execution_status` | `verification_status` | `report_validity` | `verdict` | Статус задачи |
|---|---|---|---|---|---|---|
| `STALE_SOURCE` (закреплённый источник недоступен, ref откатан; **не** допустимый fast-forward цели) | FAIL | HALTED | NOT_AVAILABLE | STALE | VOID | `blocked` |
| `STALE_EVIDENCE`, `EVIDENCE_DELETED` | FAIL | HALTED | NOT_AVAILABLE | STALE | VOID | `blocked`; ссылку повторно не использовать |
| `CONFLICT_OF_INTEREST` | — (данные check не принимаются) | — | — | INVALID | **отсутствует** | `blocked`; владелец назначает другого проверяющего |
| `AUTH_ATTESTATION_UNVERIFIED` | — | — | — | INVALID | отсутствует | `blocked`; нужно свежее личное решение владельца |
| `SCHEMA_INVALID`, `CANONICALIZATION_ERROR` — субъект «отчёт» или «сообщение-основание» (§4.1; D10–D13, D15–D16) | — | — | — | INVALID | отсутствует | `blocked`; сообщение отвергнуто |
| `CANONICALIZATION_ERROR` — субъект «доказательство», только в `checks[]` при `evidence_outcome: REJECTED` (D07) | FAIL | COMPLETED | NOT_VERIFIED | VALID | FAIL | `handoff`; нужно новое корректное доказательство |
| `EVIDENCE_REF_INVALID` — поле самой `EvidenceRef/2` отсутствует или некорректно, `evidence_outcome: REJECTED` (D06) | FAIL | COMPLETED | NOT_VERIFIED | VALID | FAIL | `handoff`; нужна корректная ссылка |
| `EVIDENCE_TS_UNVERIFIABLE` — GitHub вернул для комментария-доказательства `updated_at`, который не проходит [EVIDENCE.md §6.1](EVIDENCE.md), `evidence_outcome: NOT_VERIFIED` (D05) | FAIL | COMPLETED | NOT_VERIFIED | VALID | FAIL | `handoff`; объяснить, что не подтверждено |
| `UNAPPROVED_BASE` (SPEC, G0, база или цель не совпадают) | — | — | — | INVALID | отсутствует | `blocked`; без ASSIGN/RESUME |
| `UNRUN_REQUIRED` | NOT_RUN | NOT_RUN | NOT_AVAILABLE | VALID | FAIL | `handoff` для решения владельца; никогда не QA PASS |
| `PRIMARY_SOURCE_UNKNOWN`, попытки не было | NOT_RUN | NOT_RUN | NOT_AVAILABLE | VALID | FAIL | `handoff` |
| `PRIMARY_SOURCE_UNKNOWN`, попытка была | FAIL | COMPLETED | NOT_VERIFIED | VALID | FAIL | `handoff` |
| `EVIDENCE_NOT_ACCESSIBLE`, `ATTACHMENT_403` (попытка была) | FAIL | COMPLETED | NOT_VERIFIED | VALID | FAIL | `handoff`; объяснить, что не подтверждено |
| `SCOPE_VIOLATION` (запись вне scope, доказанно связанная с задачей) | FAIL | HALTED | NOT_VERIFIED | VALID | VOID | `blocked`; отдельная проверка безопасности |
| `LEASE_EXPIRED`, `SESSION_STALE`, `ASSIGN_FENCE_STALE` | FAIL | HALTED | NOT_VERIFIED | STALE | VOID | `blocked`; только новое разрешение координатора (для RESUME/2 — с личным G0) |
| `REF_DRIFT_UNEXPLAINED` (необъяснённое изменение не-целевого ref) | FAIL | HALTED | NOT_VERIFIED | STALE | VOID | `blocked`; расследование; **не** автоматически `SCOPE_VIOLATION` |

Примечание о порядке: в DESIGN_NOTE/3 R2 тройки записаны в разном порядке (в тексте `execution + verification + result`, в таблице `result; execution; verification`). Здесь каждое измерение вынесено в отдельный именованный столбец, а значения перенесены без изменений.

Строки с исходом `VALID / FAIL` описывают **обязательный** check. Если такой исход у необязательного выполненного check, итог отчёта вычисляется по §6 п.5–6.

### 4.1 Субъект классификации

Один и тот же `reason_code` может относиться к разным объектам. Субъект определяется **местом** записи, а не выбором агента:

| Субъект | Где записывается | Что затрагивает |
|---|---|---|
| доказательство (`EvidenceRef/2` и её байты) | `checks[i].reason_code` вместе с `checks[i].evidence_outcome` | только check `i`; отчёт не становится `INVALID` |
| сообщение-основание (личный G0, `ASSIGN/2` или `RESUME/2` проверяющего, проверяемый `HANDOFF/2`) | диагностика внешнего валидатора | отчёт без действительного основания → `INVALID`, verdict отсутствует |
| сообщение — предмет check (не основание) | `checks[i]`: ссылка на сообщение оценивается шагами E1–E8 как доказательство (D14) | только check `i`; отчёт не становится `INVALID`; `VERIFIED` для обычного `agent-msg` в этой ревизии недостижим |
| отчёт (сам `QA-REPORT/2`) | диагностика внешнего валидатора | `INVALID`, verdict отсутствует; check не принимаются |

Некорректная ссылка на доказательство (`REJECTED`) — это **не** `INVALID` отчёта. Отчёт с такой ссылкой остаётся `VALID` и не может получить PASS по обязательному check, где она стоит.

### 4.2 Таблица решений (общая для EVIDENCE.md и QA-REPORT.md)

<!-- DECISION-TABLE/1 BEGIN: блок побайтно одинаков в EVIDENCE.md §2.2 и QA-REPORT.md §4.2 -->
| # | Субъект | Ситуация | `evidence_outcome` | `reason_code` | check: `result` / `execution_status` / `verification_status` | `report_validity` | `verdict` |
|---|---|---|---|---|---|---|---|
| D01 | доказательство | байты получены проверяющим напрямую; SHA-256 пересчитан и совпал; шаги F1 и F3 (EVIDENCE.md §5) дали значения, равные закреплённым | `VERIFIED` | — | PASS допустим / COMPLETED / VERIFIED | VALID | допустим; итог по QA-REPORT.md §6 |
| D02 | доказательство | байты получены, источник не менялся, но пересчитанный SHA-256 ≠ заявленному | `VERIFIED` (для фактических байтов) | — (обязателен текст `reason`) | FAIL / COMPLETED / VERIFIED | VALID | допустим; не PASS, если check обязательный |
| D03 | доказательство | 403, 401, 429, 5xx, таймаут, нет канала или прав, только relay; API не вернул строку `body` (нет поля, `null`, не строка) | `NOT_VERIFIED` | `EVIDENCE_NOT_ACCESSIBLE` (вложение: `ATTACHMENT_403`) | FAIL / COMPLETED / NOT_VERIFIED | VALID | допустим; не PASS, если check обязательный |
| D04 | доказательство | digest известен только со слов агента (`provenance: AGENT_REPORTED`), попытка получить байты была | `NOT_VERIFIED` | `PRIMARY_SOURCE_UNKNOWN` | FAIL / COMPLETED / NOT_VERIFIED | VALID | допустим; не PASS, если check обязательный |
| D05 | доказательство | `updated_at` комментария-доказательства, который вернул GitHub, отсутствует, `null`, пуст или не проходит EVIDENCE.md §6.1 | `NOT_VERIFIED` | `EVIDENCE_TS_UNVERIFIABLE` | FAIL / COMPLETED / NOT_VERIFIED | VALID | допустим; не PASS, если check обязательный |
| D06 | доказательство | поле самой `EvidenceRef/2` отсутствует или некорректно: `comment_updated_at` отсутствует, пуст или не в форме EVIDENCE.md §6.2; SHA-256 не `[0-9a-f]{64}`; `commit` не `[0-9a-f]{40}`; адрес на ветку; `algorithm` ≠ `ISSUE_TEXT_LF/1`; неизвестный `type` | `REJECTED` | `EVIDENCE_REF_INVALID` | FAIL / COMPLETED / NOT_VERIFIED | VALID | допустим; не PASS, если check обязательный |
| D07 | доказательство | декодированное `body` получено, но нарушена грамматика `ISSUE_TEXT_LF/1` (EVIDENCE.md §4.1 п.1–6) или строка содержит непарные суррогаты | `REJECTED` | `CANONICALIZATION_ERROR` (субъект — доказательство) | FAIL / COMPLETED / NOT_VERIFIED | VALID | допустим; не PASS, если check обязательный |
| D08 | доказательство | `updated_at` или `body_sha256` изменились между шагами F1 и F3 или относительно закреплённых | `STALE` | `STALE_EVIDENCE` | FAIL / HALTED / NOT_AVAILABLE | STALE | только VOID |
| D09 | доказательство | 404 на закреплённый комментарий | `STALE` | `EVIDENCE_DELETED` | FAIL / HALTED / NOT_AVAILABLE | STALE | только VOID |
| D10 | сообщение-основание | канонические байты нарушают LIFECYCLE.md §1 п.3 | — | `CANONICALIZATION_ERROR` (субъект — сообщение) | check не принимаются | INVALID | отсутствует |
| D11 | сообщение-основание | ключи или значения нарушают схему, в том числе собственные `ts` или `lease_until` не в формате времени v2 | — | `SCHEMA_INVALID` | check не принимаются | INVALID | отсутствует |
| D12 | сообщение-основание | GitHub: `updated_at` ≠ `created_at` после нормализации (сообщение отредактировано) | — | `SCHEMA_INVALID` | check не принимаются | INVALID | отсутствует |
| D13 | сообщение-основание | GitHub: `created_at` или `updated_at` отсутствует или не проходит EVIDENCE.md §6.1; неизменность сообщения установить нельзя (fail closed) | — | `SCHEMA_INVALID` | check не принимаются | INVALID | отсутствует |
| D14 | сообщение — предмет check, а не основание | check исследует сообщение протокола, которое не является основанием отчёта (например, чтобы установить его недействительность по D10–D13). Отдельного типа `EvidenceRef/2` для обычного комментария `agent-msg` в этой ревизии нет: ссылка оценивается шагами E1–E8 без исключений, D14 их не переопределяет (EVIDENCE.md §2.2 правило 6). Если раньше не сработали D03–D05 или D08–D09, ссылка `github_issue_text` на такой комментарий не проходит E5 (первая строка — fence, а не `BEGIN-EVIDENCE-TEXT/1`), а неизвестный `type` не проходит E1 | `REJECTED` | `CANONICALIZATION_ERROR` (E5, субъект — доказательство) или `EVIDENCE_REF_INVALID` (E1) | FAIL / COMPLETED / NOT_VERIFIED | VALID | допустим; не PASS, если check обязательный; `VERIFIED` для такого предмета недостижим |
| D15 | отчёт | нарушена схема самого QA-REPORT/2: нет обязательного поля, недопустимая пара QA-REPORT.md §6, нарушен любой из I1–I10, `ts` отчёта не в формате времени v2, неизвестный `reason_code`, `SCHEMA_INVALID` внутри `checks[]` | — | `SCHEMA_INVALID` | check не принимаются | INVALID | отсутствует |
| D16 | отчёт | нарушены байтовые правила проводной формы самого отчёта (применимо только после того, как эта форма будет определена, см. F4) | — | `CANONICALIZATION_ERROR` (субъект — отчёт) | check не принимаются | INVALID | отсутствует |
<!-- DECISION-TABLE/1 END -->

Порядок оценки одной ссылки (шаги E1–E8) и правила таблицы — [EVIDENCE.md §2.1, §2.2](EVIDENCE.md). Они действуют здесь без изменений.

Строка D16 ссылается на проводную форму, которая теперь определена: байтовые правила и обёртка — [F4-WIRE.md §2–§3](F4-WIRE.md), коды `F4-W*` и `F4-B*`. Нарушения строк, ключей, значений и инвариантов отчёта (`F4-L*`, `F4-K*`, `F4-S*`, `F4-Q*`) относятся к D15, а нарушения в проверяемом `HANDOFF/2` — к D10–D13 ([F4-WIRE.md §11](F4-WIRE.md)). Коды `F4-*` записывает внешний валидатор. В `checks[].reason_code` они недопустимы и в словарь §4 не входят (F4-WIRE.md NEG-F4-17). Сам блок таблицы не изменён.

## 5. Независимость проверяющего

| Ситуация | Решение |
|---|---|
| Автор дизайна проверяет свой дизайн | **ЗАПРЕЩЕНО** как независимый QA → `CONFLICT_OF_INTEREST` |
| Автор кода проверяет свою реализацию | **ЗАПРЕЩЕНО** → `CONFLICT_OF_INTEREST` |
| Исполнитель доказательств — единственный проверяющий файлов, которые контролировал только он | **ЗАПРЕЩЕНО** как единственная проверка |
| Проверяющий ранее предлагал часть идей проверяемого дизайна | раскрыть + арбитраж владельца |
| Координатор, он же автор дизайна | может организовать приём, **не может** сертифицировать свой дизайн |
| Заявление владельца пересказано агентом | `RELAYED_OWNER_STATEMENT`, не личное утверждение |
| Проверяющий без конфликта ролей | допустим, если доступ и идентичность сессии достаточны для стандарта владельца |

При общем аккаунте GitHub (v1 §0.1) всё это процедурно. Граница уровня безопасности требует отдельных учётных записей или GitHub App, ограниченных прав и подписей. Этот контракт таких прав не создаёт.

## 6. Вычисление итога (фиксированный приоритет)

Валидатор отчёта применяет правила по порядку. Срабатывает первое подходящее:

1. Нарушения схемы, авторизации или конфликт интересов (`SCHEMA_INVALID`, `CANONICALIZATION_ERROR`, `UNAPPROVED_BASE`, `AUTH_ATTESTATION_UNVERIFIED`, `CONFLICT_OF_INTEREST`) → `report_validity: INVALID`, поле `verdict` **отсутствует**. Check из такого отчёта не принимаются, даже если в них написано `PASS`. `SCHEMA_INVALID` и `CANONICALIZATION_ERROR` срабатывают здесь **только** с субъектом «отчёт» или «сообщение-основание» (§4.1). Тот же `CANONICALIZATION_ERROR` в `checks[]` с субъектом «доказательство» (D07), а также `EVIDENCE_REF_INVALID` (D06) и `EVIDENCE_TS_UNVERIFIABLE` (D05) этот пункт не запускают: они обрабатываются п.4–6.
2. Устаревший источник, доказательство, сессия, lease или токен (`STALE_SOURCE`, `STALE_EVIDENCE`, `EVIDENCE_DELETED`, `LEASE_EXPIRED`, `SESSION_STALE`, `ASSIGN_FENCE_STALE`, `REF_DRIFT_UNEXPLAINED`) → `STALE`, `VOID`.
3. Доказанное нарушение scope (`SCOPE_VIOLATION`) → `VALID`, `VOID`.
4. Хотя бы один обязательный check не `PASS` → `VALID`, `FAIL`.
5. `VALID`, `PASS` — только если все обязательные check `PASS` и ни один выполненный необязательный check не `FAIL`.
6. Иначе (все обязательные check `PASS`, но выполненный необязательный check `FAIL`, в том числе из-за `REJECTED` или `NOT_VERIFIED` доказательства) → `VALID`, `FAIL`.

Допустимые пары: `INVALID` + (нет verdict); `STALE` + `VOID`; `VALID` + `PASS | FAIL | VOID`. Любая другая пара → `SCHEMA_INVALID`.

Отчёт с неверной схемой не получает принятого вердикта. Диагностику `INVALID` записывает внешний валидатор, а не сам отчёт. Выдавать `SCHEMA_INVALID` за продуктовый `FAIL` запрещено.

Workflow-статус меняет только координатор по политике владельца. QA не может перевести `handoff` в `done`.

## 7. Отрицательные случаи F1/F2 (только документация)

Ожидаемое поведение будущего валидатора, выведенное из текста. Это не прогон и не фикстуры. Примеры правильной классификации — [EVIDENCE.md §2.3](EVIDENCE.md); там же NEG-F1-01..04 и NEG-F2-01..03.

| ID | Вход | Ожидание |
|---|---|---|
| NEG-F1-05 | обязательный check: `evidence_outcome: REJECTED`, `reason_code: CANONICALIZATION_ERROR`, `result: FAIL`; отчёт записан как `INVALID` без verdict | неверно: субъект — доказательство (§4.1). Правильно: `VALID`, `FAIL` (§6 п.4) |
| NEG-F1-06 | `evidence_outcome: REJECTED` с `reason_code: EVIDENCE_NOT_ACCESSIBLE` | нарушен I10 → `SCHEMA_INVALID` отчёта (D15) |
| NEG-F1-07 | `evidence_outcome: NOT_VERIFIED` с `reason_code: CANONICALIZATION_ERROR` | нарушен I10 → `SCHEMA_INVALID` отчёта (D15) |
| NEG-F1-08 | check `PASS`, `evidence_outcome: NOT_VERIFIED` или `REJECTED` | нарушены I1 и I10 → `SCHEMA_INVALID` отчёта |
| NEG-F2-04 | `checks[].reason_code: SCHEMA_INVALID` для ссылки с некорректным `comment_updated_at` | нарушен I10 → `SCHEMA_INVALID` отчёта. Правильно: `EVIDENCE_REF_INVALID` (D06), отчёт `VALID` |
| NEG-F2-05 | `ts` отчёта без `.sss`; отчёт записывает это как check с `EVIDENCE_TS_UNVERIFIABLE` | неверно: субъект — отчёт (D15) → `INVALID`, verdict отсутствует |
| NEG-F2-06 | `ASSIGN/2` проверяющего отредактирован (`updated_at` ≠ `created_at`); отчёт объявлен `VALID` | неверно: сообщение-основание (D12) → `INVALID`, verdict отсутствует |
| NEG-F2-07 | необязательный выполненный check FAIL из-за D05; обязательные PASS; отчёт `VALID`, `PASS` | неверно: §6 п.5 не выполнен, итог по п.6 → `VALID`, `FAIL` |
| NEG-D14-01 | сообщение-предмет: 774-байтное тело `` ```agent-msg `` вокруг фикстуры RESUME/2, `DECODED_BODY_UTF8/1` SHA-256 `11a352f2bad2ac2c30ecb77ee904e64d5c9350e8efed78d224bd0e3e59879968`, синтетические `created_at` 15:00:00Z и `updated_at` 15:01:00Z; check записан как FAIL / COMPLETED / VERIFIED | неверно: E5 не пройден → D14 = D07, `REJECTED` / `CANONICALIZATION_ERROR`, FAIL / COMPLETED / NOT_VERIFIED, отчёт VALID. Запись `VERIFIED` нарушает I10 → `SCHEMA_INVALID` отчёта (D15). Полное построение — [EVIDENCE.md §2.5](EVIDENCE.md) |

## 8. Межфайловые проверки согласованности (статические)

Это проверки текста, которые проверяющий может повторить офлайн. Они **не** являются прогоном валидатора v2.

| ID | Проверка | Ожидание |
|---|---|---|
| C-01 | блок между маркерами `DECISION-TABLE/1 BEGIN` и `END` в [EVIDENCE.md §2.2](EVIDENCE.md) и в §4.2 этого файла | побайтно одинаковы (одинаковый SHA-256) |
| C-02 | каждый `reason_code` из таблицы решений | есть в закрытом словаре §4 |
| C-03 | каждый `evidence_outcome` из таблицы решений | есть в [EVIDENCE.md §2](EVIDENCE.md) и в поле `checks[].evidence_outcome` §2 |
| C-04 | пары `evidence_outcome` ↔ `reason_code` в таблице решений | совпадают с I10 |
| C-05 | [TEST-CASES.md](TEST-CASES.md) NEG-AC4-01..04 (`CANONICALIZATION_ERROR` конверта) | соответствуют D07: субъект — доказательство, отчёт не `INVALID` |
| C-06 | TEST-CASES.md NEG-AC4-05 и NEG-AC7-04 (ссылка `NOT_VERIFIED`) | соответствуют D04 и D05 |
| C-07 | TEST-CASES.md NEG-10, NEG-11, NEG-13, NEG-14 | соответствуют D08, D12, D03 (`ATTACHMENT_403`), D03 (`EVIDENCE_NOT_ACCESSIBLE`) |
| C-08 | TEST-CASES.md NEG-AC5-01..04, NEG-AC5-06 и NEG-21 (NEG-AC5-05 — это `UNRUN_REQUIRED`, VALID / FAIL, вне таблицы решений) | соответствуют D15 (отчёт) и D10–D11 (сообщение) |
| C-09 | [LIFECYCLE.md §1](LIFECYCLE.md) п.6–7 (байты, ключи и правка сообщения) | соответствуют D10–D12 |
| C-10 | строка D14 таблицы решений, EX-F2-07 и NEG-D14-01 | D14 даёт `REJECTED` с кодом из набора I10 и тройку FAIL / COMPLETED / NOT_VERIFIED; ни строка D14, ни EX-F2-07 не дают `VERIFIED` для сообщения-предмета; NEG-D14-01 проходит E1–E4 и останавливается на E5 |
| C-11 | блок `DECISION-TABLE/1` в этом файле и в EVIDENCE.md после ревизии F4 | побайтно равен блоку на Base `cf92e83c45f8b0ed9e310f2bbcb96bec6dd39059`: 7038 байт, SHA-256 `e91f4d30c89e6b0583666f980864029c8b6c6844989138ee155927014a5aba03` |
| C-12 | коды `F4-*` из [F4-WIRE.md §11](F4-WIRE.md) и закрытый словарь §4 | не пересекаются; словарь `checks.<i>.reason_code` в F4-WIRE.md §6 = 19 кодов §4 и `none` |
| C-13 | последовательность ключей `HANDOFF/2` (F4-WIRE.md §7) и таблица [LIFECYCLE.md §7](LIFECYCLE.md) | тот же набор полей и порядок строк; поля «—» и «отсутствует» опущены |
| C-14 | последовательность ключей `QA-REPORT/2` (F4-WIRE.md §8) и §2 этого файла | тот же набор полей и порядок; поля элемента `checks[]` в порядке §2 |
| C-15 | таблица сочетаний F4-WIRE.md §9.3 и таблица исходов §4, I1–I6, I10 | каждая строка §9.3 выводится из §4 и инвариантов; `PASS` возможен только при `evidence_outcome: VERIFIED` |
| C-16 | длина и SHA-256 положительных векторов F4-WIRE.md §14, извлечённых командами §14.5 | совпадают с указанными; `spec_sha256` векторов = SHA-256 синтетических SPEC/2 §13.1–§13.2 |
| C-17 | `fixtures/` (30 файлов, `SHA256SUMS`), EVIDENCE.md, PROFILES.md, RESUME2-FIXTURE.md, `.gitattributes`, `docs/agents/PROTOCOL.md` | побайтно равны Base; изменены только пять разрешённых путей |
