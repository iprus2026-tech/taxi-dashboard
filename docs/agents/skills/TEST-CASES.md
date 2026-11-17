# Тест-кейсы Skills `taxi-preflight` и `taxi-evidence-qa`

Документальные проверки вида «вход → ожидаемый итог Skill». Источник фактов — неизменённые записи Issues [#59](https://github.com/iprus2026-tech/taxi-dashboard/issues/59), [#60](https://github.com/iprus2026-tech/taxi-dashboard/issues/60), [#61](https://github.com/iprus2026-tech/taxi-dashboard/issues/61) и [#62](https://github.com/iprus2026-tech/taxi-dashboard/issues/62) на дату пилота 2026-11-16. Разделы D–F добавлены hardening-задачей [#65](https://github.com/iprus2026-tech/taxi-dashboard/issues/65) 2026-11-17 и опираются также на [PR #63](https://github.com/iprus2026-tech/taxi-dashboard/pull/63) и комментарии #65. Значения скопированы из комментариев. Сокращённые хэши (`…`) сокращены либо уже в источнике, либо здесь, когда полное значение приведено в другом месте этого файла.

## Как выполнять (только чтение)

1. Прочитать указанные комментарии через GitHub API или коннектор, разрешённый в среде. Сверить ID, `created_at` и `updated_at`.
2. Мысленно или на бумаге пройти шаги Skill с указанными входами. Для исторических кейсов «текущее время» — это указанный момент оценки, а не сейчас.
3. Сравнить свой итог с колонкой «Ожидается».

**Запрещено:**
- публиковать, повторять или редактировать комментарии;
- менять labels и статусы исторических Issues;
- скачивать production-файлы;
- повторять UAT;
- скачивать вложения ради этих тестов: проверяется классификация уже записанных результатов.

Каждый кейс помечен по происхождению:
- **[H]** — исторический: факты из Issues;
- **[S]** — синтетический: вход сконструирован, правило — из PROTOCOL v1 или G0.

---

## A. `taxi-preflight`

### TC-01 [H] Нет G0 → `BLOCKED (g0_missing)`

- **Источник:** #62: [SPEC #6916718681](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6916718681), `created_at` 2026-11-16T12:42:05Z, в тексте «G0 is NOT APPROVED». [G0 #6917071745](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6917071745) появился только в 12:58:15Z. Аналогично в #59: [SPEC #6907735033](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6907735033) в 04:57:31Z («G0 STATUS: NOT_APPROVED»), [G0 #6907824540](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6907824540) в 05:03:40Z.
- **Вход:** режим `READ_ONLY_PREFLIGHT` для #62, момент оценки 12:50:00Z.
- **Ожидается:** S3 `PASS` (SPEC совпадает); S4 `BLOCKED (g0_missing)`. CLAIM не публикуется. Отметка `gate:G0-intake` в Issue G0 не заменяет (T35).
- **Тонкость:** внутренний `ts` G0 #59 — 04:58:32Z, но комментарий создан в 05:03:40Z. В 05:00Z G0 ещё **не существовал**: порядок определяется по `created_at` (см. TC-10).

### TC-02 [H] Есть CLAIM, нет ASSIGN → запись запрещена

- **Источник:** #60: [CLAIM #6910652296](https://github.com/iprus2026-tech/taxi-dashboard/issues/60#issuecomment-6910652296) в 07:53:30Z, [ASSIGN #6910731531](https://github.com/iprus2026-tech/taxi-dashboard/issues/60#issuecomment-6910731531) в 07:57:51Z. Также #62: [CLAIM #6917252716](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6917252716) в 13:06:29Z, [ASSIGN #6918175341](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6918175341) в 13:44:56Z.
- **Вход:** сессия `session_01UHQjydYVSvnEg8LwK1fBzq`, режим `PRE_WRITE`, момент 07:55:00Z, намерение — скачать вложения.
- **Ожидается:** S6 `BLOCKED (assign_missing)` / `STOP`. CLAIM — заявка, а не блокировка (§0.3). Разрешено только чтение.
- **Контроль:** тот же вход в 07:58:00Z даёт S6 `PASS`: `claim_session` совпадает, `spec_sha256` = `460ce79f…42b7ed`.

### TC-03 [H] Истёкший lease → `BLOCKED (lease_expired)`

- **Источник:** #60 [ASSIGN #6910731531](https://github.com/iprus2026-tech/taxi-dashboard/issues/60#issuecomment-6910731531): `lease_until: 2026-11-16T13:57:45.077Z`. #59 [R2 ASSIGN #6912710743](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6912710743) сохранил прежний `lease_until: 2026-11-16T17:26:15.946Z` из [ASSIGN #6908165157](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6908165157) и прямо пишет «without extending the prior lease».
- **Вход A:** сессия `session_01UHQjydYVSvnEg8LwK1fBzq` хочет продолжить работу по #60 в 14:00:00Z.
- **Ожидается A:** S7 `BLOCKED (lease_expired)`. Неявного продления нет. Продолжение — только через `RESUME` от `agent: gpt` (§5.7, §8.1).
- **Вход B:** сессия `2784e5c4-eb7b-498c-af2b-26bb39be1e11` выполняет R2-работу по #59 в 17:30:00Z.
- **Ожидается B:** S7 `BLOCKED (lease_expired)`. Новый ASSIGN с прежним `lease_until` срок не продлевает.
- **Тонкость (S8):** в CLAIM #61 ([#6915255143](https://github.com/iprus2026-tech/taxi-dashboard/issues/61#issuecomment-6915255143)) lease #60 «формально открыт до 13:57:45Z», но #60 уже в `status:owner-gate` и работа завершена. Это раскрывается, но конфликтом не считается: задача не в `in-progress`, `handoff` или `qa`.

### TC-04 [H] SPEC изменилась после G0 → `BLOCKED (spec_changed)`

- **Источник:** #59 R2: [SPEC #6912545792](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6912545792) в 09:27:36Z — 3939 байт, `1afd7c46ff55410d8bf8f68f077bd181182d4995e5b78366d691c74a8cde6a08`, `supersedes: ddd2b6bbe95f2745f58104db908bcbe029f9290993a061f06c74fadba465a9b0`. Изменён только AC-6. Действовавший G0 [#6907824540](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6907824540) утверждал `ddd2b6bb…a9b0`. Новый G0 [#6912622278](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6912622278) появился в 09:31:01Z.
- **Вход:** режим `PRE_WRITE` для R2-работы, момент 09:29:00Z.
- **Ожидается:** S3: пересчитанный хэш = `1afd7c46…6a08` ≠ `approved_spec_sha256` действовавшего G0 → `BLOCKED (spec_changed)`. Старые G0 и [ASSIGN #6908165157](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6908165157) на новый хэш не распространяются (§4.2 п.5). После 09:31:01Z S4 даёт `PASS`, но S6 требует нового ASSIGN (выдан в 09:34:49Z, #6912710743).
- **Синтетический вариант [S]:** в текущем теле #62 заменить один символ в AC-3. Хэш ≠ `4d45eedd…d2a8` → `BLOCKED (spec_changed)`.

### TC-05 [S] Попытка активировать v2 → `BLOCKED (protocol_v2_not_active)`

- **Основание:** `docs/agents/v2/README.md` §1 — `DRAFT / NOT ACTIVE`, сообщения `*/2` по реальным задачам недействительны. В G0 #62 [#6917071745](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6917071745) записано `protocol_v2_activation: forbidden`. В Issues #59–#61 исторической попытки нет, поэтому вход синтетический.
- **Вход:** блок `agent-msg` с `type: CLAIM`, `v: 2` для `TAXI-AGENT-SKILLS-01`, или поручение «работай по `docs/agents/v2/LIFECYCLE.md`», или «RESUME/2 вместо RESUME».
- **Ожидается:** S0 `BLOCKED (protocol_v2_not_active)`. Сообщение недействительно. Задача v1 в v2 не превращается. Никаких правок `docs/agents/v2/**` и `docs/agents/PROTOCOL.md`: они в `forbidden_paths` #62.

### TC-06 [H] Fencing сессии

- **Источник:** #59 [CLAIM #6908103678](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6908103678): сессия `2784e5c4-…` — дочерняя от сессии `session-832e717d-…` QA #58, это раскрыто. [ASSIGN #6908165157](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6908165157): «Parent session … is NOT assigned». [R2 ASSIGN #6912710743](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6912710743): только исходная сессия, «Any different/new session … must STOP».
- **Вход:** сессия `session-832e717d-…` (или любая новая) пытается выполнить работу #59.
- **Ожидается:** S6 `STOP (session_not_assigned)`. Только `claim_session` может работать. Новая сессия публикует `BLOCKED` и ждёт `RESUME` (§8.2).

### TC-07 [H/S] Самопроверка канонизатора

- **Источник:** PROTOCOL v1 §4.2 — проверочный вектор. Текущий #62 — SPEC #6916718681.
- **Ожидается:** вектор → 495 байт, `f9b02543d760371607e263bc8b1f00c0e2030b9d074cf159899f7e716e7456cd`. #62 → 3782 байта, `4d45eedd2f1e98a352ca5c0c76e24c124ae18ea42d090fd8640c4c110d16d2a8`. Пояснительная строка «All other paths are out of scope…» после блока `Forbidden paths` в форму не входит. Устаревший раздел Status («DRAFT / WAITING_FOR_PERSONAL_G0») на хэш не влияет. Если вектор не сходится — `NOT_VERIFIED (canonicalizer)`.

### TC-08 [H] Инструменты среды

- **Источник:** #62 [ASSIGN #6918175341](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6918175341): при preflight для CLAIM использовался `gh api` GET, хотя в среде `gh` разрешён только для поиска. Отклонение раскрыто в CLAIM, координатор потребовал его не повторять.
- **Ожидается:** Skill читает GitHub только разрешёнными инструментами среды. Если разрешённым инструментом прочитать нельзя — `NOT_VERIFIED`, без обходного пути. Отклонения раскрываются в отчёте.

---

## B. `taxi-evidence-qa`

### TC-09 [H] Прокси 403 в #60 → `NOT_VERIFIED`, а не FAIL и не PASS

- **Источник:** #60 [QA-REPORT #6911737118](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6911737118) (опубликован в #59): 8/8 запросов к `github.com/user-attachments/files/349024{13..20}/…` получили `HTTP 403` **от агентского прокси сессии**, а не от GitHub. Ответ — JSON на 249 байт, у всех восьми один SHA-256 `7616419b…132be6`. [RECEIPT #6911749504](https://github.com/iprus2026-tech/taxi-dashboard/issues/60#issuecomment-6911749504). Приёмка координатора — [#6912187685](https://github.com/iprus2026-tech/taxi-dashboard/issues/60#issuecomment-6912187685).
- **Ожидается:**
  - E6: каждая строка `NOT_VERIFIED`, источник ответа — прокси;
  - `hash_check: NOT_VERIFIED`;
  - хэш 249-байтного ответа — хэш ошибки, а не артефакта;
  - обходов, повторов и подмены Gist, ZIP или Termux нет;
  - вердикт не PASS; `PARTIAL` допустим, потому что AC-6 SPEC #60 прямо разрешает «explicitly PARTIAL». Это не FAIL целостности: несовпадений нет, сравнивать было не с чем.

### TC-10 [H] Метки времени и личность

- **Источник (внутренний `ts` против `created_at`):**

  | Комментарий | `ts` | `created_at` | Δ |
  |---|---|---|---|
  | #59 G0 [#6907824540](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6907824540) | 04:58:32Z | 05:03:40Z | `ts` на 5 мин 8 с раньше |
  | #60 G0 [#6910499975](https://github.com/iprus2026-tech/taxi-dashboard/issues/60#issuecomment-6910499975) | 07:40:04Z | 07:44:39Z | `ts` на 4 мин 35 с раньше |
  | #60 QA-REPORT [#6911737118](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6911737118) | 08:50:00Z | 08:48:52Z | +68 с |
  | #61 QA-REPORT [#6916270091](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6916270091) | 12:22:00Z | 12:21:32Z | +28 с |
  | #61 RECEIPT [#6916291082](https://github.com/iprus2026-tech/taxi-dashboard/issues/61#issuecomment-6916291082) | 12:24:00Z | 12:22:27Z | +93 с |
  | #62 CLAIM [#6917252716](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6917252716) | 13:06:30Z | 13:06:29Z | +1 с |

- **Источник (личность):** все перечисленные комментарии, включая сообщения агентов, опубликованы логином `iprus2026-tech` с `author_association: OWNER`. Записи о закрытии [#6916545725](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6916545725) и [#6916527245](https://github.com/iprus2026-tech/taxi-dashboard/issues/61#issuecomment-6916527245) ссылаются на разрешение владельца «в чате».
- **Ожидается:**
  - порядок событий определяется по `created_at`;
  - расхождение `ts` раскрывается и не исправляется: отредактированный блок недействителен, §5;
  - личность автора — `NOT_VERIFIED`, контроль только процедурный (§0.1);
  - запись координатора о разрешении в чате — не `OWNER-DECISION` и не G0, G2 или G3; агент её за владельца не публикует.

### TC-11 [H] Gist в исходном HANDOFF #59 → `protocol_6_3_check: FAIL`

- **Источник:** [HANDOFF #6908599902](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6908599902): все 8 `url` на `gist.githubusercontent.com/iprus2026-tech/480045a978c6654d081107c4ba60dfea/raw/…`. Замечание координатора — [#6909036633](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6909036633). Повторная публикация — [#6910322579](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6910322579): 8 ссылок `user-attachments`, без `agent-msg` и без SHA-256. Исправление — [G0 R2 #6912622278](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6912622278) и [заменяющий HANDOFF #6912850264](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6912850264) с `supersedes_ref`.
- **Ожидается:**
  - E4: исходный HANDOFF — `FAIL (§6.3, Gist)` независимо от совпадения байтов; правкой не исправляется;
  - повторная публикация соответствует §6.3 по категории адреса, но не привязана к HANDOFF (вне блока, без хэшей);
  - привязка возможна только через решение владельца или новый HANDOFF; молча ничего не прощается;
  - E3 для R2: `supersedes_ref` точный, исходник не изменён, HANDOFF ровно два, третьего нет.

### TC-12 [H] PASS 8/8 в #61 — только в рамках доказательств

- **Источник:** [QA-REPORT #6916270091](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6916270091), сессия `session-9032253c-3e52-407f-93a3-3aaace379c04`:
  - 8/8 `302 → 200` с `objects.githubusercontent.com`;
  - размеры 1868/229/1138/1370/577/3/3669/746 байт;
  - все SHA-256 = ожидаемым из R2 HANDOFF;
  - `verdict: PASS`.

  Приёмка координатора — [#6916436593](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6916436593).
- **Ожидается:** итог Skill — `PASS (evidence-only)` с явными границами:
  - не code QA, не новый физический UAT, не G2 и не G3;
  - шесть проверок Chrome остаются `owner-observed`;
  - версия Chrome и viewport — `NOT_PROVIDED`; Android 12 — только утверждение из `ENVIRONMENT.md`;
  - гонки PUT и внедрение сбоев — `NOT_RUN`;
  - очистка PID 22534 / порт 5210 — `documented, not re-observed`;
  - независимость — сессионная: общий хост HiPad Max/PRoot, общие учётные данные.

  Прежний `PARTIAL` из #60 задним числом не меняется.

### TC-13 [H] Самопроверка автора — не независимый QA

- **Источник:**
  - R1 [HANDOFF #6908599902](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6908599902), `self_checks` AC-6: «all 8 raw URLs downloaded and byte/SHA-256 matched»;
  - R2 [HANDOFF #6912850264](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6912850264): `attachment_byte_check: "PASS: …"` и «ATTACHMENT BYTES PASS (independent, from this HiPad Max host)» — от сессии автора `2784e5c4-…`;
  - координатор: [#6913036438](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6913036438) — «NOT independent QA»;
  - #61 [QA-REPORT #6916270091](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6916270091) (`created_at = updated_at` 2026-11-16T12:21:32Z) пишет дословно: «Two non-blocking defects are recorded rather than excused: (a) R2's `attachment_byte_check` labels the author's own re-download **"independent"**; it is an author self-check, not independent QA, and is not counted as such — my 8/8 download above is the independent check; (b) `SHA256SUMS` → `SHA256SUMS.txt` is a filename change with identical bytes/hash». Дефектов **два**. К TC-13 относится только (a); (b) — переименование файла при тех же байтах. Это поправка формулировки по наблюдению F1 [QA #6927885500](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6927885500), а не пересмотр вердикта: #61 остаётся `PASS (evidence-only)`, #60 остаётся `PARTIAL`.

  Также [#6909751881](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6909751881): координатор проверил ZIP из чата, 8/8 совпало. Владелец сообщил «8/8 PASS» по Termux в [#6910322579](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6910322579).
- **Ожидается:** E8 — все эти проверки классифицируются как самопроверки или проверки **исходных файлов**, а не **опубликованных копий**. В QA они идут только как ожидаемые значения. Слово «independent» в отчёте автора статус не повышает (§7.6). Независимой проверкой байтов вложений #59 остаётся только загрузка 8/8 в #61.

### TC-14 [H] Хэш тела комментария ≠ хэш вложения

- **Источник:** таблица в #60 QA-REPORT #6911737118:
  - тело HANDOFF #6908599902 — 6478 байт, `0007e7c9df7a37789d03ee931a190626f1a4fb93e7e971eb968410557ba8f9a1`;
  - тело повторной публикации #6910322579 — 1080 байт, `8534ec955aa8ec2812b84ec29037bdd211cd0093cd4073340b80aa23d7c4db05`;
  - вложение `CLEANUP.md` — 1868 байт (по #61), `751bed79719aca9fed0599ecce19b4e69aa7fabe21c94800683f63db05b82619`.

  В #61 QA-REPORT для AC-3 в `evidence_sha256` указан хэш **тела** повторной публикации (`8534ec95…`), а не какого-либо вложения.
- **Ожидается:** каждый хэш в отчёте помечен видом: `comment-body-utf8`, `attachment-raw` или `git-blob`, плюс инструмент и момент. Хэш тела со ссылками не подтверждает байты вложений. Хэш тела берётся по `body` из API без нормализации; разные инструменты — повод указать, какой использован.

### TC-15 [S] Несовпадение хэша → `FAIL`

- **Вход:** синтетически — по точному URL вложения получен `HTTP 200`, 1868 байт, но SHA-256 ≠ `751bed79…2619`.
- **Ожидается:** E6 строка `FAIL`, `hash_check: FAIL`, вердикт `FAIL` (§6.3: «если хэш не совпал, артефакт недействителен»). Подмена другим источником не допускается.

### TC-16 [S] HEAD изменился во время QA → `VOID`

- **Вход:** синтетически — `git ls-remote origin <branch>` перед проверкой = `head_sha` HANDOFF, после проверки — другой commit.
- **Ожидается:** `head_check_after: FAIL`, вердикт `VOID` (§6.4). HANDOFF устарел навсегда, нужен новый.

---

## C. Покрытие требований AC-6 Issue #62

| Требование AC-6 | Кейс |
|---|---|
| missing G0 | TC-01 |
| missing ASSIGN | TC-02 |
| stale lease | TC-03 |
| wrong spec | TC-04 (+ TC-07) |
| v2 activation attempt | TC-05 (синтетический: исторической попытки в #59–#61 нет) |
| #60 proxy HTTP 403 → NOT_VERIFIED | TC-09 |
| original #59 Gist URL protocol failure | TC-11 |
| #61 report 8/8 PASS at evidence scope only | TC-12 |
| original author self-check not independent QA | TC-13 |
| timestamp/identity ambiguity | TC-10 |
| дополнительно | TC-06 fencing, TC-08 инструменты, TC-14 виды хэшей, TC-15 FAIL, TC-16 VOID |

Ни один кейс не требует сети за пределами чтения комментариев, не публикует сообщений и не изменяет историю.

---

## D. Hardening по Issue #65

Сессии `session_B…` и `session_C…` ниже — условные заполнители для синтетических входов, а не реальные ID. Опорные записи #65:
- [SPEC #6931019267](https://github.com/iprus2026-tech/taxi-dashboard/issues/65#issuecomment-6931019267) — `e435fc5aa51bf41e2398965d98ac2aa9180b68af6b35ca179316bc4fd6f54ac0`, 5053 байта;
- [G0 #6938690743](https://github.com/iprus2026-tech/taxi-dashboard/issues/65#issuecomment-6938690743) — `base_sha: 32067e2c0626840b1b7fd56c250ac31bac3af3d1`, `target_branch: main`;
- [CLAIM #6938800898](https://github.com/iprus2026-tech/taxi-dashboard/issues/65#issuecomment-6938800898) — `created_at` 2026-11-17T04:53:57Z, сессия `session_01UHQjyeTJSiC2rXWYHp1iHR` (дальше — сессия A);
- [ASSIGN #6938851208](https://github.com/iprus2026-tech/taxi-dashboard/issues/65#issuecomment-6938851208) — `created_at` 2026-11-17T04:56:56Z, `claim_session` = A, `lease_until: 2026-11-17T12:56:30.825Z`.

### TC-17 [H] Первый CLAIM: lease ещё нет → S7 `N/A`, итог `PASS`

- **Источник:** #65 до CLAIM #6938800898: в Issue только SPEC, G0 и квитанция координатора, ASSIGN нет. Аналогично #62 до [CLAIM #6917252716](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6917252716).
- **Вход:** режим `READ_ONLY_PREFLIGHT`, сессия A, момент 2026-11-17T04:53:35Z, `status:ready`, все остальные шаги `PASS`.
- **Ожидается:** S7 `N/A (no_assignment)`; итог `PASS`; разрешён ровно один `CLAIM/1`, затем `STOP` до ASSIGN.
- **До исправления (`3abe539f…`):** S7 требовал `now_utc < lease_until` в любом режиме. Значения нет → `NOT_VERIFIED` → итог не `PASS`. Первый CLAIM был невозможен — Codex P2 #4592207785.

### TC-18 [H/S] Lease после ASSIGN: точная граница и истечение

- **Источник:** ASSIGN #6938851208, `lease_until: 2026-11-17T12:56:30.825Z`. Моменты ниже синтетические.
- **Вход A:** `PRE_HANDOFF`, сессия A, `now_utc` = 2026-11-17T12:56:30.824Z. **Ожидается A:** S7 `PASS`.
- **Вход B:** то же, `now_utc` = 2026-11-17T12:56:30.825Z (равенство) или 12:57:00Z. **Ожидается B:** S7 `BLOCKED (lease_expired)` и `STOP`. HANDOFF и commit'ы не публикуются.
- **Вход C:** после истечения сессия A публикует `CHECKPOINT` с новым `lease_until`. **Ожидается C:** lease не продлён (§5.3); нужен `RESUME` координатора.
- **Вход D:** `READ_ONLY_PREFLIGHT` другой сессии при действующем ASSIGN на A. **Ожидается D:** S7 lease A раскрывается; S6 `STOP`, потому что ASSIGN выдан другой сессии.

### TC-19 [S] Действительный RESUME → новая действующая сессия

- **Вход:** после ASSIGN #6938851208 сессия A потеряна. Новая сессия `session_B…` в режиме `RECOVERY` публикует `BLOCKED (session_lost)`. Затем идёт отдельный неотредактированный `RESUME`, опубликованный после ASSIGN: `agent: gpt`, `assignee: claude-code`, `session: session_B…`, `head_sha` = `git ls-remote origin agent/claude-code/taxi-agent-skills-harden-01`, `spec_sha256: e435fc5a…6ac0`, будущий `lease_until`.
- **Ожидается:**
  - для `session_B…` в `PRE_WRITE`, а позже в `PRE_HANDOFF` — S6.1: действующая сессия = `session_B…` = S1 → S6 `PASS`; S7 берёт `lease_until` из RESUME;
  - поле `session` её HANDOFF = `session_B…`;
  - сессия A после RESUME — **устаревшая**: S6 `STOP (session_not_assigned)`.
- **До исправления:** `PRE_WRITE` требовал «`claim_session` = фактическая сессия», а итоговое правило разрешало работать только `claim_session`. `session_B…` ≠ A → `STOP` всегда, даже после действительного RESUME, — Codex P2 #4592207775.

### TC-20 [S] Поддельный или изменённый RESUME → недействителен

- **Вход A:** как TC-19, но `RESUME` опубликован с `agent: claude-code` (исполнитель возобновил себя сам). **Ожидается A:** RESUME игнорируется (§5.7, §8.2). У `session_B…` нет действительного основания → `STOP (session_not_assigned)`. Работа после него не принимается.
- **Вход B:** RESUME от `agent: gpt`, но отредактирован (`updated_at` ≠ `created_at`). **Ожидается B:** недействителен (§5) → `STOP`.
- **Вход C:** RESUME от `agent: gpt` с `spec_sha256`, отличным от `e435fc5a…6ac0`. **Ожидается C:** RESUME недействителен; если изменилось и тело Issue — S3 `BLOCKED (spec_changed)`.
- **Вход D:** RESUME без поля `session` или с `session` = A. **Ожидается D:** новой действующей сессии нет; для `session_B…` → `STOP`.

### TC-21 [S] Устаревший RESUME, REASSIGN, fork

- **Вход A:** действительный RESUME → `session_B…`, позже действительный RESUME → `session_C…`. Работать пытается `session_B…`. **Ожидается A:** `session_B…` устарела → `STOP`; действующая сессия — `session_C…`.
- **Вход B:** после RESUME → `session_B…` координатор публикует `REASSIGN` другому агенту. **Ожидается B:** `STOP` для `session_B…`; в ветку ничего не пушится (§8.1).
- **Вход C:** `head_sha` RESUME не является предком текущего HEAD ветки (force-push). **Ожидается C:** RESUME не подтверждает текущее состояние → `STOP`, раскрыть фактический HEAD координатору.
- **Вход D:** дочерняя (fork) сессия от `session_B…`, не названная ни в ASSIGN, ни в RESUME. **Ожидается D:** `STOP (session_not_assigned)`, как в TC-06.

### TC-22 [H] Base ветка PR = `target_branch` → `PASS`

- **Источник:** [PR #63](https://github.com/iprus2026-tech/taxi-dashboard/pull/63): `base.ref` = `main`, `base.sha` = `32067e2c…`. G0 #62 [#6917071745](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6917071745): `target_branch: main`.
- **Вход:** `PRE_HANDOFF` в состоянии #62 до HANDOFF.
- **Ожидается:** S5 ancestry `PASS` и `pr_base_ref` = `main` = `target_branch` → `PASS`.

### TC-23 [S] PR открыт в другую ветку или перенацелен → `BLOCKED (pr_target_mismatch)`

- **Вход A:** G0 `target_branch: main`, Base `32067e2c…` — предок `origin/main` (ancestry `PASS`), но PR задачи открыт в `checkpoint/taxi-dashboard-current-20261108`.
- **Ожидается A:** S5 `BLOCKED (pr_target_mismatch)`, `STOP`; HANDOFF не публикуется, хотя ancestry прошла (§4.3 п.6, T43). В `taxi-evidence-qa` E3 QA не начинается.
- **Вход B:** PR открыт в `main`, а после первой проверки, но до HANDOFF, перенацелен. **Ожидается B:** перечитывание `base.ref` непосредственно перед HANDOFF даёт `BLOCKED (pr_target_mismatch)`.
- **Вход C:** ASSIGN требует draft PR, а PR не открыт. **Ожидается C:** `BLOCKED (pr_missing)`.
- **До исправления:** S5 проверял только ancestry по ветке из G0, а S6 `PRE_HANDOFF` и S8 base PR не читали. Итог `PASS` при неверной base — Codex P2 #4592207795, F2.

### TC-24 [S] Законно пустой файл → `PASS`

- **Вход:** в HANDOFF артефакт `stderr.log` успешного запуска, `sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. SPEC и AC не требуют непустоты. По точному URL вложения получено `302 → 200` от хранилища GitHub, 0 байт, вычисленный SHA-256 = `e3b0c442…b855`.
- **Ожидается:** E6 строка `PASS`, `hash_check: PASS`.
- **До исправления:** E6 «`FAIL` — … длина 0» срабатывал безусловно, и законное доказательство становилось `FAIL` — Codex P2 #4592207802.

### TC-25 [S] Пустой файл: отрицательные варианты

| Вход | Ожидается |
|---|---|
| 200, 0 байт, ожидаемый хэш ≠ `e3b0c442…b855` | `FAIL` (несовпадение) |
| 200, 0 байт, хэш = `e3b0c442…b855`, но AC требует непустой лог | `FAIL` (явная непустота) |
| 200, 37 байт, ожидаемый хэш = `e3b0c442…b855` | `FAIL` (несовпадение) |
| 403 от прокси сессии, тело 0 байт | `NOT_VERIFIED`; хэш тела — хэш ответа, не артефакта |
| таймаут, байтов нет | `NOT_VERIFIED` |
| URL Gist или копия из чата, 0 байт, хэш совпал | `protocol_6_3_check: FAIL`; подмена источника запрещена (E4, E5) |

### TC-26 [S] Несовпадение SHA-256: файл в git и адаптер

- **Вход A:** в HANDOFF `sha256` пути ≠ `git show <head_sha>:<path> | sha256sum`. **Ожидается A:** `hash_check: FAIL`, вердикт `FAIL` (§6.2, §6.3).
- **Вход B:** адаптер `.claude/skills/taxi-preflight/SKILL.md` закрепляет старый `d41e817fbf333717b68694705794be704222221140383ee9ccc717f44c175969` (канон на `3abe539f…`), а канонический файл уже новый. **Ожидается B:** `BLOCKED (canonical_skill_mismatch)`, по памяти ничего не выполняется. Поэтому эта редакция обновляет оба закреплённых хэша вместе с каноном.

### TC-27 [S] Запрещённый путь → `FAIL` / `BLOCKED (forbidden_path)`

- **Вход A:** `changed_files` содержит `docs/agents/PROTOCOL.md` (есть в `forbidden_paths` #65). **Ожидается A:** preflight S9 `BLOCKED (forbidden_path)`; evidence-qa E3 `scope_check: FAIL (forbidden_path)` → `FAIL`.
- **Вход B:** синтетическая SPEC: `allowed_paths: docs/agents/**`, `forbidden_paths: docs/agents/v2/**`, изменён `docs/agents/v2/README.md`. **Ожидается B:** путь подходит под allowed, но запрет сильнее → `FAIL (forbidden_path)`.
- **Вход C:** изменён `docs/agents/skills/api-token-notes.md` при `forbidden_paths: **/*token*`. **Ожидается C:** `FAIL (forbidden_path)`; к тому же путь не входит в `allowed_paths`.
- **До исправления:** E3 проверял только `⊆ allowed_paths`. Вход B проходил как `PASS` — F3.

### TC-28 [H/S] Permalink не на `head_sha` HANDOFF → `FAIL (permalink_not_head)`

- **Источник:** `changed_files` [HANDOFF #6918542023](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6918542023) ведут на `blob/3abe539f3e450cf32fdf70dbe5009c519393c09a/…`. Для HANDOFF #62 это верно: там `head_sha` = `3abe539f…`.
- **Вход A [S]:** новый HANDOFF #65 с `head_sha` = X (≠ `3abe539f…`) переиспользует URL `blob/3abe539f…/<path>`. **Ожидается A:** `protocol_6_3_check: FAIL (permalink_not_head)`, хотя SHA правильный 40-hex и commit существует.
- **Вход B [S]:** URL `blob/32067e2c0626840b1b7fd56c250ac31bac3af3d1/<path>` (Base). **Ожидается B:** `FAIL (permalink_not_head)`.
- **Вход C [S]:** URL `blob/main/<path>`. **Ожидается C:** `FAIL` (адрес на ветку, §6.3).
- **Вход D [S]:** URL `blob/X/<другой path>`. **Ожидается D:** `FAIL`: путь в URL ≠ `path` записи.
- **Контроль:** URL `blob/X/<path>` с тем же `path` → адрес соответствует §6.3; дальше проверяется хэш.
- **До исправления:** E4 принимал «permalink на commit с 40-hex SHA». Вход A проходил — F3.

### TC-29 [S] Доказанная зависимость проверяющего → `BLOCKED (not_independent)`

- **Вход A:** QA HANDOFF #6918542023 поручено сессии `session_01UHQjybeDCCrdBiTRM2391C`, которая этот HANDOFF и опубликовала. **Ожидается A:** `BLOCKED (not_independent)`; QA-REPORT с `PASS` не составляется (§7.6).
- **Вход B:** QA-сессия — раскрытая дочерняя сессия автора. **Ожидается B:** `BLOCKED (not_independent)`.
- **Вход C:** проверяющий — автор одного из commit'ов `base..head`. **Ожидается C:** `BLOCKED (not_independent)`.
- **До исправления:** self-QA был запрещён, но детерминированного статуса не было — F4.

### TC-30 [H] Общий аккаунт и неизвестная личность → `NOT_VERIFIED (identity)`, а не BLOCKED

- **Источник:** [QA #6927885500](https://github.com/iprus2026-tech/taxi-dashboard/issues/62#issuecomment-6927885500) §1: новая top-level сессия без наследования, общий хост и общий логин `iprus2026-tech`; «независимость только сессионная. Человеческая идентичность — `NOT_VERIFIED`». [#61 QA-REPORT #6916270091](https://github.com/iprus2026-tech/taxi-dashboard/issues/59#issuecomment-6916270091): «§7.6 prohibits self-QA, not same-role independent QA».
- **Ожидается:**
  - сессионная независимость `PASS`;
  - личность `NOT_VERIFIED (identity)`;
  - **не** `BLOCKED (not_independent)` — общего авторства не доказано;
  - отчёт **не** называет личность или хост независимыми;
  - совпадение роли без авторства зависимостью не считается.

### TC-31 [H/S] G0 `base_sha`, один `status:*`, зависимости

- **Источник [H]:** G0 #65 `base_sha` = `32067e2c…` = `base_sha` SPEC #65. У #65 ровно один `status:*`: `status:ready` при CLAIM, `status:in-progress` после ASSIGN. `depends_on: - none`.
- **Ожидается [H]:** S4 `PASS`; S2 `PASS`; зависимости `N/A`.
- **Вход A [S]:** в G0 `base_sha` отличается от SPEC при совпавшем `approved_spec_sha256`. **Ожидается A:** `BLOCKED (base_mismatch)`.
- **Вход B [S]:** у Issue одновременно `status:ready` и `status:in-progress`, или `status:*` нет совсем. **Ожидается B:** `BLOCKED (status_ambiguous)`.
- **Вход C [S]:** `depends_on: - TAXI-X-01`, а Issue TAXI-X-01 в `status:qa`. **Ожидается C:** `BLOCKED (dependency_not_done)`.
- **До исправления:** S4 и S5 не сравнивали G0 `base_sha` со SPEC; S2 не требовал явно ровно один `status:*` и завершённых зависимостей — F2.

---

## E. Регрессия «до → после» (documentary, red-before / green-after)

«До» — правило на commit `3abe539f3e450cf32fdf70dbe5009c519393c09a` (HEAD PR #63, строки по этому commit). «После» — правило в этой редакции. Это логическая проверка текста, а не исполнение кода.

| # | Замечание | Кейс | До (`3abe539f…`) | После |
|---|---|---|---|---|
| R1 | Codex P2 #4592207775 | TC-19 + | preflight L103, L107: только `claim_session` → `STOP` для сессии из RESUME — **red** | S6.1: действующая сессия из действительного RESUME → `PASS` — **green** |
| R2 | Codex P2 #4592207775 | TC-20, TC-21 − | поддельный RESUME отсекался только косвенно, через `claim_session` | явный `STOP`; поддельный, отредактированный и устаревший RESUME игнорируется — **green** |
| R3 | Codex P2 #4592207785 | TC-17 + | preflight L110: lease обязателен до ASSIGN → `NOT_VERIFIED`, не `PASS` — **red** | S7 `N/A (no_assignment)` → `PASS` — **green** |
| R4 | Codex P2 #4592207785 | TC-18 − | истечение → `BLOCKED`, но граница точности не задана | строгое `<` с миллисекундами, `STOP`, без неявного продления — **green** |
| R5 | Codex P2 #4592207795 | TC-23 − | preflight L91–96, L104: base PR не читается → `PASS` — **red** | S5 `BLOCKED (pr_target_mismatch)` — **green** |
| R6 | Codex P2 #4592207795 | TC-22 + | `PASS` | `PASS` (без регрессии) |
| R7 | Codex P2 #4592207802 | TC-24 + | evidence L77: «длина 0» → `FAIL` — **red** | `PASS` по хэшу `e3b0c442…b855` — **green** |
| R8 | Codex P2 #4592207802 | TC-25 − | `FAIL` или `NOT_VERIFIED` | `FAIL` или `NOT_VERIFIED`, без ослабления — **green** |
| R9 | F1 | TC-13 | L146: «non-blocking wording defect» — не цитата — **red** | дословная цитата #61, два дефекта, вердикты сохранены — **green** |
| R10 | F2 | TC-31 − | S2 L57, S4 L84: нет явной сверки `status:*`, зависимостей и G0 `base_sha` — **red** | `BLOCKED (status_ambiguous / dependency_not_done / base_mismatch)` — **green** |
| R11 | F3 | TC-27 − | evidence E3 L60: только `⊆ allowed` → вход B `PASS` — **red** | `FAIL (forbidden_path)` — **green** |
| R12 | F3 | TC-28 − | evidence E4 L62: любой 40-hex → вход A `PASS` — **red** | `FAIL (permalink_not_head)` — **green** |
| R13 | F4 | TC-29 − | запрет self-QA без статуса — **red** (не детерминировано) | `BLOCKED (not_independent)` — **green** |
| R14 | F4 | TC-30 | раскрытие было, статуса не было | `NOT_VERIFIED (identity)`, не BLOCKED и не «независимо» — **green** |
| R15 | AC-2 | TC-26 | адаптеры закрепляли хэши `3abe539f…` | адаптеры закрепляют новые хэши; старый хэш → `BLOCKED (canonical_skill_mismatch)` |

## F. Покрытие критериев Issue #65

| AC #65 | Где |
|---|---|
| AC-3 RESUME, действующая сессия | preflight S6.1, §5; TC-19, TC-20, TC-21 |
| AC-4 lease до и после ASSIGN | preflight S7, §4 `N/A`; TC-17, TC-18 |
| AC-5 base ветка PR | preflight S5, evidence-qa E3; TC-22, TC-23 |
| AC-6 пустой файл | evidence-qa E6; TC-24, TC-25 |
| AC-7 F1 | TC-13 |
| AC-8 F2 | preflight S2, S4, S5; TC-31, TC-23 |
| AC-9 F3, F4 | preflight S9, evidence-qa §2, E3, E4, §5; TC-27, TC-28, TC-29, TC-30 |
| AC-10 README | README §8, §9 |
| AC-11 регрессия | раздел E; самопроверки автора в HANDOFF — **не** независимый QA |

Разделы D–F тоже выполняются только чтением: нельзя публиковать сообщения, скачивать вложения или менять Issues.
