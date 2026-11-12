# v2 — QA-REPORT/2: независимые измерения результата, reason_code и независимость проверяющего

> **Статус: `DRAFT / NOT ACTIVE`.** Действует `docs/agents/PROTOCOL.md` v1. Исторические `QA-REPORT/1` сохраняются без семантических изменений. См. [README.md](README.md).

Покрывает: **AC-5** (`execution_status`, `verification_status`, `report_validity` и `verdict` независимы; отсутствующее или непроверенное доказательство не может дать PASS).

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

Каждый элемент `checks[]`: `id`, `required`, `result`, `execution_status`, `verification_status`, `evidence`, `provenance`, `reason_code`, `reason`.

- `id` совпадает с AC утверждённой SPEC.
- `required` берётся из неизменной утверждённой SPEC. Агент его не выбирает.
- `evidence` — `EvidenceRef/2` или `null`.
- `provenance`: `DIRECT_SOURCE` | `CODE_DERIVED` | `AGENT_REPORTED` | `INFERRED` | `OWNER_ATTESTED` | `RELAYED_OWNER_STATEMENT`.
- `reason_code` и текст `reason` обязательны всегда, когда check не полностью подтверждён, пропущен, выведен или не выполнен.

## 3. Инварианты check

| # | Инвариант |
|---|---|
| I1 | `result: PASS` ⇒ `execution_status: COMPLETED` **и** `verification_status: VERIFIED`; для check, где нужно доказательство, ещё и `evidence ≠ null` с SHA-256, который проверяющий пересчитал сам |
| I2 | Check выполнен, но доказательство не подтверждено независимо ⇒ `COMPLETED + NOT_VERIFIED + FAIL`. Записывать его как `NOT_RUN` запрещено |
| I3 | Check действительно не выполнялся ⇒ `NOT_RUN + NOT_AVAILABLE + NOT_RUN` с причиной |
| I4 | Наблюдаемый провал ⇒ `COMPLETED + VERIFIED + FAIL` допустим |
| I5 | `evidence: null` допустим только для действительно недоступных или невыполненных пунктов и только с `reason`. Для `PASS` — никогда |
| I6 | `provenance` `AGENT_REPORTED`, `INFERRED` или `RELAYED_OWNER_STATEMENT` ⇒ `verification_status ≠ VERIFIED` ⇒ `result ≠ PASS` |
| I7 | `OWNER_ATTESTED` — только для оформленного личного заявления владельца. Пересказ агентом и подпись общим логином GitHub — это `RELAYED_OWNER_STATEMENT` |
| I8 | Любой обязательный check не в состоянии `PASS` ⇒ общий `verdict ≠ PASS` |
| I9 | Заглушки, выдуманные хэши и «ожидаемые» значения вместо пересчитанных запрещены |

Следствие: **отсутствующее или непроверенное доказательство не может дать PASS** ни на уровне check (I1, I5, I6), ни на уровне отчёта (I8).

## 4. Закрытый словарь `reason_code` и детерминированные исходы

Допустимы только перечисленные значения. Любая другая строка → `SCHEMA_INVALID`, если SPEC не вводит новую версию словаря.

| reason_code | `result` | `execution_status` | `verification_status` | `report_validity` | `verdict` | Статус задачи |
|---|---|---|---|---|---|---|
| `STALE_SOURCE` (закреплённый источник недоступен, ref откатан; **не** допустимый fast-forward цели) | FAIL | HALTED | NOT_AVAILABLE | STALE | VOID | `blocked` |
| `STALE_EVIDENCE`, `EVIDENCE_DELETED` | FAIL | HALTED | NOT_AVAILABLE | STALE | VOID | `blocked`; ссылку повторно не использовать |
| `CONFLICT_OF_INTEREST` | — (данные check не принимаются) | — | — | INVALID | **отсутствует** | `blocked`; владелец назначает другого проверяющего |
| `AUTH_ATTESTATION_UNVERIFIED` | — | — | — | INVALID | отсутствует | `blocked`; нужно свежее личное решение владельца |
| `SCHEMA_INVALID`, `CANONICALIZATION_ERROR` | — | — | — | INVALID | отсутствует | `blocked`; сообщение отвергнуто |
| `UNAPPROVED_BASE` (SPEC, G0, база или цель не совпадают) | — | — | — | INVALID | отсутствует | `blocked`; без ASSIGN/RESUME |
| `UNRUN_REQUIRED` | NOT_RUN | NOT_RUN | NOT_AVAILABLE | VALID | FAIL | `handoff` для решения владельца; никогда не QA PASS |
| `PRIMARY_SOURCE_UNKNOWN`, попытки не было | NOT_RUN | NOT_RUN | NOT_AVAILABLE | VALID | FAIL | `handoff` |
| `PRIMARY_SOURCE_UNKNOWN`, попытка была | FAIL | COMPLETED | NOT_VERIFIED | VALID | FAIL | `handoff` |
| `EVIDENCE_NOT_ACCESSIBLE`, `ATTACHMENT_403` (попытка была) | FAIL | COMPLETED | NOT_VERIFIED | VALID | FAIL | `handoff`; объяснить, что не подтверждено |
| `SCOPE_VIOLATION` (запись вне scope, доказанно связанная с задачей) | FAIL | HALTED | NOT_VERIFIED | VALID | VOID | `blocked`; отдельная проверка безопасности |
| `LEASE_EXPIRED`, `SESSION_STALE`, `ASSIGN_FENCE_STALE` | FAIL | HALTED | NOT_VERIFIED | STALE | VOID | `blocked`; только новое разрешение координатора (для RESUME/2 — с личным G0) |
| `REF_DRIFT_UNEXPLAINED` (необъяснённое изменение не-целевого ref) | FAIL | HALTED | NOT_VERIFIED | STALE | VOID | `blocked`; расследование; **не** автоматически `SCOPE_VIOLATION` |

Примечание о порядке: в DESIGN_NOTE/3 R2 тройки записаны в разном порядке (в тексте `execution + verification + result`, в таблице `result; execution; verification`). Здесь каждое измерение вынесено в отдельный именованный столбец, а значения перенесены без изменений.

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

1. Нарушения схемы, авторизации или конфликт интересов (`SCHEMA_INVALID`, `CANONICALIZATION_ERROR`, `UNAPPROVED_BASE`, `AUTH_ATTESTATION_UNVERIFIED`, `CONFLICT_OF_INTEREST`) → `report_validity: INVALID`, поле `verdict` **отсутствует**. Check из такого отчёта не принимаются, даже если в них написано `PASS`.
2. Устаревший источник, доказательство, сессия, lease или токен (`STALE_SOURCE`, `STALE_EVIDENCE`, `EVIDENCE_DELETED`, `LEASE_EXPIRED`, `SESSION_STALE`, `ASSIGN_FENCE_STALE`, `REF_DRIFT_UNEXPLAINED`) → `STALE`, `VOID`.
3. Доказанное нарушение scope (`SCOPE_VIOLATION`) → `VALID`, `VOID`.
4. Хотя бы один обязательный check не `PASS` → `VALID`, `FAIL`.
5. `VALID`, `PASS` — только если все обязательные check `PASS` и ни один выполненный необязательный check не `FAIL`.

Допустимые пары: `INVALID` + (нет verdict); `STALE` + `VOID`; `VALID` + `PASS | FAIL | VOID`. Любая другая пара → `SCHEMA_INVALID`.

Отчёт с неверной схемой не получает принятого вердикта. Диагностику `INVALID` записывает внешний валидатор, а не сам отчёт. Выдавать `SCHEMA_INVALID` за продуктовый `FAIL` запрещено.

Workflow-статус меняет только координатор по политике владельца. QA не может перевести `handoff` в `done`.
