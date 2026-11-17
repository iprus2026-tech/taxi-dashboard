---
name: taxi-evidence-qa
description: Claude Code adapter for the canonical Taxi Dashboard skill at .agents/skills/taxi-evidence-qa/SKILL.md. Use when an assigned, independent QA session verifies HANDOFF evidence under docs/agents/PROTOCOL.md v1 - comment-body UTF-8 SHA-256 versus attachment raw-byte SHA-256, exact authorized URLs and head_sha permalinks, HTTP status, size and hash per file, 403 as NOT_VERIFIED, mismatch as FAIL, empty files by the empty SHA-256. Produces only QA-REPORT/RECEIPT drafts; no self-QA, implied PASS or proxy bypass.
---

# taxi-evidence-qa (адаптер Claude Code)

Это **тонкий адаптер**. Собственных правил в нём нет.

1. Прочитай целиком канонический файл **`.agents/skills/taxi-evidence-qa/SKILL.md`** из корня этого репозитория и выполняй **его**. Предусловие из этого файла — сначала `taxi-preflight`.
2. Сверь его SHA-256 с закреплённым ниже значением (`sha256sum`, либо SHA-256 байтов файла, полученных через GitHub). Если файл не найден, не читается или хэш не совпал, итог — `BLOCKED (canonical_skill_mismatch)`. Ничего не делай по памяти или по этому адаптеру и сообщи поручающему.
3. Если канонический файл расходится с `docs/agents/PROTOCOL.md` v1, прав v1. `docs/agents/v2/**` — `DRAFT / NOT ACTIVE`.

Закреплённый канонический файл:

```text
path: .agents/skills/taxi-evidence-qa/SKILL.md
sha256: 80267ce3e32a0beb21762c5d252e7e6f536768ee6758ad41bb1f3759e9d961dd
```

Особенности Claude Code, не меняющие процедуру:

- Фактический ID сессии бери из `get_session` (сервер `claude-code-remote`), поле `id`.
- Прокси облачной сессии может отвечать `403` на `github.com/user-attachments/...`, как в QA #60. Тогда файл получает `NOT_VERIFIED`, источник ответа — «прокси сессии». Повторных обходов и подмены источника нет.
- Если код или результат писала роль `claude-code`, это раскрывается. Свою работу эта сессия не проверяет (§7.6): при доказанной зависимости итог — `BLOCKED (not_independent)`. Общий аккаунт сам по себе даёт `NOT_VERIFIED (identity)`, а не BLOCKED.

Символические ссылки намеренно не используются: адаптер — обычный текстовый файл, поэтому он одинаково работает на Linux, macOS, Windows и Android/Termux.
