# Проектные Skills Taxi Dashboard (пилот TAXI-AGENT-SKILLS-01, hardening TAXI-AGENT-SKILLS-HARDEN-01 и -02)

**Действующая редакция — вторая hardening-замена:**

- Задача: `TAXI-AGENT-SKILLS-HARDEN-02` ([Issue #68](https://github.com/iprus2026-tech/taxi-dashboard/issues/68)) — третий, отдельный draft PR вместо замороженного PR #66
- SPEC/1: [#6942795142](https://github.com/iprus2026-tech/taxi-dashboard/issues/68#issuecomment-6942795142), `issue_spec_sha256` `53130953a5b425b8fc713274f4007321635f19ed1f6501197086fcf50c8efd16` (5867 байт)
- Личный OWNER G0: [#6943730960](https://github.com/iprus2026-tech/taxi-dashboard/issues/68#issuecomment-6943730960) (`target_branch: main`, `previous_pr_66: frozen_do_not_modify`, `original_pr_63: frozen_do_not_modify`)
- Base SHA: `32067e2c0626840b1b7fd56c250ac31bac3af3d1`
- Исходное содержимое шести файлов: commit `0cb5757c28e87a39e810162657bd38213a10c500` (HEAD PR #66), воспроизведён побайтно, затем узкие исправления трёх Codex P2 по §10
- Автор: `claude-code`, сессия `session_01UHQjyfK487x9yA1CgAYEN1`, [CLAIM #6943894075](https://github.com/iprus2026-tech/taxi-dashboard/issues/68#issuecomment-6943894075), [ASSIGN #6943949459](https://github.com/iprus2026-tech/taxi-dashboard/issues/68#issuecomment-6943949459)

**Первая hardening-замена (история, не переписывается):**

- Задача: `TAXI-AGENT-SKILLS-HARDEN-01` ([Issue #65](https://github.com/iprus2026-tech/taxi-dashboard/issues/65)), [PR #66](https://github.com/iprus2026-tech/taxi-dashboard/pull/66) — заморожен ([STOP_MERGE #6942687029](https://github.com/iprus2026-tech/taxi-dashboard/pull/66#issuecomment-6942687029)), не изменяется
- SPEC/1: [#6931019267](https://github.com/iprus2026-tech/taxi-dashboard/issues/65#issuecomment-6931019267), `issue_spec_sha256` `e435fc5aa51bf41e2398965d98ac2aa9180b68af6b35ca179316bc4fd6f54ac0`
- Личный OWNER G0: [#6938690743](https://github.com/iprus2026-tech/taxi-dashboard/issues/65#issuecomment-6938690743) (`target_branch: main`, `original_pr_63: frozen_do_not_modify`, `protocol_v2_activation: forbidden`)
- Base SHA: `32067e2c0626840b1b7fd56c250ac31bac3af3d1`
- Исходное содержимое шести файлов: commit `3abe539f3e450cf32fdf70dbe5009c519393c09a` (HEAD PR #63), затем узкие исправления по §8
- Автор: `claude-code`, сессия `session_01UHQjyeTJSiC2rXWYHp1iHR`, [CLAIM #6938800898](https://github.com/iprus2026-tech/taxi-dashboard/issues/65#issuecomment-6938800898), [ASSIGN #6938851208](https://github.com/iprus2026-tech/taxi-dashboard/issues/65#issuecomment-6938851208)
- Независимый QA PASS [#6942066669](https://github.com/iprus2026-tech/taxi-dashboard/issues/65#issuecomment-6942066669) и G2 [#6942477573](https://github.com/iprus2026-tech/taxi-dashboard/issues/65#issuecomment-6942477573) относятся **только** к `0cb5757c…` и эту редакцию не утверждают

**Исходный пилот (история, не переписывается):**

- Задача: `TAXI-AGENT-SKILLS-01` ([Issue #62](https://github.com/iprus2026-tech/taxi-dashboard/issues/62)), [PR #63](https://github.com/iprus2026-tech/taxi-dashboard/pull/63) — заморожен, не изменяется
- SPEC/1: [#6916718681](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6916718681), `issue_spec_sha256` `4d45eedd2f1e98a352ca5c0c76e24c124ae18ea42d090fd8640c4c110d16d2a8`
- Личный OWNER G0: [#6917071745](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6917071745) (`target_branch: main`, `protocol_v2_activation: forbidden`)
- Автор: `claude-code`, сессия `session_01UHQjybeDCCrdBiTRM2391C`, [ASSIGN #6918175341](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6918175341)
- Независимый QA PASS [#6927885500](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6927885500) и G2 [#6929501305](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6929501305) относятся **только** к `3abe539f…` и эту редакцию не утверждают

## 1. Статус

**Действующий и единственный нормативный протокол — `docs/agents/PROTOCOL.md` v1.** Каталог `docs/agents/v2/**` имеет статус **`DRAFT / NOT ACTIVE`** и этим пилотом не активируется. Skills ничего не добавляют к v1 и ничего в нём не отменяют. При расхождении прав v1, а расхождение — дефект Skill.

Skills — **процедурные справки, а не полномочия**:

- они не выдают G0, ASSIGN, RESUME, REASSIGN, G2 и G3;
- не делают merge и deploy;
- не меняют labels и статусы;
- не публикуют ничего в GitHub по своей инициативе;
- не составляют `OWNER-DECISION` за владельца.

Публиковать сообщения протокола агент может только по своему действующему поручению (ASSIGN или явное поручение человека) и только в форматах v1.

До независимого QA, личного OWNER G2 по точному HEAD и ручного merge эти файлы существуют только в ветке задачи. **Ни одна платформа не получает их автоматически.** Даже после merge они остаются справками и сами по себе ничего не запускают.

## 2. Состав

| Файл | Назначение | Нормативность |
|---|---|---|
| `.agents/skills/taxi-preflight/SKILL.md` | проверка предусловий: SPEC/SHA-256, G0 и `target_branch`, Base/main, CLAIM/ASSIGN и fencing сессии, lease, конфликты; режимы `READ_ONLY_PREFLIGHT`, `PRE_WRITE`, `PRE_HANDOFF`, `RECOVERY` | **канонический** |
| `.agents/skills/taxi-evidence-qa/SKILL.md` | независимая проверка доказательств: хэш тела комментария и хэш сырых байтов вложения, точные URL, HTTP/размер/хэш, `403 → NOT_VERIFIED`, несовпадение → `FAIL`, независимость, черновики QA-REPORT/RECEIPT | **канонический** |
| `.claude/skills/taxi-preflight/SKILL.md` | адаптер Claude Code: отсылает к каноническому файлу и закрепляет его SHA-256 | без собственных правил |
| `.claude/skills/taxi-evidence-qa/SKILL.md` | адаптер Claude Code: отсылает к каноническому файлу и закрепляет его SHA-256 | без собственных правил |
| `docs/agents/skills/README.md` | этот документ | справочный |
| `docs/agents/skills/TEST-CASES.md` | документальные read-only тест-кейсы по Issues #59/#60/#61/#62/#65/#68, синтетические негативные случаи и таблицы регрессии hardening (§8, §10) | справочный |

Исполняемых скриптов, внешних зависимостей, новых агентов, webhooks, GitHub Actions и runtime-подключений нет. Команды в тексте Skills (`git ls-remote`, `sha256sum`) — примеры для ручного выполнения разрешёнными в среде инструментами.

## 3. Защита от расхождения адаптеров

Адаптеры в `.claude/skills/` не копируют процедуру. Каждый адаптер:

1. указывает путь к каноническому файлу;
2. содержит его SHA-256;
3. требует `BLOCKED (canonical_skill_mismatch)`, если файл не найден или хэш не совпал.

Поэтому любое изменение канонического Skill без одновременного обновления закреплённого хэша в адаптере сразу видно. Тихо разойтись с каноном адаптер не может. Изменение канонического файла — это изменение кода задачи: нужны новая задача, SPEC, G0, ASSIGN, HANDOFF, QA и G2.

Символические ссылки **не используются**: на Windows и Android/Termux они ненадёжны, а Git на части систем хранит их как текстовые файлы. Адаптер — обычный текст с относительным путём от корня репозитория.

## 4. Обнаружение и вызов по платформам

Колонка «Проверено в пилоте» честно показывает, что подтверждено в этой сессии, а что — нет.

| Участник | Как найти Skill | Как вызвать | Проверено в пилоте |
|---|---|---|---|
| **Claude Code** (CLI, облачные сессии) | Каталог `.claude/skills/<name>/SKILL.md` — место проектных Skills в документации Claude Code. Файлы появятся в рабочей копии только после merge в `main` или при checkout ветки задачи. | Автоматически по `description` или явно: `/taxi-preflight`, `/taxi-evidence-qa`. Адаптер требует прочитать канонический файл. | **NOT_VERIFIED.** Обнаружение не проверялось: текущая сессия загружает Skills при старте, а новая сессия на этой ветке не запускалась. Разметка frontmatter проверена (`name`, `description`). |
| **Codex** | Каталог `.agents/skills/<name>/SKILL.md` предназначен для Codex по конвенции Agent Skills. | Автоматически, если Codex его поддерживает, или вручную: «прочитай `.agents/skills/taxi-preflight/SKILL.md` и выполни». | **NOT_VERIFIED.** В среде пилота Codex CLI не установлен. Автоматическое обнаружение не утверждается. Ручной вызов работает на любой платформе, которая читает файлы. |
| **GPT, координатор** (ChatGPT) | Доступа к файловой системе нет. Файл нужно передать: permalink на commit или вставка текста. | Вручную: дать ссылку на `.agents/skills/<name>/SKILL.md` на конкретном commit и попросить выполнить процедуру. Хэш файла сверить по permalink. | Автоматического обнаружения нет и не утверждается. |
| **DeepSeek Harness** | Нативная поддержка формата Skills не проверена. | Вручную: прочитать канонический файл из своей рабочей копии на нужном commit (`git show <sha>:.agents/skills/<name>/SKILL.md`) и выполнить. | **NOT_VERIFIED.** Автоматическое обнаружение не утверждается. |

Единый порядок для всех ролей: **сначала `taxi-preflight`**, затем работа по поручению. Для QA — затем `taxi-evidence-qa`. Если Skill недоступен, протокол v1 действует так же: Skill не обязателен, обязателен протокол.

## 5. Переносимость

- Формат Markdown с YAML frontmatter (`name`, `description`) — общий для Claude Code и конвенции Agent Skills. Других полей frontmatter нет, чтобы не зависеть от возможностей платформы.
- Процедуры не привязаны к ОС: проверки описаны как действия (прочитать, пересчитать, сравнить), а не как скрипты.
- Различия платформ — как узнать ID сессии и какими инструментами разрешено читать GitHub — указаны в Skill как варианты одного шага. Если способа нет, итог `NOT_VERIFIED`, догадок нет.
- Переносимость на конкретную платформу считается подтверждённой только после отдельной проверки на ней. В этом пилоте такой проверки нет.

## 6. Тесты

[`TEST-CASES.md`](TEST-CASES.md) содержит документальные проверки «вход → ожидаемый итог Skill» по реальным записям Issues #59, #60, #61 и #62, а также синтетические негативные случаи. Тесты выполняются **только чтением**:

- нельзя публиковать или повторять комментарии;
- нельзя скачивать production-файлы;
- нельзя менять исторические Issues.

Для истории не нужно повторно скачивать вложения: проверяется классификация уже записанных результатов.

## 7. Ограничения пилота

- Обнаружение Skills платформами не проверено ни для одной платформы (§4).
- Skills не исполнялись другой ролью. Самопроверка автора — не независимый QA. Для merge нужны отдельная QA-задача и личный OWNER G2 по точному HEAD.
- Общий аккаунт GitHub не подтверждает личность (v1 §0.1). Skills это ограничение не снимают.

## 8. Hardening по Issue #65: что исправлено и где

Исходные замечания — четыре непогашенных inline-замечания Codex P2 к PR #63 и четыре неблокирующих наблюдения F1–F4 независимого QA [#6927885500](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6927885500). Исторические комментарии, PR #63 и его ветка не изменялись.

| Замечание | Суть | Исправление | Кейсы |
|---|---|---|---|
| [Codex P2 #4592207775](https://github.com/iprus2026-tech/taxi-dashboard/pull/63#discussion_r4592207775) | после действительного RESUME `PRE_WRITE` всё ещё требовал исходный `claim_session` | `taxi-preflight` S6.1: **действующая сессия** по цепочке ASSIGN → действительные RESUME (§5.7, §8.2), в `PRE_WRITE` и `PRE_HANDOFF`; поддельный, отредактированный или устаревший RESUME игнорируется; устаревшая, дочерняя и неназначенная сессии → `STOP` | TC-19, TC-20, TC-21 |
| [Codex P2 #4592207785](https://github.com/iprus2026-tech/taxi-dashboard/pull/63#discussion_r4592207785) | S7 требовал lease до первого CLAIM, когда ASSIGN ещё нет | S7: `N/A (no_assignment)` в `READ_ONLY_PREFLIGHT` до ASSIGN; после ASSIGN или RESUME — точное сравнение `lease_until` (UTC, миллисекунды), при истечении `BLOCKED (lease_expired)` + `STOP`, без неявного продления; §4 — разрешённые `N/A` | TC-17, TC-18 |
| [Codex P2 #4592207795](https://github.com/iprus2026-tech/taxi-dashboard/pull/63#discussion_r4592207795) | фактическая base ветка PR не сравнивалась с `target_branch` G0 | `taxi-preflight` S5: `base.ref` PR = `target_branch` последнего действующего G0, перечитывается перед HANDOFF; иначе `BLOCKED (pr_target_mismatch)`, даже если ancestry PASS (§4.3 п.6, T43); `taxi-evidence-qa` E3 — то же в начале QA | TC-22, TC-23 |
| [Codex P2 #4592207802](https://github.com/iprus2026-tech/taxi-dashboard/pull/63#discussion_r4592207802) | безусловное «длина 0 → FAIL» отвергало законно пустые файлы | `taxi-evidence-qa` E6: 0 байт + ожидаемый `e3b0c442…b855` + нет требования непустоты → `PASS`; несовпадение байтов или хэша и явная непустота → `FAIL`; 403 и таймаут → `NOT_VERIFIED`; пустое тело ошибки — не артефакт | TC-24, TC-25 |
| F1 | TC-13: «non-blocking wording defect» — не цитата #61 | TC-13 цитирует #61 дословно: «Two non-blocking defects…», к TC-13 относится только пункт (a); вердикты #60 PARTIAL и #61 PASS сохранены | TC-13 |
| F2 | нет явной сверки G0 `base_sha` со SPEC, ровно одного `status:*`, зависимостей, base PR | S2: ровно один `status:*`, `depends_on` в `status:done`; S4: G0 `base_sha` = SPEC Base, иначе `BLOCKED (base_mismatch)`; S5: base PR (см. выше); проверки по режимам сохранены | TC-31, TC-23 |
| F3 | E3 без отдельной проверки `forbidden_paths`; E4 принимал любой 40-hex SHA | E3: каждый путь против каждого запрещённого шаблона, `scope_check: FAIL (forbidden_path)`; E4: permalink только на `head_sha` HANDOFF, иначе `FAIL (permalink_not_head)`; preflight S9 — `BLOCKED (forbidden_path)` | TC-27, TC-28 |
| F4 | нет детерминированного статуса ложной независимости | `taxi-evidence-qa` §2: `BLOCKED (not_independent)` **только** при доказанной зависимости; общий аккаунт или неизвестная личность — `NOT_VERIFIED (identity)`, а не независимость и не автоматический BLOCKED | TC-29, TC-30 |

Адаптеры `.claude/skills/*` закрепляют SHA-256 **новых** канонических файлов. Адаптер со старым хэшем из `3abe539f…` при новом каноне даёт `BLOCKED (canonical_skill_mismatch)` (TC-26).

## 9. Что доказано, что не проверено, что не запускалось

| Категория | Что входит | Статус |
|---|---|---|
| **Доказано документально** (чтение и сравнение текста) | правила Skills сверены с PROTOCOL v1; каждый кейс TC-01…TC-42 выведен из текста Skills и первичных комментариев; регрессия «до (`3abe539f…`) → после» для четырёх P2 и F1–F4 (TEST-CASES §E) и «до (`0cb5757c…`) → после» для трёх новых P2 (TEST-CASES §H); хэши адаптеров равны хэшам канонических файлов; frontmatter валиден | proved, только documentary |
| **NOT_VERIFIED** | автоматическое обнаружение Skills платформами Claude Code, Codex, DeepSeek Harness; у GPT-координатора обнаружения нет вовсе; личность авторов комментариев (общий аккаунт, §0.1) | не утверждается |
| **NOT_RUN** | реальное исполнение Skills другой ролью или на другой платформе; интеграция с runtime, ботами, Actions и агентами; скачивание вложений ради тестов; способ E5-G2 (Git objects API) в этой сессии не выполнялся; production, планшет, GPS | не выполнялось |

Самопроверка автора (в том числе однократное чтение G1 и загрузка HTML-просмотрщика для TC-36 и TC-37) — **не** независимый QA.

`docs/agents/PROTOCOL.md` v1 остаётся единственным нормативным протоколом. `docs/agents/v2/**` остаётся `DRAFT / NOT ACTIVE`. Эта редакция ничего не активирует.

## 10. Hardening-02 по Issue #68: что исправлено и где

Исходные замечания — три новых inline-замечания Codex P2 к PR #66 на HEAD `0cb5757c28e87a39e810162657bd38213a10c500`. PR #66, PR #63, их ветки, HANDOFF, QA-REPORT, RECEIPT и OWNER-DECISION не изменялись. Исправления §8 (четыре P2 к PR #63, F1–F4) сохранены без ослабления: TEST-CASES §H, строки R26–R27.

| Замечание | Суть | Исправление | Кейсы |
|---|---|---|---|
| [Codex P2 #4596961703](https://github.com/iprus2026-tech/taxi-dashboard/pull/66#discussion_r4596961703) | S6.1 безусловно сравнивал действующую сессию с фактической. До первого ASSIGN действующей сессии нет, поэтому первый CLAIM получал `STOP (session_not_assigned)`, хотя S7 уже давал `N/A` | `taxi-preflight` S6.1 «Применимость»: без единого `ASSIGN` от `agent: gpt` (или при явно прекращённой REASSIGN или RELEASE цепочке и снова `status:ready`) и только в `READ_ONLY_PREFLIGHT` → `N/A (no_assignment)`, ровно один `CLAIM/1`, затем `STOP`. При любом назначении S6.1 обязателен: чужая, устаревшая, fork-сессия и неоднозначный ASSIGN → `STOP`. В `PRE_WRITE`/`PRE_HANDOFF` без ASSIGN → `BLOCKED (assign_missing)`. §4: `N/A` разрешён для S6.1 и S7 по одному и тому же условию | TC-17, TC-32, TC-33 |
| [Codex P2 #4596961734](https://github.com/iprus2026-tech/taxi-dashboard/pull/66#discussion_r4596961734) | `taxi-evidence-qa` §0, §1 и §2 п.1 требовали `claim_session` исходного ASSIGN = эта сессия. QA-сессию, законно возобновлённую через RESUME, это блокировало | §0, §1, §2 п.1, E9 и §6 используют **действующую сессию** QA-задачи по цепочке `ASSIGN → RESUME…`, как `taxi-preflight` S6.1. Проверяются: сессия, SPEC, lease, роль, порядок, обрыв цепочки, право публикации из ASSIGN. Поддельный, отредактированный, отсутствующий, устаревший или истёкший RESUME → `STOP` или `BLOCKED`. RESUME не даёт независимости: RESUME на сессию автора → `BLOCKED (not_independent)` | TC-34, TC-35 |
| [Codex P2 #4596961721](https://github.com/iprus2026-tech/taxi-dashboard/pull/66#discussion_r4596961721) | загрузка permalink `github.com/…/blob/<head_sha>/<path>` отдаёт HTML-просмотрщик, а E6 требовал HTTP 200 для PASS. Итог — ложный FAIL или невозможный PASS | E4 проверяет **только адрес**, точно и без нормализации (`url_malformed`, `permalink_not_head`). Новый E5-G получает байты git-файла детерминированно по тем же `head_sha` и `path`: G1 — локальный объект git (`rev-parse`, `ls-tree`, `cat-file blob`, контроль `blob_id`), G2 — Git objects API (commit → tree → path → blob, контроль git-хэша). E5-A — вложения строго по точному URL. HTML-просмотрщик, raw-подмены, архивы, зеркала и рабочая копия запрещены. E6 различает вид источника, записывает происхождение и не требует HTTP для локального объекта git | TC-36…TC-42 |

Адаптеры `.claude/skills/*` закрепляют SHA-256 **новых** канонических файлов. Хэши редакции `0cb5757c…` (`4af7e921…70f1`, `80267ce3…61dd`) при новом каноне дают `BLOCKED (canonical_skill_mismatch)`, как в TC-26.
