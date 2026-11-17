---
name: taxi-preflight
description: Claude Code adapter for the canonical Taxi Dashboard skill at .agents/skills/taxi-preflight/SKILL.md. Use before CLAIM, before the first write after ASSIGN, before HANDOFF, or when recovering an in-progress or blocked task under docs/agents/PROTOCOL.md v1. Read-only check of canonical SPEC/SHA-256, G0, base_sha and target_branch, Base/main, actual PR base, the effective session from ASSIGN/RESUME, lease once assigned, and conflicts. Grants no G0, ASSIGN, G2/G3, merge or deploy.
---

# taxi-preflight (адаптер Claude Code)

Это **тонкий адаптер**. Собственных правил в нём нет.

1. Прочитай целиком канонический файл **`.agents/skills/taxi-preflight/SKILL.md`** из корня этого репозитория и выполняй **его**.
2. Сверь его SHA-256 с закреплённым ниже значением (`sha256sum`, либо SHA-256 байтов файла, полученных через GitHub). Если файл не найден, не читается или хэш не совпал, итог — `BLOCKED (canonical_skill_mismatch)`. Ничего не делай по памяти или по этому адаптеру и сообщи поручающему.
3. Если канонический файл расходится с `docs/agents/PROTOCOL.md` v1, прав v1. `docs/agents/v2/**` — `DRAFT / NOT ACTIVE`.

Закреплённый канонический файл:

```text
path: .agents/skills/taxi-preflight/SKILL.md
sha256: d55f6e55c94fbb98ad92a74a611b43b3e4a23d899b2a47b21ced58c5a3288b5f
```

Особенности Claude Code, не меняющие процедуру:

- Фактический ID сессии бери из `get_session` (сервер `claude-code-remote`), поле `id`. Сравнение с действующей сессией и его применимость определяет канонический шаг S6.1: до первого ASSIGN в `READ_ONLY_PREFLIGHT` это `N/A (no_assignment)`, а при любом назначении работать можно, только если `id` равен действующей сессии.
- В облачной сессии GitHub читай через MCP-инструменты `mcp__github__*`. `gh` допустим только для поиска. Обходить прокси нельзя. Base ветку PR бери из `mcp__github__pull_request_read`, поле `base.ref`.
- Служебная ветка окружения (`claude/...`) не получает коммитов задачи. Ветку задачи определяет ASSIGN, а после RESUME — ASSIGN вместе с действительным RESUME.

Символические ссылки намеренно не используются: адаптер — обычный текстовый файл, поэтому он одинаково работает на Linux, macOS, Windows и Android/Termux.
