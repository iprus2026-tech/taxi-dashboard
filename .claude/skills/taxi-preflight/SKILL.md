---
name: taxi-preflight
description: Claude Code adapter for the canonical Taxi Dashboard skill at .agents/skills/taxi-preflight/SKILL.md. Use before CLAIM, before the first write after ASSIGN, before HANDOFF, or when recovering an in-progress or blocked task under docs/agents/PROTOCOL.md v1. Read-only check of canonical SPEC/SHA-256, G0 and target_branch, Base/main, CLAIM/ASSIGN session fencing, lease and conflicts. Grants no G0, ASSIGN, G2/G3, merge or deploy.
---

# taxi-preflight (адаптер Claude Code)

Это **тонкий адаптер**. Собственных правил в нём нет.

1. Прочитай целиком канонический файл **`.agents/skills/taxi-preflight/SKILL.md`** из корня этого репозитория и выполняй **его**.
2. Сверь его SHA-256 с закреплённым ниже значением (`sha256sum`, либо SHA-256 байтов файла, полученных через GitHub). Если файл не найден, не читается или хэш не совпал, итог — `BLOCKED (canonical_skill_mismatch)`. Ничего не делай по памяти или по этому адаптеру и сообщи поручающему.
3. Если канонический файл расходится с `docs/agents/PROTOCOL.md` v1, прав v1. `docs/agents/v2/**` — `DRAFT / NOT ACTIVE`.

Закреплённый канонический файл:

```text
path: .agents/skills/taxi-preflight/SKILL.md
sha256: d41e817fbf333717b68694705794be704222221140383ee9ccc717f44c175969
```

Особенности Claude Code, не меняющие процедуру:

- Фактический ID сессии бери из `get_session` (сервер `claude-code-remote`), поле `id`.
- В облачной сессии GitHub читай через MCP-инструменты `mcp__github__*`. `gh` допустим только для поиска. Обходить прокси нельзя.
- Служебная ветка окружения (`claude/...`) не получает коммитов задачи. Ветку задачи определяет ASSIGN.

Символические ссылки намеренно не используются: адаптер — обычный текстовый файл, поэтому он одинаково работает на Linux, macOS, Windows и Android/Termux.
