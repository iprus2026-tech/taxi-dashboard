# v2 — Канонический пример RESUME/2 (закреплённые байты)

> **Статус: `DRAFT / NOT ACTIVE`.** Пример **синтетический**: он не является реальным `RESUME`, `CLAIM`, `ASSIGN`, G0 или доказательством работы валидатора и не даёт никаких прав. См. [README.md](README.md).

Покрывает: **AC-6** (полный канонический пример RESUME/2 с одним завершающим LF, длиной в байтах и пересчитанным SHA-256) и часть **AC-7** (lease PT12H).

---

## 1. Закреплённое значение

| Параметр | Значение |
|---|---|
| Файл (нормативные байты) | [`fixtures/resume2-canonical-pt12h.txt`](fixtures/resume2-canonical-pt12h.txt) |
| Длина | **757 байт** (только ASCII, это подмножество UTF-8) |
| Строк | 24: строка-заголовок `agent-msg` + 23 уникальных ключа в порядке [LIFECYCLE.md §6.3](LIFECYCLE.md) |
| Переводы строк | только LF, ровно один завершающий LF, без пустых строк, без CR, BOM и табуляций |
| **SHA-256** | **`55709c807e386edf0a58edf558801b00aa0856c3954123a938d5b1e5a49aaaa6`** |
| Источник | [PRE_G0_CONDITIONS_NOTE/1 #6831064801](https://github.com/iprus2026-tech/taxi-dashboard/issues/26#issuecomment-6831064801), C3 |
| Утверждено | личным [OWNER G0 #6831274083](https://github.com/iprus2026-tech/taxi-dashboard/issues/26#issuecomment-6831274083): `resume2_fixture_bytes: 757`, `resume2_fixture_sha256: 55709c80…aaaa6` |

Нормативны **байты файла**. Блок ниже — отображение для чтения. Канонические байты — это содержимое между строками fence, включая LF перед закрывающим fence ([LIFECYCLE.md §1](LIFECYCLE.md)):

```agent-msg
agent-msg
type: RESUME
v: 2
task: TAXI-PROTOCOL-EXAMPLE-01
agent: gpt
coordinator_session: synth-coord-0001
assignee: deepseek-qa
session: synth-reviewer-0002
ts: 2026-11-12T15:00:00.000Z
owner_decision_ref: 12345670
claim_ref: 12345672
previous_assign_ref: 12345671
issue_spec_sha256: 1af6f8e4148697a85f6970ac9fb98bf0bde97a543203a1d4a77cb5e8265fe559
base_sha: 48b0454d3b68f90e7687bd00b2ccc5a9318f6d70
target_branch: main
source_ref: refs/heads/main
source_sha: 48b0454d3b68f90e7687bd00b2ccc5a9318f6d70
task_role: EVIDENCE_REVIEWER
branch: none
last_artifact_ref: none
last_artifact_updated_at: none
last_artifact_body_sha256: none
refs_snapshot_sha256: 032e90d80bbec3b3c125886c50216d059d306ebd9101fee1a7a1a728cdedd47c
lease_until: 2026-11-13T03:00:00.000Z
```

## 2. Синтетический контекст, в котором пример валиден

Пример проверяется против вымышленного контекста. В реальном событии каждая ссылка должна существовать и проходить проверки [LIFECYCLE.md §6.2](LIFECYCLE.md).

| Элемент контекста | Синтетическое значение |
|---|---|
| Задача | `TAXI-PROTOCOL-EXAMPLE-01` |
| Утверждённая SPEC/2 | [`fixtures/spec2-example-499.txt`](fixtures/spec2-example-499.txt), 499 байт, `1af6f8e4148697a85f6970ac9fb98bf0bde97a543203a1d4a77cb5e8265fe559` |
| Личный G0 для этого RESUME/2 | комментарий `12345670`: `approved_spec_sha256` = хэш выше; `note` содержит `target_branch: main`, `resume_of_comment_id: 12345671`, `new_session: synth-reviewer-0002`, `task_role: EVIDENCE_REVIEWER`, `resume2_lease_duration: PT12H`, `approve_one_RESUME/2: true` |
| Новый CLAIM/2 | комментарий `12345672`, `session: synth-reviewer-0002`, `agent: deepseek-qa` |
| Последний действующий токен | комментарий `12345671` (ASSIGN/2), не вытеснен |
| Сессия координатора | `synth-coord-0001` |
| Прежние артефакты | нет (тройка `last_artifact_*` = `none`) |
| Снимок refs | [`fixtures/refs-snapshot-example.txt`](fixtures/refs-snapshot-example.txt), 78 байт, `032e90d80bbec3b3c125886c50216d059d306ebd9101fee1a7a1a728cdedd47c` |
| Lease | `ts` `2026-11-12T15:00:00.000Z` + PT12H = `2026-11-13T03:00:00.000Z` |

Внимание: `issue_spec_sha256` примера (`1af6f8e4…`) — хэш **синтетической SPEC/2**. Это не хэш реальной SPEC/1 задачи #26 (`1239d989…`).

## 3. Как воспроизвести

Из корня клона, на коммите HANDOFF:

```bash
wc -c docs/agents/v2/fixtures/resume2-canonical-pt12h.txt
```

```bash
sha256sum docs/agents/v2/fixtures/resume2-canonical-pt12h.txt
```

Ожидается `757` и `55709c807e386edf0a58edf558801b00aa0856c3954123a938d5b1e5a49aaaa6`. Файлы в `fixtures/` помечены `-text` ([`.gitattributes`](.gitattributes)), чтобы Git не менял в них переводы строк. Если `git config core.autocrlf` включён, проверяйте байты через `git show <commit>:<path> | sha256sum`.

Независимо от репозитория те же байты можно получить из блока `agent-msg` комментария [#6831064801](https://github.com/iprus2026-tech/taxi-dashboard/issues/26#issuecomment-6831064801): JSON-декодированное `body` → содержимое между строками fence. Такая проверка подтверждает только декодированный текст ([EVIDENCE.md §3](EVIDENCE.md)).

## 4. Связь с ранними вариантами

| Вариант | Байт | SHA-256 | Статус |
|---|---|---|---|
| DESIGN_ERRATUM/1 R4, lease +24 ч (`lease_until: 2026-11-13T15:00:00.000Z`) | 757 | `515c1d2dc4a1a337a31c6ac9fc5bc376eeb5f582f46c57b621818590c3693491` | **исторический**. Этот хэш посчитал DeepSeek в [REVIEW_MEMO/4](https://github.com/iprus2026-tech/taxi-dashboard/issues/24#issuecomment-6829357927) как ненормативный. По политике PT12H этот пример **отвергается** (`fixtures/negative/sem-03-lease-24h-erratum.txt`) |
| C3 / G0 #6831274083, lease +12 ч | 757 | `55709c807e386edf0a58edf558801b00aa0856c3954123a938d5b1e5a49aaaa6` | **нормативный** |

Варианты отличаются только значением `lease_until`.

## 5. Чем пример не является

- Он не даёт права на работу и не является fencing-токеном: числовые ID вымышлены.
- Он не доказывает работу парсера или валидатора v2: их ещё нет, это отдельная будущая задача.
- Он не заменяет личный G0 владельца, который нужен для **каждого** реального RESUME/2.
