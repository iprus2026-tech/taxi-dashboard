# v2 — Профили работ, роли, SPEC/2 и проверки без ветки

> **Статус: `DRAFT / NOT ACTIVE`.** Документ входит в нормативный контракт протокола v2 (`docs/agents/v2/`), который **не активирован**. Действует `docs/agents/PROTOCOL.md` v1. Порядок активации и границы этапа описаны в [README.md](README.md).

Покрывает: **AC-1** (раздельные профили), **AC-3** (NO_BRANCH_READ_ONLY и обязательная ветка CODE_CHANGE).

Ключевые слова «ДОЛЖЕН», «НЕ ДОЛЖЕН», «ЗАПРЕЩЕНО» и «ДОПУСКАЕТСЯ» в документах v2 нормативные. Идентификаторы полей, значений и reason_code пишутся латиницей точно как указано и регистрозависимы.

---

## 1. Два корневых профиля

| Свойство | `CODE_CHANGE/1` | `READ_ONLY_EVIDENCE_QA/1` |
|---|---|---|
| Git-ветка задачи | **ОБЯЗАТЕЛЬНА**, реальный ref `agent/<agent>/<task-id-lowercase>` от `base_sha` | **ЗАПРЕЩЕНА**, литерал `branch: none` |
| `branch_policy` в SPEC/2 | `REQUIRED` | `FORBIDDEN` |
| `allowed_paths` | непустой список путей (не `- none`) | ровно `- none` |
| Запись в файлы, коммиты, PR | только в своей ветке и только в `allowed_paths` | запрещена |
| Результат | `HANDOFF/2` с `head_sha` и `changed_files` (правила v1 §6.2–§6.4 сохраняются без ослабления) | `HANDOFF/2`, `QA-REPORT/2` или `REVIEW_MEMO/2` только как текстовые комментарии Issue |
| Проверка HEAD | `git ls-remote origin <branch>` = `head_sha` до и после QA (v1 §6.4) | проверки источника §5 (без ветки) |
| Восстановление после обрыва | процедура v1 §8.2 по HEAD ветки; `RESUME/2` **неприменим** | только `RESUME/2` с личным G0 владельца ([LIFECYCLE.md §6](LIFECYCLE.md)) |
| Гейты | G0; G2 перед merge; G3 перед deploy | G0; G2/G3 неприменимы (нечего мержить) |

### 1.1 Инвариант неприсваивания привилегий (AC-1)

1. Профиль задачи — поле `work_profile` в канонической SPEC/2. Оно входит в `issue_spec_sha256` и утверждается владельцем на G0. Агент и координатор **НЕ ДОЛЖНЫ** выбирать, менять или «дополнять» профиль после G0. Смена профиля означает новую SPEC/2 и новый G0.
2. Исключения профиля `READ_ONLY_EVIDENCE_QA/1` (отсутствие ветки, `branch: none`, `changed_files: []`, проверка по `source_sha` вместо `head_sha`) **никогда** не применяются к задаче `CODE_CHANGE/1`. Задача `CODE_CHANGE/1` без реального ref ветки → `BLOCKED`, причина `UNAPPROVED_BASE` (кейс `NEG-AC3-01` в [TEST-CASES.md](TEST-CASES.md)).
3. Права `CODE_CHANGE/1` (создание ref, commit, PR, запись файлов) **никогда** не переносятся в задачу `READ_ONLY_EVIDENCE_QA/1`, даже если тот же агент или та же сессия параллельно ведёт code-задачу. Назначение привязано к кортежу `(repo, task_id, session, assign_ref)` и не переходит между задачами.
4. Задача имеет ровно один профиль и ровно одну роль. Комбинированные профили не определены. Задача, которой нужны обе возможности, делится на две задачи с отдельными SPEC/2 и G0.

### 1.2 Роли внутри `READ_ONLY_EVIDENCE_QA/1`

Поле `task_role` (входит в SPEC/2, взаимоисключающее, выбирается владельцем на G0):

| `task_role` | Что делает | Что публикует | Чего не делает |
|---|---|---|---|
| `EVIDENCE_EXECUTOR` | читает утверждённые источники, собирает доказательства | один `HANDOFF/2` (с инвентарём и явными недоступными входами) | не заявляет независимый QA |
| `EVIDENCE_REVIEWER` | проверяет чужой `HANDOFF/2` или дизайн | `QA-REPORT/2` или явно консультативный `REVIEW_MEMO/2` | не проверяет собственную работу |
| `DESIGNER` | готовит проектный текст | `DESIGN_NOTE/2` | не сертифицирует свой дизайн; проверку делает отдельная задача `EVIDENCE_REVIEWER` |

Для `CODE_CHANGE/1` поле `task_role` имеет единственное допустимое значение `IMPLEMENTER`.

`REVIEW_MEMO/2` — консультативный документ, а не замаскированный `QA-REPORT/2`. Отдельная роль агента Claude Design (Issue #25) этим документом **не вводится**: роль `DESIGNER` здесь — роль задачи, а не новый участник.

### 1.3 `allowed_actions` (закрытый словарь)

Токены: `repo:read`, `issue_comment:create`, `issue:metadata_update`, `git_ref:create`, `git_ref:update`, `git_commit:create`, `pr:create`.

- Список сортируется побайтно, без повторов; пустой список записывается ровно как `- none` и не может сочетаться с токенами.
- При `branch_policy: FORBIDDEN` **ЗАПРЕЩЕНЫ** `git_ref:create`, `git_ref:update`, `git_commit:create`, `pr:create` и любая запись в файлы. Такая SPEC/2 недействительна (`SCHEMA_INVALID`).
- При `branch_policy: REQUIRED` обязательны `git_ref:create` и `git_commit:create`. `pr:create` даёт право только на **draft** PR (v1 §1).
- Токен не выдаёт учётных данных, сетевого доступа, гейтов владельца или доступа к другим репозиториям. Новый токен требует новой версии схемы.

---

## 2. Каноническая форма `TAXI-ISSUE-SPEC/2`

SPEC/2 — **новая версия**. Она никогда не выводится из SPEC/1 и требует собственного G0. SPEC/1 по-прежнему проверяется только правилами v1 §4.2.

### 2.1 Байтовые правила

Те же, что в v1 §4.2: UTF-8 без BOM, Unicode NFC (только для текста спецификации), только LF, без табуляций, без пустых строк, без пробелов в начале и конце строк (кроме префикса `- ` у элементов списка), ровно один завершающий LF. `issue_spec_sha256` = SHA-256 этих байтов.

### 2.2 Порядок полей (точный)

```text
TAXI-ISSUE-SPEC/2
task_id          — регулярное выражение v1 §4.2
depends_on       — список Task ID, сортировка побайтно, пусто → "- none"
work_profile     — CODE_CHANGE/1 | READ_ONLY_EVIDENCE_QA/1
task_role        — IMPLEMENTER | EVIDENCE_EXECUTOR | EVIDENCE_REVIEWER | DESIGNER
base_sha         — 40 hex, нижний регистр
target_branch    — полное имя ветки
source_ref       — refs/heads/<branch> (§2.4)
source_sha       — 40 hex, нижний регистр
branch_policy    — REQUIRED | FORBIDDEN
evidence_policy  — ISSUE_TEXT_LF/1 | none
allowed_actions  — список (§1.3)
allowed_paths    — список; для FORBIDDEN ровно "- none"
forbidden_paths  — непустой список
acceptance       — AC-1..AC-n
gates            — подмножество G0-intake, G1-design, G2-merge, G3-deploy в этом порядке
```

Каждый список выводится всегда, даже если он пуст (`- none`).

Допустимые сочетания: `CODE_CHANGE/1` ↔ `IMPLEMENTER` ↔ `REQUIRED`; `READ_ONLY_EVIDENCE_QA/1` ↔ {`EVIDENCE_EXECUTOR`, `EVIDENCE_REVIEWER`, `DESIGNER`} ↔ `FORBIDDEN`. Любое другое сочетание → `SCHEMA_INVALID`.

### 2.3 Зависимости и переход в `ready`

`depends_on` содержит только канонические Task ID: без номеров Issues, повторов, циклов, неизвестных задач и зависимости задачи от самой себя. Каждая зависимость соответствует ровно одному Issue в этом репозитории. Перед переходом в `ready` и ещё раз перед `ASSIGN/2` и `RESUME/2` координатор заново читает каждую зависимость и подтверждает `status:done`. Статусы `handoff`, `owner-gate` и `blocked` не засчитываются.

### 2.4 `source_ref` и `source_sha`

- `source_ref` — ровно `refs/heads/<branch>`. `<branch>` состоит из непустых сегментов через `/`, каждый сегмент соответствует `[A-Za-z0-9][A-Za-z0-9_-]*`, общая длина `<branch>` не больше 128 байт ASCII. Теги, wildcard, точки, выражения коммитов и URL запрещены.
- Все байты источника читаются по `source_sha`, а не по изменяемому имени ветки.
- `base_sha` (эталон задачи и защищённых файлов) и `source_sha` (коммит, по которому читаются доказательства) — **разные поля**. Они могут различаться только с явного одобрения владельца в SPEC/2. Автоматически приравнивать их запрещено.
- `source_repo` по умолчанию — репозиторий задачи. Другой репозиторий требует новой схемы и разрешения владельца.

### 2.5 `target_branch`

В SPEC/2 хэшированное значение `target_branch` — **единственный** источник целевой ветки. Та же строка `target_branch: <имя>` ДОЛЖНА присутствовать в `note` личного G0 и совпадать байт в байт. Расхождение или отсутствие строки → `UNAPPROVED_BASE`, `ASSIGN/2` и `RESUME/2` не выдаются. Смена целевой ветки — только через новую SPEC/2 и новый G0.

### 2.6 Проверочный вектор SPEC/2

Файл [`fixtures/spec2-example-499.txt`](fixtures/spec2-example-499.txt): **499 байт** ASCII, один завершающий LF, SHA-256 `1af6f8e4148697a85f6970ac9fb98bf0bde97a543203a1d4a77cb5e8265fe559`. Это синтетический пример (`TAXI-PROTOCOL-EXAMPLE-01`), а не утверждённая спецификация. Вектор на 480 байт (`02e19f6d…`) из DESIGN_NOTE/2 §B — исторический и ненормативный.

---

## 3. Base SHA, целевая ветка и ancestry

1. `base_sha` ДОЛЖЕН существовать и быть предком текущей `origin/<target_branch>` в момент `ASSIGN/2` и `RESUME/2`: `git merge-base --is-ancestor <base_sha> origin/<target_branch>` возвращает 0.
2. Fast-forward `target_branch` после G0 сам по себе **не** делает `base_sha` недействительным. `base_sha` не «прокручивается» вперёд: переход на новую базу — только новая SPEC/2 и G0 (как v1 §4.3 п.7).
3. Rewind, удаление или переписывание `target_branch` (база перестала быть предком или недоступна) → `STALE_SOURCE`, задача `blocked`.

---

## 4. `CODE_CHANGE/1`: ветка обязательна

1. Ветка `agent/<agent>/<task-id-lowercase>` создаётся **только после** `ASSIGN/2`, строго от `base_sha`, и только сессией из `ASSIGN/2`.
2. `HANDOFF/2` для `CODE_CHANGE/1` содержит реальные `branch` и `head_sha`. `changed_files` = в точности `git diff --name-only <base_sha>..<head_sha>`, каждый путь ⊆ `allowed_paths` и ∉ `forbidden_paths`. `sha256` каждого файла = `git show <head_sha>:<path> | sha256sum`, URL — permalink на commit SHA (правила v1 §6.2–§6.3).
3. Правило v1 §6.4 (устаревший HANDOFF) действует без исключений: любой новый commit, force-push или rebase после HANDOFF делает его недействительным навсегда.
4. Отсутствие ветки, ветка с другим именем или ветка не от `base_sha` → задача `blocked`, причина `UNAPPROVED_BASE`. Профиль `READ_ONLY_EVIDENCE_QA/1` **не может** служить оправданием.

---

## 5. `READ_ONLY_EVIDENCE_QA/1`: проверки NO_BRANCH_READ_ONLY (AC-3)

Задача без ветки не может проверяться через HEAD ветки, поэтому вместо v1 §6.4 исполнитель и проверяющий выполняют **одинаковый набор проверок до и после** работы. Набор `[S1..S6]` выполняется дважды: `before` (до первого чтения источника) и `after` (после последней проверки, перед публикацией результата).

| # | Проверка | Ожидание | При нарушении |
|---|---|---|---|
| S1 | Заново построить SPEC/2 из текущего Issue и пересчитать `issue_spec_sha256` | = `approved_spec_sha256` последнего действующего личного G0 | `UNAPPROVED_BASE` → `INVALID`, `blocked` |
| S2 | `target_branch` из SPEC/2 = строке `target_branch:` в `note` G0 | совпадают байт в байт | `UNAPPROVED_BASE` |
| S3 | `git ls-remote origin refs/heads/<target_branch>`; `git merge-base --is-ancestor <base_sha> <tip>` | exit 0 | `STALE_SOURCE` (`before` → работа не начинается; `after` → отчёт `STALE`) |
| S4 | `source_sha` доступен (`git cat-file -e <source_sha>^{commit}` после fetch) и равен утверждённому; нужные blob читаются по `source_sha` | доступен и равен | `STALE_SOURCE` |
| S5 | Снимок refs `TAXI-REFS-SNAPSHOT/1` (§5.1) и его SHA-256 | `after` сравнивается с `before` по правилам §5.2 | по §5.2 |
| S6 | Свежий снимок сообщений задачи: последний действующий `ASSIGN/2`/`RESUME/2` = `assign_ref` сессии; `lease_until` не истёк | `assign_ref` не вытеснен, lease действует | `ASSIGN_FENCE_STALE` / `LEASE_EXPIRED` |

Оба набора результатов (время, `tip` целевой ветки, `refs_snapshot_sha256` до и после) ДОЛЖНЫ быть записаны в `HANDOFF/2` или `QA-REPORT/2` (поля `source_checks.before` и `source_checks.after`, [QA-REPORT.md §2](QA-REPORT.md)).

Задача без ветки **никогда** не создаёт ref. Имя ветки в сообщении read-only задачи запрещено: допустим только литерал `branch: none`.

### 5.1 Снимок refs `TAXI-REFS-SNAPSHOT/1`

```text
TAXI-REFS-SNAPSHOT/1
<full_ref> <40_lowercase_object_sha>
...
```

- Первая строка — литерал `TAXI-REFS-SNAPSHOT/1`.
- Затем каждый видимый разрешённый `refs/heads/*` и `refs/tags/*`, сортировка по имени ref побайтно, по одной строке `<ref> <sha>`.
- Для аннотированных тегов берётся SHA объекта ref как его возвращает `git ls-remote`, без разыменования (`^{}`-строки не включаются).
- Только LF, ровно один завершающий LF. `refs_snapshot_sha256` = SHA-256 этих байтов.
- Пример: [`fixtures/refs-snapshot-example.txt`](fixtures/refs-snapshot-example.txt), 78 байт, SHA-256 `032e90d80bbec3b3c125886c50216d059d306ebd9101fee1a7a1a728cdedd47c`.
- Если нужные refs недоступны или история неполна → `NOT_VERIFIED`/`BLOCKED`. Предполагать, что инвентарь не изменился, запрещено.

### 5.2 Классификация изменений refs между `before` и `after`

| Наблюдение | Классификация | Последствие |
|---|---|---|
| refs не изменились | `PASS` | — |
| только fast-forward утверждённой `target_branch`, `base_sha` и `source_sha` по-прежнему доступны | допустимо | записать старый и новый SHA; `STALE_SOURCE` **не** выставляется |
| rewind, удаление или переписывание `target_branch` | `STALE_SOURCE` | `blocked` |
| любое необъяснённое изменение другого ref | `REF_DRIFT_UNEXPLAINED` | `blocked`, расследование; **не** считается автоматически `SCOPE_VIOLATION` |
| независимое доказательство записи ref этой сессией | `SCOPE_VIOLATION` | `VOID`, `blocked`, отдельная проверка безопасности |

`SCOPE_VIOLATION` приписывается агенту только при независимом доказательстве его записи. Одного различия снимков для этого недостаточно.
