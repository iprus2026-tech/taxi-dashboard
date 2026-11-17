---
name: taxi-evidence-qa
description: Claude Code adapter for the canonical Taxi Dashboard skill at .agents/skills/taxi-evidence-qa/SKILL.md. Use when the effective independent QA session (ASSIGN or valid coordinator RESUME) verifies HANDOFF evidence under docs/agents/PROTOCOL.md v1 - comment-body UTF-8 SHA-256 versus attachment raw-byte SHA-256, head_sha permalinks checked as addresses with git bytes from verified git objects (not the HTML viewer), provenance, size and hash per file, 403 as NOT_VERIFIED, mismatch as FAIL, empty files by the empty SHA-256. Produces only QA-REPORT/RECEIPT drafts; no self-QA, implied PASS or proxy bypass.
---

# taxi-evidence-qa (адаптер Claude Code)

Это **тонкий адаптер**. Собственных правил в нём нет.

1. Прочитай целиком канонический файл **`.agents/skills/taxi-evidence-qa/SKILL.md`** из корня этого репозитория и выполняй **его**. Предусловие из этого файла — сначала `taxi-preflight`.
2. Сверь его SHA-256 с закреплённым ниже значением (`sha256sum`, либо SHA-256 байтов файла, полученных через GitHub). Если файл не найден, не читается или хэш не совпал, итог — `BLOCKED (canonical_skill_mismatch)`. Ничего не делай по памяти или по этому адаптеру и сообщи поручающему.
3. Если канонический файл расходится с `docs/agents/PROTOCOL.md` v1, прав v1. `docs/agents/v2/**` — `DRAFT / NOT ACTIVE`.

Закреплённый канонический файл:

```text
path: .agents/skills/taxi-evidence-qa/SKILL.md
sha256: 267cebfa1d4839134ebd8eb2268cf2cf9ab700486c909263796ebe6ed9f9aeb8
```

Особенности Claude Code, не меняющие процедуру:

- Фактический ID сессии бери из `get_session` (сервер `claude-code-remote`), поле `id`. Он должен быть равен действующей сессии QA-задачи по цепочке ASSIGN → RESUME из канонического файла, а не обязательно исходному `claim_session`.
- Байты файлов в git — способами канонического шага E5-G (`git cat-file blob <head_sha>:<path>` после `git fetch` или Git objects API через `mcp__github__*`), а не загрузкой страницы `github.com/…/blob/…`.
- Прокси облачной сессии может отвечать `403` на `github.com/user-attachments/...`, как в QA #60. Тогда файл получает `NOT_VERIFIED`, источник ответа — «прокси сессии». Повторных обходов и подмены источника нет.
- Если код или результат писала роль `claude-code`, это раскрывается. Свою работу эта сессия не проверяет (§7.6): при доказанной зависимости итог — `BLOCKED (not_independent)`. Общий аккаунт сам по себе даёт `NOT_VERIFIED (identity)`, а не BLOCKED.

Символические ссылки намеренно не используются: адаптер — обычный текстовый файл, поэтому он одинаково работает на Linux, macOS, Windows и Android/Termux.
