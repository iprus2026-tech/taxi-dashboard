# AGENT-CONSULT Stage A — предложение формата и офлайн-верификатор

- Задача: `TAXI-AGENT-CONSULT-STAGE-A-01` (Issue #87)
- Основание: DESIGN_NOTE/1 (Issue #86, комментарий 6991948774) и G1 APPROVE (Issue #86, комментарий 7000037199)
- Статус: **NON-NORMATIVE / OFFLINE / DISABLED BY DEFAULT**

> Этот документ — **предложение**, а не часть действующего протокола.
> `docs/agents/PROTOCOL.md` (PROTOCOL v1) не меняется. Записи CONSULT-REQUEST/1,
> CONSULT-REPLY/1 и CONSULT-CLOSE/1 **нельзя** публиковать как сообщения v1,
> вставлять в живые задачи или использовать для изменения задач, labels, lease,
> гейтов или QA. Прямой обмен между агентами (Claude Code, DeepSeek и другими)
> не включается. Чтобы включить консультации в живых задачах, нужна отдельная
> задача: свой SPEC, G0, независимый QA и G2 владельца.

## 1. Что входит в Stage A

| Файл | Назначение |
|---|---|
| `docs/agents/consult/STAGE-A-PROPOSAL.md` | этот документ: формат, инварианты, коды |
| `tools/agent_consult/__init__.py` | пакет и флаги `ENABLED = False`, `LIVE_TRANSPORT = False`, `NORMATIVE = False` |
| `tools/agent_consult/verify.py` | разбор и сериализация записей, детерминированный верификатор |
| `tests/test_agent_consult.py` | синтетические регрессии (stdlib `unittest`) |

У прототипа нет транспорта. Он ничего не отправляет и ничего не читает по сети,
не пишет в GitHub, не работает с файлами, не читает переменные окружения и
токены, не запускает процессы и не исполняет текст записей. Функций вроде
`send`/`post`/`publish`/`relay`/`subscribe` нет; это проверяют тесты (§8).
Флаги в `__init__.py` — информационные константы: никакой код их не читает, и
способа включить живой режим в пакете нет.

Результат любой проверки — `Result(verdict, codes, effect)`:
- `verdict` ∈ `PASS` | `FAIL` | `NOT_VERIFIED`;
- `codes` — коды причин (§6);
- `effect` всегда `"NONE"`. Запись не даёт никаких прав: ни ASSIGN, ни lease,
  ни гейта, ни QA-вердикта, ни права на запись в ветку.

## 2. Режимы

| | COLLABORATIVE_DEV | INDEPENDENT_QA |
|---|---|---|
| Кто | подтверждённый исполнитель (сессия из ASSIGN) и отдельно авторизованные советники | независимый QA по замороженному HEAD |
| Консультации | только совет, асинхронно, без полномочий | **запрещены**: QA получает только HANDOFF и Issue (PROTOCOL v1 §7) |
| В верификаторе | единственный допустимый `mode` | `mode: INDEPENDENT_QA` → `FAIL MODE_FORBIDDEN` |

Кроме того (§5, `QA_FIREWALL`, `QA_INDEPENDENCE_CONFLICT`):
- советник не может быть QA-исполнителем этой задачи (по агенту или сессии);
- QA не может ни задавать вопрос, ни отвечать;
- агент, участвовавший в консультации по задаче и HEAD (как советник или
  заявитель), не может заявить себя независимым QA этого же HEAD. Сверка идёт и
  по роли агента, и по сессии, потому что сессии можно обновлять под общим
  аккаунтом.

## 3. Байтовый формат записи

Правила (проверяются, а **не исправляются**; неканонический вход отклоняется,
исторические комментарии никогда не переписываются):

- UTF-8 без BOM, Unicode NFC, только LF, без табуляций и управляющих символов
  (в том числе U+2028/U+2029/U+FEFF);
- первая строка — `NON-NORMATIVE-CONSULT-PROPOSAL/1` (не `agent-msg`, поэтому
  запись нельзя спутать с сообщением v1, а блок v1 отклоняется кодом `HEADER`);
- затем поля в фиксированном порядке (§4); скаляр — `ключ: значение`, список —
  `ключ:` и строки `- элемент`; пустой список — `- none`; элементы списков без
  повторов и отсортированы побайтно;
- без пробелов в начале и конце значений, без пустых строк; файл заканчивается
  ровно одним LF;
- canonical-проверка: `serialize(parse(raw)) == raw`, иначе `NON_CANONICAL`.

Ограничения:

| Что | Предел |
|---|---|
| вся запись | 16384 байт |
| свободный текст (`question`, `answer`, `conflict_disclosure`, `prior_participation`, `rationale`) | 4096 байт UTF-8, одна строка |
| прочие скаляры и элементы списков | 512 байт |
| элементов в списке | 16 |
| срок консультации по умолчанию (`draft_request`) | 60 минут |
| максимальный срок (`expires_at_utc − ts_utc`) | 4 часа |

`normalize_text()` (NFC, схлопывание пробелов) используется только при
составлении **новой** записи (`draft_request`), но не при проверке полученной.

Хэш записи: `content_sha256 = sha256(raw bytes)`.

## 4. Поля

Общие правила значений:

| Тип | Правило |
|---|---|
| `task_id` | `^TAXI-[A-Z0-9]+(-[A-Z0-9]+)*-[0-9]{2}(\.[0-9]+)?$` (как в PROTOCOL v1 §4.2) |
| `consult_id` | UUID v4 в нижнем регистре |
| агент | `claude-code`, `claude-design`, `deepseek-qa`, `gpt` (владелец не пишет консультации; `owner` → `ROLE_UNKNOWN`) |
| сессия | полный ID, `^[A-Za-z0-9][A-Za-z0-9._:-]{11,127}$`; в запросе `target_session` может быть `unassigned` |
| SHA | HEAD — 40 hex, SPEC и хэши — 64 hex, нижний регистр, полная длина |
| время | строго `YYYY-MM-DDTHH:MM:SSZ` (UTC, без долей секунды и смещений) |
| ссылка на код | `https://github.com/<repo>/blob/<40 hex>/<путь>[#Ln[-Lm]]`; ссылки на ветку (`blob/main/…`) недействительны |
| ссылка на комментарий | `https://github.com/<repo>/(issues|pull)/<n>#issuecomment-<id>` |
| путь | от корня репозитория, `/`, без `./`, `..` и ведущего `/` |

### 4.1 CONSULT-REQUEST/1

| Поле | Значение |
|---|---|
| `type` | `CONSULT-REQUEST` |
| `v` | `1` |
| `mode` | `COLLABORATIVE_DEV` |
| `task_id` | родительская задача |
| `consult_id` | UUID v4 |
| `source_agent`, `source_session` | заявитель = исполнитель из действующего ASSIGN |
| `target_agent`, `target_session` | советник из списка авторизованных |
| `source_ref` | permalink на файл при `source_head_sha` |
| `source_head_sha` | закреплённый полный HEAD |
| `spec_sha256` | `issue_spec_sha256`, утверждённый на G0 |
| `ts_utc`, `expires_at_utc` | время запроса и срок |
| `risk` | `LOW` / `MEDIUM` / `HIGH` |
| `scope` | `advisory-only` |
| `question` | вопрос (свободный текст) |
| `source_paths` | файлы, о которых вопрос; ⊆ Allowed paths задачи |
| `allowed_evidence` | список permalink'ов |

### 4.2 CONSULT-REPLY/1

| Поле | Значение |
|---|---|
| `type`, `v`, `mode`, `task_id`, `consult_id` | как в запросе |
| `source_agent`, `source_session` | отвечающий = `target_*` запроса |
| `target_agent`, `target_session` | = `source_*` запроса |
| `in_reply_to` | permalink комментария с запросом |
| `request_sha256` | `content_sha256` запроса |
| `source_head_sha`, `spec_sha256` | как в запросе |
| `ts_utc` | время ответа, в окне `[ts_utc, expires_at_utc)` запроса |
| `status` | `ANSWERED` / `CANNOT_ANSWER` / `NEEDS_COORDINATOR` |
| `risk`, `scope` | `scope: advisory-only` |
| `conflict_disclosure`, `prior_participation` | раскрытие конфликта и прежнего участия (`none` или текст) |
| `answer` | ответ (свободный текст) |
| `evidence` | permalink'и |

### 4.3 CONSULT-CLOSE/1 (только координатор)

| Поле | Значение |
|---|---|
| `type`, `v`, `task_id`, `consult_id` | |
| `source_agent`, `source_session` | `gpt` и известная сессия координатора |
| `request_ref`, `request_sha256` | ссылка на запрос и его хэш |
| `reply_ref`, `reply_sha256` | ссылка на ответ и хэш, либо оба `none` |
| `ts_utc` | время закрытия |
| `final_state` | `ACCEPTED_AS_CONTEXT` / `DECLINED` / `EXPIRED` / `CONFLICT` / `ESCALATED` |
| `scope` | `advisory-only` |
| `rationale` | обоснование |

Закрытие не влияет на G0–G3, lease, merge и deploy. `ACCEPTED_AS_CONTEXT`
требует принятого ответа и активного lease. `EXPIRED` допустим только после
срока запроса. Запрос без ответа никогда не превращается в согласие или
инструкцию.

## 5. Инварианты верификатора

Верификатор получает синтетический контекст родительской задачи
`TaskContext` (SPEC, HEAD, исполнитель, lease, Allowed/Forbidden paths,
советники, сессии координатора, назначения QA, ожидаемые логины,
флаги доказательств) и снимок комментария `CommentSnapshot` (URL,
`created_at`, `updated_at`, байты тела, хэш при снятии снимка, логин автора).

1. **Fail closed.** Флаги `authority_evidence`, `provenance_evidence`,
   `transport_evidence` по умолчанию `NOT_VERIFIED`; любой не `VERIFIED` флаг
   даёт как минимум `NOT_VERIFIED`. Неполный контекст — `CONTEXT_INVALID`.
   В ledger принимаются только записи с итогом `PASS`.
2. **Идентичность.** Общий логин (`iprus2026-tech`) не доказывает автора
   (PROTOCOL v1 §0.1) → `IDENTITY_SHARED_ACCOUNT` (`NOT_VERIFIED`). Нет
   ожидаемого логина → `IDENTITY_NOT_VERIFIED`. Другой логин →
   `IDENTITY_MISMATCH` (`FAIL`). Поля вроде `human_author` → `UNKNOWN_FIELD`.
3. **Дедупликация** по ключу `(type, task_id, source_session, consult_id,
   source_head_sha)`:
   - тот же комментарий с теми же байтами → `DUPLICATE_NOOP` (без эффекта);
   - те же байты в другом комментарии → `REPLAYED_COMMENT`;
   - тот же ключ с другими байтами → `CONFLICT`;
   - тот же `consult_id` с другим HEAD или сессией → `CONSULT_ID_REUSED`;
   - тот же URL с другими байтами → `CONFLICT`.
4. **Неизменность комментария.** `created_at ≠ updated_at` → `COMMENT_EDITED`;
   хэш тела ≠ хэшу снимка → `SNAPSHOT_MISMATCH`.
5. **Ответ ↔ запрос.** `in_reply_to`, `request_sha256`, `consult_id`,
   `task_id`, HEAD и SPEC совпадают с запросом; отвечает именно адресат;
   запрос уже принят в ledger.
6. **SPEC/HEAD.** Расхождение с живым контекстом → `SPEC_MISMATCH`,
   `HEAD_MISMATCH`; `source_ref` не при `source_head_sha` → `SOURCE_REF_MISMATCH`.
7. **Lease.** Истёк → `PARENT_LEASE_EXPIRED`; `BLOCKED`/`REASSIGNED`/`REVOKED` →
   `PARENT_LEASE_REVOKED`. Срок консультации не может выходить за lease
   (`EXPIRY_BEYOND_LEASE`) и не продлевает его.
8. **Срок консультации.** `CONSULT_EXPIRED`, `EXPIRY_OVER_CAP`,
   `EXPIRY_NOT_AFTER_TS`, `TS_IN_FUTURE`, `REPLY_OUTSIDE_WINDOW`; нет ответа
   до срока → `AWAITING_REPLY`, после срока → `CONSULT_TIMEOUT` (оба
   `NOT_VERIFIED`, никогда не «молчаливое да»).
9. **Пути и роли.** Пути вне Allowed или в Forbidden → `PATH_ESCALATION`;
   другая задача → `CROSS_TASK`; заявитель не исполнитель →
   `SOURCE_NOT_ASSIGNEE`; адресат не авторизован → `TARGET_NOT_AUTHORIZED`;
   сам себе → `SELF_CONSULT`; закрытие не координатором →
   `CLOSE_NOT_COORDINATOR`; `risk: HIGH` или `NEEDS_COORDINATOR` →
   `RISK_HIGH_ESCALATE` (`NOT_VERIFIED`, эскалация координатору).
10. **Недоверенный текст.** Свободный текст только классифицируется
    регулярными выражениями и никогда не исполняется:
    - управляющая лексика протокола (`type: ASSIGN`, `OWNER-DECISION`,
      `decision:`, `lease_until:`, «G2 approved», «merge now», продление lease,
      блок `agent-msg`) → `FORGED_AUTHORITY`;
    - prompt injection («ignore previous instructions», «you are now»,
      `</system>`, `__import__`, `exec(`, русские варианты) →
      `PROMPT_INJECTION`;
    - секреты (токены GitHub/Mapbox/AWS, приватные ключи, `api_key=…`,
      Bearer) во всей записи → `SECRET_DETECTED`;
    - координаты GPS, телефоны, e-mail, имена runtime-файлов
      (`driver_state.json`, `shift_history.json`, `yandex_day.json`) →
      `SENSITIVE_DATA`.

    Детекторы эвристические и намеренно строгие (ложное срабатывание даёт
    `FAIL`, а не пропуск). Главная гарантия не в них: запись никогда не
    исполняется и ничего не разрешает (`effect: NONE`).

## 6. Коды причин

Код может иметь суффикс `:деталь`. Серьёзность определяется по части до `:`.

- **FAIL:** `ENCODING`, `BOM`, `NOT_NFC`, `NOT_LF`, `CONTROL_CHAR`,
  `NON_CANONICAL`, `RECORD_TOO_LARGE`, `HEADER`, `MALFORMED_LINE`,
  `DUPLICATE_FIELD`, `UNKNOWN_FIELD`, `MISSING_FIELD`, `FIELD_ORDER`,
  `UNKNOWN_TYPE`, `BAD_VERSION`, `TEXT_TOO_LONG`, `FIELD_TOO_LONG`,
  `LIST_TOO_LONG`, `BAD_TASK_ID`, `BAD_CONSULT_ID`,
  `BAD_SESSION`, `BAD_SHA40`, `BAD_SHA64`, `BAD_TIMESTAMP`, `BAD_ENUM`,
  `BAD_PATH`, `INVALID_LINK`, `ROLE_UNKNOWN`, `MODE_FORBIDDEN`,
  `SCOPE_NOT_ADVISORY`, `TS_IN_FUTURE`, `EXPIRY_NOT_AFTER_TS`,
  `EXPIRY_OVER_CAP`, `EXPIRY_BEYOND_LEASE`, `CONSULT_EXPIRED`,
  `PARENT_LEASE_EXPIRED`, `PARENT_LEASE_REVOKED`, `CROSS_TASK`,
  `SPEC_MISMATCH`, `HEAD_MISMATCH`, `SOURCE_REF_MISMATCH`, `PATH_ESCALATION`,
  `SOURCE_NOT_ASSIGNEE`, `TARGET_NOT_AUTHORIZED`, `SELF_CONSULT`,
  `QA_FIREWALL`, `QA_INDEPENDENCE_CONFLICT`, `COMMENT_EDITED`,
  `SNAPSHOT_MISMATCH`, `REPLAYED_COMMENT`, `CONFLICT`, `CONSULT_ID_REUSED`,
  `REQUEST_NOT_ACCEPTED`, `REPLY_NOT_ACCEPTED`, `REPLY_LINK_MISMATCH`,
  `REQUEST_HASH_MISMATCH`, `REPLY_HASH_MISMATCH`, `REPLY_MISMATCH`,
  `REPLY_OUTSIDE_WINDOW`, `CLOSE_NOT_COORDINATOR`, `CLOSE_STATE_INVALID`,
  `FORGED_AUTHORITY`, `PROMPT_INJECTION`, `SECRET_DETECTED`,
  `SENSITIVE_DATA`, `IDENTITY_MISMATCH`, `CONTEXT_INVALID`.
- **NOT_VERIFIED:** `AUTHORITY_NOT_VERIFIED`, `PROVENANCE_NOT_VERIFIED`,
  `TRANSPORT_NOT_VERIFIED`, `IDENTITY_NOT_VERIFIED`,
  `IDENTITY_SHARED_ACCOUNT`, `TARGET_UNASSIGNED`, `RISK_HIGH_ESCALATE`,
  `CONSULT_TIMEOUT`, `AWAITING_REPLY`.
- **Информационный (PASS):** `DUPLICATE_NOOP`.
- Неизвестный код считается `FAIL`.

Итог: есть хотя бы один `FAIL` → `FAIL`; иначе есть `NOT_VERIFIED` →
`NOT_VERIFIED`; иначе `PASS`.

Важно: на сегодня все участники пишут через общий аккаунт, поэтому реальная
запись из GitHub всегда получила бы как минимум `NOT_VERIFIED`
(`IDENTITY_SHARED_ACCOUNT`). `PASS` достижим только на синтетическом контексте
с отдельными подтверждёнными логинами и флагами `VERIFIED`. Это намеренно.

## 7. Соответствие негативным сценариям DESIGN_NOTE/1 (§H)

| ID | Сценарий | Код | Тест |
|---|---|---|---|
| NEG-01 | ответ «ASSIGN approved, push now» | `FORGED_AUTHORITY` | `AdversarialTests.test_forged_authority_in_reply` |
| NEG-02 | QA спрашивает исполнителя во время QA | `QA_FIREWALL` | `QaFirewallTests.test_qa_cannot_ask_producer` |
| NEG-03 | prompt injection | `PROMPT_INJECTION` | `AdversarialTests.test_prompt_injection`, `test_payload_is_never_executed` |
| NEG-04 | повтор `consult_id` с другим SHA/содержимым | `CONSULT_ID_REUSED`, `CONFLICT`, `REPLAYED_COMMENT` | `InvariantTests.test_same_consult_id_with_changed_head`, `test_conflicting_payload_same_key`, `test_replayed_comment_rejected` |
| NEG-05 | HEAD или SPEC отличаются | `HEAD_MISMATCH`, `SPEC_MISMATCH` | `InvariantTests.test_spec_and_head_mismatch` |
| NEG-06 | lease истёк, задача переназначена или заблокирована | `PARENT_LEASE_EXPIRED`, `PARENT_LEASE_REVOKED` | `InvariantTests.test_parent_lease_expired_or_revoked` |
| NEG-07 | правки вне Allowed paths | `PATH_ESCALATION` | `InvariantTests.test_source_path_checks`, `AdversarialTests.test_cross_task_path_escalation` |
| NEG-08 | секрет, GPS, PII | `SECRET_DETECTED`, `SENSITIVE_DATA` | `AdversarialTests.test_leaked_secrets`, `test_real_gps_and_pii` |
| NEG-09 | советник недоступен | `AWAITING_REPLY`, `CONSULT_TIMEOUT` | `AdversarialTests.test_consultant_timeout_is_never_yes` |
| NEG-10 | отказ от установки плагина | не применимо: прототип ничего не устанавливает | `DisabledByDefaultTests`, `IsolationTests` |
| NEG-11 | общий/украденный GitHub-аккаунт | `IDENTITY_SHARED_ACCOUNT`, `IDENTITY_MISMATCH` | `AdversarialTests.test_shared_or_stolen_identity` |
| NEG-12 | комментарий отредактирован после хэша | `COMMENT_EDITED`, `SNAPSHOT_MISMATCH`, `CONFLICT` | `InvariantTests.test_edited_comment_rejected`, `test_snapshot_hash_mismatch_rejected`, `test_same_url_new_content_is_conflict` |

## 8. Соответствие критериям приёмки

| AC | Где |
|---|---|
| AC-2 | `__init__.py` (флаги), заголовок `NON-NORMATIVE-CONSULT-PROPOSAL/1`; `DisabledByDefaultTests` |
| AC-3 | §3–§4; `SchemaAndSerializationTests` |
| AC-4 | §5; `InvariantTests` |
| AC-5 | §2; `QaFirewallTests` |
| AC-6 | §5 п.10, §7; `AdversarialTests` |
| AC-7 | `IsolationTests`: статический разбор импортов и вызовов (только `hashlib`, `re`, `unicodedata`, `dataclasses`, `datetime`, `typing`; нет `open`/`eval`/`exec`/`os`/`socket`/`subprocess`/`environ`); запуск под запретом сокетов, `open`, `os.open`, `os.system`, `subprocess.Popen`; фикстуры и ledger только во временном каталоге вне репозитория; `setUpModule`/`tearDownModule` сверяют, что `.github`, `app.py`, `docs/agents/PROTOCOL.md`, `docs/agents/v2`, `static`, `templates` не изменились и runtime-файлы не появились |

## 9. Запуск

Из корня репозитория, только стандартная библиотека Python 3.10+:

```bash
python3 -m unittest tests.test_agent_consult -v
```

## 10. Чего здесь нет

- Публикации записей в GitHub, relay, MCP-инструмента, подписок агентов.
- Изменений PROTOCOL v1, задач, labels, веток, QA и других агентов.
- Чтения production-данных, GPS, планшета или ПК.
- Включения CONSULT в живых задачах. Это требует отдельной задачи с SPEC,
  G0, независимым QA и G2 владельца.
