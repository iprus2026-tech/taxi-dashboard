# Тест-кейсы Skills `taxi-preflight` и `taxi-evidence-qa`

Документальные проверки вида «вход → ожидаемый итог Skill». Источник фактов — неизменённые записи Issues [#59](https://github.com/iprus2026-tech/taxi-dashboard/issues/59), [#60](https://github.com/iprus2026-tech/taxi-dashboard/issues/60), [#61](https://github.com/iprus2026-tech/taxi-dashboard/issues/61) и [#62](https://github.com/iprus2026-tech/taxi-dashboard/issues/62) на дату пилота 2026-11-16. Разделы D–F добавлены hardening-задачей [#65](https://github.com/iprus2026-tech/taxi-dashboard/issues/65) 2026-11-17 и опираются также на [PR #63](https://github.com/iprus2026-tech/taxi-dashboard/pull/63) и комментарии #65. Разделы G–I и дополнения к TC-17 добавлены второй hardening-задачей [#68](https://github.com/iprus2026-tech/taxi-dashboard/issues/68) 2026-11-17 и опираются на [PR #66](https://github.com/iprus2026-tech/taxi-dashboard/pull/66) (HEAD `0cb5757c28e87a39e810162657bd38213a10c500`) и комментарии #68. Разделы J–L добавлены задачей [#75](https://github.com/iprus2026-tech/taxi-dashboard/issues/75) 2026-11-18 и опираются на три замечания Codex к [PR #72](https://github.com/iprus2026-tech/taxi-dashboard/pull/72) (HEAD `8b3a622c49af58409340965ecb5f0849c3befd7f`) и комментарии #75. Значения скопированы из комментариев. Сокращённые хэши (`…`) сокращены либо уже в источнике, либо здесь, когда полное значение приведено в другом месте этого файла.

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
- **Ожидается:** S6.1 `N/A (no_assignment)`: в задаче нет ни одного `ASSIGN` от `agent: gpt`; S7 `N/A (no_assignment)`; итог `PASS`; разрешён ровно один `CLAIM/1`, затем `STOP` до ASSIGN.
- **До исправления (`3abe539f…`):** S7 требовал `now_utc < lease_until` в любом режиме. Значения нет → `NOT_VERIFIED` → итог не `PASS`. Первый CLAIM был невозможен — Codex P2 #4592207785.
- **До исправления (`0cb5757c…`, добавлено #68):** S7 уже давал `N/A`, но S6.1 L125 безусловно требовал «действующая сессия = S1». Без ASSIGN действующей сессии нет → `STOP (session_not_assigned)`; §4 L171 не разрешал `N/A` для S6, а L173 требовал `PASS` всех обязательных шагов. Итог `STOP`, кейс оставался **red** — Codex P2 #4596961703. **После:** green (§H, R16).

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

---

## G. Hardening-02 по Issue #68

Сессии `session_Q1…`, `session_Q2…` и `session_Q3…` ниже — условные заполнители для синтетических входов, а не реальные ID. `X` — условный 40-hex `head_sha` нового HANDOFF. Опорные записи #68:
- [SPEC #6942795142](https://github.com/iprus2026-tech/taxi-dashboard/issues/68#issuecomment-6942795142) — `53130953a5b425b8fc713274f4007321635f19ed1f6501197086fcf50c8efd16`, 5867 байт;
- [G0 #6943730960](https://github.com/iprus2026-tech/taxi-dashboard/issues/68#issuecomment-6943730960) — `created_at` 2026-11-17T09:11:48Z, `base_sha: 32067e2c…`, `target_branch: main`;
- [CLAIM #6943894075](https://github.com/iprus2026-tech/taxi-dashboard/issues/68#issuecomment-6943894075) — `created_at` 2026-11-17T09:19:11Z (внутренний `ts` 09:19:30Z, +19 с, раскрыто), сессия `session_01UHQjyfK487x9yA1CgAYEN1`;
- [ASSIGN #6943949459](https://github.com/iprus2026-tech/taxi-dashboard/issues/68#issuecomment-6943949459) — `created_at` 2026-11-17T09:21:48Z, `claim_session` = эта сессия, `lease_until: 2026-11-17T18:00:00Z`.

### TC-32 [H] Первый CLAIM #68 без ASSIGN → S6.1 `N/A (no_assignment)`, итог `PASS`

- **Источник:** до 09:19:11Z в #68 были только SPEC, G0 и квитанция координатора [#6943766859](https://github.com/iprus2026-tech/taxi-dashboard/issues/68#issuecomment-6943766859). Ни одного `ASSIGN` не было, `status:ready`. CLAIM #6943894075 записал «S6.1 effective-session → `N/A (no_assignment)`, lease → `N/A (no_lease)`». ASSIGN появился только в 09:21:48Z.
- **Вход:** `READ_ONLY_PREFLIGHT`, сессия `session_01UHQjyfK487x9yA1CgAYEN1`, момент 09:18:37Z, остальные шаги `PASS`.
- **Ожидается:** S6.1 `N/A (no_assignment)`, S7 `N/A (no_assignment)`, итог `PASS`, ровно один `CLAIM/1`, затем `STOP` до ASSIGN.
- **Контроль после ASSIGN:** тот же вход в 09:27Z в `PRE_WRITE` → назначение есть, S6.1 обязателен: действующая сессия = `claim_session` = S1 → `PASS`. Тот же момент в `READ_ONLY_PREFLIGHT` → свой CLAIM уже есть, второй не публикуется.
- **До исправления (`0cb5757c…`):** L125 → `STOP (session_not_assigned)`; итог не `PASS` (L171, L173) — **red**.

### TC-33 [S] Коллизии в `READ_ONLY_PREFLIGHT`: `N/A` не открывается

| Вход | Ожидается |
|---|---|
| A. Действительный ASSIGN от `agent: gpt` на `session_Q1…`; CLAIM хочет опубликовать `session_Q2…` | назначение есть → S6.1 обязателен → `STOP`; второй исполнитель CLAIM не публикует |
| B. Своя сессия уже опубликовала CLAIM, ASSIGN ещё нет | S6.1 `N/A`, но второй CLAIM не публикуется (ровно один) |
| C. ASSIGN на `session_Q1…`, затем действительный RESUME на `session_Q2…`; preflight запускает `session_Q1…` | `session_Q1…` устарела → `STOP (session_not_assigned)` |
| D. Дочерняя (fork) сессия от `session_Q1…` при действующем ASSIGN на `session_Q1…` | `STOP (session_not_assigned)`, как TC-06 и TC-21 D |
| E. Единственный «ASSIGN» опубликован с `agent: claude-code` | ASSIGN недействителен (§5.2), раскрывается; назначением не считается → S6.1 `N/A`, допустим ровно один CLAIM, решение за координатором |
| F. ASSIGN от `agent: gpt` отредактирован (`updated_at ≠ created_at`) | прав не даёт, но и `N/A` не открывает (fail closed) → `STOP`, вопрос координатору |
| G. `PRE_WRITE` или `PRE_HANDOFF` без ASSIGN | `N/A` запрещён → `BLOCKED (assign_missing)` / `STOP` (TC-02) |
| H. `N/A (no_assignment)` записан для S6.1 при существующем ASSIGN | неразрешённый `N/A` → `NOT_VERIFIED` → итог не `PASS` (§4) |
| I. Прежний ASSIGN оборван `RELEASE` его действующей сессии (или `REASSIGN` от `agent: gpt`), Issue снова `status:ready`; CLAIM публикует новый заявитель | назначение прекращено → S6.1 `N/A (no_assignment)`, прежняя цепочка раскрывается; ровно один CLAIM |
| J. Как I, но вместо `RELEASE` опубликован `BLOCKED` действующей сессии | `BLOCKED` цепочку не прекращает (ждёт `RESUME`) → назначение есть → `STOP` |

- **До исправления (`0cb5757c…`):** входы A, C, D давали `STOP` и раньше, без регрессии. Положительный вход (TC-17, TC-32) давал `STOP` вместо `PASS`. Входы E–J не были описаны.

### TC-34 [S] Возобновлённая QA-сессия → проверка и публикация разрешены

- **Вход:** QA-задача по HANDOFF с `head_sha` = X. ASSIGN QA выдан `session_Q1…`, называет `QA-REPORT/1` и `RECEIPT/1` результатом. `session_Q1…` потеряна и публикует `BLOCKED (session_lost)`. Затем идёт отдельный неотредактированный RESUME после ASSIGN: `agent: gpt`, `assignee: deepseek-qa`, `session: session_Q2…`, `head_sha` = X, `spec_sha256` = пересчитанная SPEC QA-задачи = её G0, будущий `lease_until`. `session_Q2…` не связана с автором HANDOFF.
- **Ожидается:**
  - `taxi-preflight` `PRE_WRITE` для `session_Q2…`: S6.1 действующая сессия = `session_Q2…` → `PASS`;
  - `taxi-evidence-qa` §2 п.1 `PASS` без требования `claim_session` = `session_Q2…`; §2 п.2 сессионная независимость `PASS`;
  - E9 перед публикацией: цепочка не изменилась, lease действует;
  - `QA-REPORT/1` и `RECEIPT/1` публикует `session_Q2…`, поле `session` = `session_Q2…`;
  - `session_Q1…` устарела и ничего не публикует.
- **До исправления (`0cb5757c…`):** evidence-qa L32 «ASSIGN с `claim_session` = эта сессия» → для `session_Q2…` `STOP`; L15 и L25 запрещали публикацию — **red**, хотя `taxi-preflight` S6.1 уже давал `PASS` (Codex P2 #4596961734).

### TC-35 [S] Возобновлённая QA: отрицательные варианты

| Вход (как TC-34, но…) | Ожидается |
|---|---|
| A. RESUME опубликован с `agent: deepseek-qa` (самовозобновление) или `agent: claude-code` | поддельный, игнорируется → `STOP (session_not_assigned)`; QA-REPORT и RECEIPT не публикуются |
| B. RESUME от `agent: gpt`, но отредактирован | недействителен → `STOP` |
| C. RESUME нет совсем; `session_Q2…` ссылается на чат или квитанцию координатора | `STOP (session_not_assigned)`: квитанция — не RESUME |
| D. RESUME с `spec_sha256` ≠ SPEC QA-задачи или опубликован до ASSIGN | недействителен → `STOP`; при изменённом теле Issue — `BLOCKED (spec_changed)` |
| E. `lease_until` RESUME истёк до публикации (E9) | `BLOCKED (lease_expired)`, публикации нет |
| F. Позже второй действительный RESUME на `session_Q3…`; публиковать пытается `session_Q2…` | `session_Q2…` устарела → `STOP`, черновик передаётся координатору |
| G. После RESUME опубликован `REASSIGN` | цепочка оборвана → `STOP` |
| H. Действительный RESUME выдан сессии автора HANDOFF или её дочерней сессии | полномочия есть, независимости нет → `BLOCKED (not_independent)` (§2 п.2, §7.6); QA-REPORT с `PASS` не составляется |
| I. ASSIGN QA не называет QA-REPORT результатом; RESUME действителен | RESUME scope не расширяет → публиковать нельзя, только черновик |

### TC-36 [H] Permalink на `head_sha` как адрес, байты — из объекта git (G1) → `PASS`

- **Источник:** [HANDOFF #6939150464](https://github.com/iprus2026-tech/taxi-dashboard/issues/65#issuecomment-6939150464) (#65): `head_sha: 0cb5757c28e87a39e810162657bd38213a10c500`. Запись `path: .agents/skills/taxi-preflight/SKILL.md`, `sha256: 4af7e921eecb7b4120e388f18fe7640ee1a0ff21a8bfa674275e6dd0c2bf70f1`, `url: https://github.com/iprus2026-tech/taxi-dashboard/blob/0cb5757c28e87a39e810162657bd38213a10c500/.agents/skills/taxi-preflight/SKILL.md`.
- **Наблюдение автора этой редакции** (2026-11-17T09:32Z, самопроверка, не независимый QA):
  - `git ls-remote origin refs/heads/agent/claude-code/taxi-agent-skills-harden-01` = `0cb5757c…`;
  - `git rev-parse --verify 0cb5757c…^{commit}` = `0cb5757c…`;
  - `git ls-tree 0cb5757c… -- .agents/skills/taxi-preflight/SKILL.md` → `100644 blob 13c79e24eeed03ca43b0763fb7faddfe7bcc9066`;
  - `git cat-file blob …` → 28729 байт, `git hash-object` = `13c79e24…9066`, SHA-256 = `4af7e921…70f1`.

  Для `.agents/skills/taxi-evidence-qa/SKILL.md`: `100644 blob f133a41a7ff59f29b50efb6b7f2c6c918235d2a6`, 20583 байта, SHA-256 `80267ce3e32a0beb21762c5d252e7e6f536768ee6758ad41bb1f3759e9d961dd`.
- **Ожидается:** E4 `protocol_6_3_check: PASS`: точный вид, `head_sha` HANDOFF, тот же `path`. E5-G способ G1. E6 строка: вид `git-blob`, способ G1, происхождение (fetch из `origin`, `head_sha`, `path`, `100644`, `blob_id`), HTTP `N/A (local git object)`, `PASS`.
- **До исправления (`0cb5757c…`):** E5 L84 — «только точные URL из перечня», способа для объекта git нет. E6 L96 — `PASS` только при «финальный ответ 200 от хранилища GitHub». Чтение `git show` по §3 L58 не давало `PASS`, а загрузка точного URL давала HTML (TC-37) — **red**.

### TC-37 [H/S] HTML-просмотрщик `HTTP 200` и raw-подмены → не байты файла

- **Наблюдение [H]** (автор этой редакции, 2026-11-17T09:32Z): загрузка точного URL из TC-36 через прокси сессии дала `HTTP 200`, `content-type: text/html; charset=utf-8`, 331196 байт, SHA-256 `89934e2dde8484b3d9de728feee4a189c48b7cb7e070082dac1f2bc15ccaf115` ≠ `4af7e921…70f1`. Страница динамическая, поэтому её хэш невоспроизводим и доказательством ничего не является.
- **Ожидается:** это **не** `FAIL` по хэшу и **не** `PASS`. Ответ просмотрщика — запрещённый способ (E5-G), байты файла не получены. Если подлинным способом (G1 или G2) байты не получены, строка `NOT_VERIFIED`; если получены — итог по ним (TC-36). Хэш HTML не записывается как хэш файла.
- **Вход [S]:** вместо permalink загружен `https://raw.githubusercontent.com/iprus2026-tech/taxi-dashboard/<X>/<path>`, или `…/blob/<X>/<path>?raw=true`, или `…/raw/<X>/<path>`, или архив `codeload.github.com/…/zip/<X>`, или зеркало или CDN. Хэш совпал. **Ожидается:** подмена источника → байты не засчитываются; без G1 или G2 строка `NOT_VERIFIED`. Если такой адрес стоит **в самом HANDOFF** → E4 `FAIL (url_malformed)` (§6.3).
- **До исправления (`0cb5757c…`):** просмотрщик давал ложный `FAIL` по хэшу. Raw-подмена не была явно запрещена для permalink — **red**.

### TC-38 [S] Неверный HEAD или путь при получении байтов

| Вход | Ожидается |
|---|---|
| A. `git cat-file blob <base_sha>:<path>`, `<ancestor>:<path>` или `<branch>:<path>` вместо `head_sha` | не засчитывается (E5-G: только `head_sha` из адреса); без правильного чтения → `NOT_VERIFIED` |
| B. Байты прочитаны из рабочей копии (`cat <path>`) или локальной ветки, не сверенной с `origin` | запрещено → `NOT_VERIFIED` |
| C. `git ls-remote origin <branch>` ≠ `head_sha` до или после проверки | E1 → `VOID` (§6.4) |
| D. Commit `head_sha` подлинно получен, но записи `path` в его дереве нет | `FAIL (path_not_in_commit)` |
| E. Запись `path` — symlink `120000`, submodule или каталог; или `100755` при требовании `100644` | `FAIL (not_regular_file)` |
| F. Чтение по другому `path` той же записи (опечатка в команде) | не засчитывается; повтор с точным `path` в пределах политики попыток |

### TC-39 [S] Неправильный или недопустимый адрес → E4 `FAIL`

| URL в `changed_files` | Ожидается |
|---|---|
| `…/blob/0cb5757/<path>` (сокращённый SHA) | `FAIL (url_malformed)` |
| `…/blob/0CB5757C…/<path>` (верхний регистр) | `FAIL (url_malformed)`: сверка точная |
| `…/tree/<X>/<path>` | `FAIL (url_malformed)` |
| `…/blob/<X>/<path>#L10`, `?plain=1` | `FAIL (url_malformed)`: query и фрагмент не допускаются |
| `http://github.com/…`, другой владелец или репозиторий, `%2F` в пути, `./` или `..` | `FAIL (url_malformed)` |
| `…/blob/<base_sha>/<path>`, `…/blob/main/<path>` | `FAIL (permalink_not_head)` / `FAIL` (TC-28) |

Во всех случаях E4 и E5–E6 записываются отдельно: совпавшие байты (через G1 по `head_sha`) не исправляют `protocol_6_3_check: FAIL`, и вердикт `FAIL`.

### TC-40 [S] Git objects API (G2), ошибки API и сети

| Вход | Ожидается |
|---|---|
| A. `git/commits/X` 200, `sha` = X → дерево → ровно одна запись `path`, `blob`, `100644` → `git/blobs/{blob_id}` → base64 → байты; git-хэш = `blob_id`, SHA-256 = ожидаемому | `PASS`, способ G2, происхождение — цепочка запросов |
| B. Как A, но git-хэш декодированных байтов ≠ `blob_id` | `NOT_VERIFIED (blob_integrity)`: передача не подлинна; **не** `FAIL` и **не** `PASS` |
| C. Как A, git-хэш = `blob_id`, но SHA-256 ≠ ожидаемому из HANDOFF | `FAIL` (подлинные байты не совпали) |
| D. Ответ дерева `truncated: true`, запись не найдена | пошаговый обход; без него → `NOT_VERIFIED`, а не `path_not_in_commit` |
| E. API 5xx, 403 лимита запросов, 404 на commit | `NOT_VERIFIED`; указать, кто ответил (GitHub API) |
| F. `git fetch` для G1 → 403 прокси или таймаут | `NOT_VERIFIED`, источник — прокси сессии; без обхода, зеркал и архивов |
| G. Contents API с `ref=main` | ref не `head_sha` → не засчитывается |
| H. Инструмент коннектора отдал текст, без контроля `blob_id` | байты не доказаны → `NOT_VERIFIED` |

### TC-41 [S] Пустой git-файл и подлинное несовпадение

| Вход | Ожидается |
|---|---|
| A. `git ls-tree X -- <path>` → `100644 blob e69de29bb2d1d6434b8b29ae775ad8c2e48c5391`, 0 байт, ожидаемый `e3b0c442…b855`, непустота не требуется | `PASS` (E6, пустой файл) |
| B. Как A, но AC требует непустой файл | `FAIL` (явная непустота) |
| C. 0 байт, ожидался другой хэш | `FAIL` (несовпадение) |
| D. Ожидался `e3b0c442…b855`, получены непустые подлинные байты | `FAIL` (несовпадение) |
| E. Чтение не выполнено (fetch 403), получено 0 байт | `NOT_VERIFIED`: это не пустой артефакт |

### TC-42 [S] Вложения — отдельный способ (E5-A)

| Вход | Ожидается |
|---|---|
| A. `https://github.com/user-attachments/files/<id>/<name>` из перечня → `302 → 200` от хранилища GitHub, SHA-256 = ожидаемому | `PASS`, вид `attachment-raw`, способ E5-A (как TC-12) |
| B. 403 прокси сессии | `NOT_VERIFIED` (TC-09) |
| C. Финальный 200 — HTML-страница входа на `github.com`, а не хранилище файлов | `NOT_VERIFIED`; хэш страницы — не хэш вложения |
| D. Вложение пытаются «получить» через `git show` или Git objects API | неприменимо: G1 и G2 только для git-файлов |
| E. Git-файл пытаются оценивать по правилу вложений («нужен HTTP 200») | неверно: для G1 HTTP не требуется (E6) |

---

## H. Регрессия «до (`0cb5757c…`) → после» (documentary, red-before / green-after)

«До» — правило на commit `0cb5757c28e87a39e810162657bd38213a10c500` (HEAD PR #66, строки по этому commit). «После» — правило в этой редакции. Это логическая проверка текста, а не исполнение кода. Самопроверка автора — **не** независимый QA.

| # | Замечание | Кейс | До (`0cb5757c…`) | После |
|---|---|---|---|---|
| R16 | Codex P2 #4596961703 | TC-17, TC-32 + | preflight L125 безусловно → `STOP (session_not_assigned)`; L171 без `N/A` для S6; итог L173 не `PASS` — **red** | S6.1 «Применимость»: `N/A (no_assignment)` только в `READ_ONLY_PREFLIGHT` без ASSIGN от `agent: gpt`; один CLAIM, затем `STOP` — **green** |
| R17 | Codex P2 #4596961703 | TC-33 − | A, C, D → `STOP`; E–J не описаны | A, C, D, F, J → `STOP`; B — второй CLAIM не публикуется; G → `BLOCKED (assign_missing)`; H → `NOT_VERIFIED`; E и I раскрываются, `N/A` только при отсутствии или явном прекращении назначения — **green**, без ослабления |
| R18 | Codex P2 #4596961703 | TC-18 D | `STOP` при чужом ASSIGN | `STOP` (без регрессии): назначение есть, S6.1 обязателен |
| R19 | Codex P2 #4596961734 | TC-34 + | evidence L32 `claim_session` = эта сессия; L15 и L25 — публикация только при ASSIGN на эту сессию → `STOP` для `session_Q2…` — **red** | §2 п.1, §0, §1, E9, §6: действующая сессия по цепочке S6.1 → `PASS`, публикация от `session_Q2…` — **green** |
| R20 | Codex P2 #4596961734 | TC-35 − | поддельный RESUME отсекался косвенно, через `claim_session`; RESUME на автора не был назван | явная проверка каждого поля RESUME, `STOP`/`BLOCKED (lease_expired)`; RESUME на автора → `BLOCKED (not_independent)` — **green** |
| R21 | Codex P2 #4596961721 | TC-36 + | E5 L84 только URL; E6 L96 `PASS` только при HTTP 200 от хранилища; объект git `PASS` не давал — **red** | E5-G G1 и G2, E6 по виду источника, HTTP для G1 не требуется → `PASS` — **green** |
| R22 | Codex P2 #4596961721 | TC-37 | HTML-просмотрщик 200 → ложный `FAIL` по хэшу — **red** | запрещённый способ, `NOT_VERIFIED` без подлинных байтов, хэш HTML не записывается — **green** |
| R23 | Codex P2 #4596961721 | TC-38, TC-39 − | `path_not_in_commit`, `not_regular_file`, `url_malformed` не различались | детерминированные `FAIL`, `VOID`, `NOT_VERIFIED` — **green** |
| R24 | Codex P2 #4596961721 | TC-40, TC-41 | ошибки API, git-хэш, пустой git-файл не описаны | `blob_integrity` → `NOT_VERIFIED`; подлинное несовпадение → `FAIL`; пустой blob по `e3b0c442…b855` → `PASS` — **green** |
| R25 | Codex P2 #4596961721 | TC-42 | вложения и git-файлы в одном правиле | E5-A отдельно; G1 и G2 к вложениям не применяются — **green** |
| R26 | четыре P2 PR #63 | TC-17…TC-25 | green в `0cb5757c…` | без регрессии: S6.1 цепочка RESUME, S7 lease, S5 `base.ref`, E6 пустой файл сохранены дословно по смыслу; изменена только применимость S6.1 до ASSIGN |
| R27 | F1–F4 | TC-13, TC-27…TC-31 | green в `0cb5757c…` | без регрессии: цитата TC-13, S2/S4, E3/S9 запрещённые пути, E4 `permalink_not_head`, §2 независимость сохранены |
| R28 | AC-2 #68 | TC-26 | адаптеры закрепляли `4af7e921…70f1` и `80267ce3…61dd` | адаптеры закрепляют новые хэши; старые → `BLOCKED (canonical_skill_mismatch)` |

## I. Покрытие критериев Issue #68

| AC #68 | Где |
|---|---|
| AC-1 PREFLIGHT, CLAIM, ASSIGN до записи | TC-32; HANDOFF задачи (self_checks) |
| AC-2 шесть добавленных файлов, хэши адаптеров | README §10; R28; HANDOFF |
| AC-3 первый CLAIM, коллизии | preflight S6.1, S7, §4; TC-17, TC-32, TC-33; R16–R18 |
| AC-4 возобновлённая QA | evidence-qa §0, §1, §2, E9, §6; TC-34, TC-35; R19–R20 |
| AC-5 permalink ≠ сырые байты | evidence-qa §2 п.3, §3, E4, E5-G, E5-A, E6; TC-36, TC-37; R21–R22 |
| AC-6 регрессии адреса, байтов, API, сети, вложений | TC-37…TC-42; R22–R25 |
| AC-7 согласованность, хэши, без регрессии | README §9, §10; §H R26–R28 |
| AC-8 история, `NOT_RUN`/`NOT_VERIFIED`, v1/v2 | разделы A–F не переписаны (дополнены только шапка и TC-17); README §9 |
| AC-9 HANDOFF, PR, матрица | §H; HANDOFF задачи |
| AC-10, AC-11 независимый QA, G2, PR #63/#66 | вне scope автора: не выполняются этой редакцией |

Разделы G–I тоже выполняются только чтением: нельзя публиковать сообщения, скачивать вложения или менять Issues.

---

## J. Codex P2 к PR #72 (Issue #75)

`D1…`, `D2…`, `D3…` — условные ID комментариев с решениями владельца, `session_R1…`, `session_R2…` — условные сессии, `X` — условный 40-hex `head_sha`, `H` — условный хэш SPEC. Это заполнители для синтетических входов, а не реальные значения. Опорные записи #75:
- три замечания: [#4611549410](https://github.com/iprus2026-tech/taxi-dashboard/pull/72#discussion_r4611549410) (preflight S4), [#4611549429](https://github.com/iprus2026-tech/taxi-dashboard/pull/72#discussion_r4611549429) (evidence-qa §2 п.1), [#4611549445](https://github.com/iprus2026-tech/taxi-dashboard/pull/72#discussion_r4611549445) (evidence-qa E5-G2), все `created_at` 2026-11-18T09:18Z;
- [SPEC #6974576608](https://github.com/iprus2026-tech/taxi-dashboard/issues/75#issuecomment-6974576608) — `fde63f7ea278586373312cfa571951832bfacfe0a5e9de548307440c28c55566`, 5266 байт;
- [G0 #6974769442](https://github.com/iprus2026-tech/taxi-dashboard/issues/75#issuecomment-6974769442) — единственное решение G0 задачи, `APPROVE`, `created_at = updated_at` 2026-11-18T09:41:56Z.

Все кейсы этого раздела — `DOC_REVIEW`: логическая проверка текста Skill «вход → итог», runtime `NOT_RUN`. Исполняемых тестов у Skills нет, CI их не запускает.

### TC-43 [S] Последнее решение G0 важнее раннего `APPROVE`

Все решения ниже — действительные (`agent: owner`, отдельный неотредактированный комментарий, корректный `ts`), если не сказано иное. Порядок — по `created_at`.

| Вход | Ожидается |
|---|---|
| A. `D1` `APPROVE` по `H`, затем `D2` `REJECT` по `H` | действующее — `D2` → `BLOCKED (g0_rejected)`; `D1` прав не даёт |
| B. `D1` `APPROVE` по `H`, затем `D2` `CHANGES` по `H` | действующее — `D2` → `BLOCKED (g0_changes_requested)` |
| C. `D1` `APPROVE`, `D2` `REJECT`, затем `D3` `APPROVE` по `H` с `target_branch` | действующее — `D3` → S4 `PASS` |
| D. `D1` `APPROVE` по `H`, затем `D2` `REJECT` по другому хэшу или без хэша | `D2` всё равно блокирует (fail closed) → `BLOCKED (g0_rejected)`, расхождение раскрывается |
| E. `D1` `APPROVE` по старому хэшу, затем `D2` `APPROVE` по `H` | действующее — `D2` → `PASS`; при наоборот (`D2` по старому хэшу) → `BLOCKED (spec_changed)` |
| F. `D1` `APPROVE`, ASSIGN, затем `D2` `REJECT`; исполнитель запускает `PRE_WRITE` или `PRE_HANDOFF` | `BLOCKED (g0_rejected)`: S4 пересчитывается в каждой контрольной точке, работа останавливается |

### TC-44 [S] Решения G0: недействительные и неоднозначные

| Вход | Ожидается |
|---|---|
| A. `D1` `APPROVE` действителен, позже `D2` `REJECT` отредактирован (`updated_at ≠ created_at`) | недействительный отказ молча не отбрасывается → `STOP (owner_decision_ambiguous)` |
| B. `D1` `APPROVE`, позже `D2` `CHANGES` с `agent: gpt` или в relay от агента | `STOP (owner_decision_ambiguous)`: прав не даёт и не отбрасывается молча |
| C. `D1` `REJECT` действителен, позже `D2` `APPROVE` отредактирован, от агента или с `ts: 2026-11-18 09:38` (не ISO 8601 UTC) | `D2` недействительно и пропускается; действующее — `D1` → `BLOCKED (g0_rejected)` |
| D. `D1` `APPROVE` и `D2` `REJECT` с одинаковым `created_at` | `STOP (owner_decision_ambiguous)` |
| E. Два действительных `APPROVE` по `H` | действует последнее по `created_at`; его `base_sha` и `target_branch` идут в S4/S5 |
| F. Решения нет, есть только квитанция координатора или label `gate:G0-intake` | `BLOCKED (g0_missing)` (как TC-01, T35) |
| G. Действующее `APPROVE` по `H`, но `base_sha` G0 ≠ `base_sha` SPEC | `BLOCKED (base_mismatch)` (как TC-31) |

### TC-45 [S] RESUME после восстановимого `BLOCKED` → проверка и публикация разрешены

Общий вход: QA-задача, ASSIGN на `session_R1…`, называет `QA-REPORT/1` и `RECEIPT/1` результатом. Затем — одно из сообщений ниже, а после него отдельный неотредактированный RESUME: `agent: gpt`, `assignee: deepseek-qa`, `session: session_R2…`, полный `head_sha`, `spec_sha256` = SPEC QA-задачи = её G0, будущий `lease_until` в пределах максимума. QA-REPORT по этому HANDOFF ещё не публиковался.

| Сообщение до RESUME | Ожидается |
|---|---|
| A. `BLOCKED (lease_expired)` от координатора (§8.1) | цепочка восстановлена → действующая сессия `session_R2…`, §2 п.1 `PASS`; lease — только из RESUME |
| B. `BLOCKED (session_lost)`, HEAD = `head_sha` (§8.2) | `PASS`, как TC-34 |
| C. `BLOCKED` с фактическим HEAD впереди; `head_sha` RESUME = фактический HEAD | `PASS`; дальше E1 сверяет HEAD с `head_sha` HANDOFF: если HANDOFF устарел — `VOID` (§6.4), а не публикация |
| D. Как A, проверка `taxi-preflight` `PRE_WRITE` для `session_R2…` | S6.1 `PASS` (п.3: восстановимый `BLOCKED` → новый RESUME), S7 `PASS` по `lease_until` RESUME |

Во всех случаях `session_R1…` устарела и ничего не публикует; `session_R2…` проходит §2 п.1–3 и E1–E9 заново.

### TC-46 [S] RESUME после `BLOCKED`: отрицательные варианты

| Вход (как TC-45 A, но…) | Ожидается |
|---|---|
| A. RESUME опубликовала сама `session_R2…` (`agent: deepseek-qa`) или `agent: claude-code` | самовозобновление недействительно → `STOP (session_not_assigned)` |
| B. RESUME опубликован **до** `BLOCKED (lease_expired)`, нового RESUME после нет | `BLOCKED` не закрыт → прав нет, `STOP` |
| C. `lease_until` RESUME уже прошёл, или RESUME повторяет истёкший `lease_until` прежнего ASSIGN | `BLOCKED (lease_expired)`: старый lease не используется |
| D. `lease_until` RESUME больше максимума Issue или G0 | lease недействителен → `BLOCKED`, вопрос координатору |
| E. `spec_sha256` RESUME ≠ пересчитанной SPEC, или тело Issue изменилось | `STOP` / `BLOCKED (spec_changed)` |
| F. `head_sha` RESUME ≠ фактическому HEAD ветки (устаревший HEAD) | RESUME недействителен → `STOP` |
| G. После RESUME опубликован новый `BLOCKED`, `REASSIGN`, `RELEASE` или RESUME на `session_R3…` | `session_R2…` не публикует → `STOP`, черновик координатору |
| H. Вместо `BLOCKED` был `REASSIGN` или `RELEASE` действующей сессии, затем RESUME | цепочка прекращена: RESUME прав не даёт, нужен новый ASSIGN → `STOP` |
| I. QA-REPORT или RECEIPT по этому HANDOFF уже опубликован (прежней или любой сессией) | повторной публикации нет → `STOP`, вопрос координатору |
| J. `session_R1…` после RESUME пытается опубликовать QA-REPORT, её lease формально ещё не истёк | `session_R1…` устарела → публикации нет |
| K. `BLOCKED (not_independent)`, затем RESUME на ту же зависимую сессию | причина не устранена → `STOP` / `BLOCKED (not_independent)` |
| L. RESUME выдан сессии автора HANDOFF | полномочия есть, независимости нет → `BLOCKED (not_independent)` (как TC-35 H) |

### TC-47 [H/S] E5-G: G1 и G2 дают одинаковый итог для одного дерева

- **Наблюдение [H]** (автор этой редакции, 2026-11-18T10:19Z, самопроверка, не независимый QA). Commit `8b3a622c49af58409340965ecb5f0849c3befd7f`, `path: .agents/skills/taxi-evidence-qa/SKILL.md`:
  - G1: `git ls-tree 8b3a622c… -- <path>` → `100644 blob 5211efe0b6dc63d955e5fa87a7a4e60c6c8da4fc`;
  - G2: `GET …/git/commits/8b3a622c…` → `sha` = `8b3a622c…`, `tree.sha` = `fdfef94b1bc7eae5d0ed8ad4035abca3469e9375`; `GET …/git/trees/fdfef94b…?recursive=1` → `truncated: false`, запись `mode: 100644`, `type: blob`, `sha: 5211efe0…a4fc`.

  Обоими способами одна и та же запись. Требования `100755` в SPEC нет → `100644` по умолчанию → режим подходит обоим способам.

| Вход (одинаковое дерево `X`, одна запись `path`) | Требование SPEC | G1 | G2 |
|---|---|---|---|
| A. `100644 blob` | нет | `PASS` (режим) | `PASS` (режим) |
| B. `100755 blob` | AC прямо требует `100755` для этого `path` | `PASS` | `PASS` |
| C. `100755 blob` | нет (или только утверждение автора, HANDOFF, общий glob) | `FAIL (not_regular_file)` | `FAIL (not_regular_file)` |
| D. `100644 blob` | AC прямо требует `100755` | `FAIL (not_regular_file)` | `FAIL (not_regular_file)` |
| E. `120000 blob` (symlink) | любое | `FAIL (not_regular_file)` | `FAIL (not_regular_file)` |
| F. `160000 commit` (submodule) | любое | `FAIL (not_regular_file)` | `FAIL (not_regular_file)` |
| G. `040000 tree` (каталог) | любое | `FAIL (not_regular_file)` | `FAIL (not_regular_file)` |

После проверки режима действуют прежние правила: git-хэш байтов = `blob_id`, SHA-256 = ожидаемому (TC-36, TC-40).

### TC-48 [S] E5-G: режим не обходится

| Вход | Ожидается |
|---|---|
| A. HANDOFF утверждает «файл исполняемый, `100755` разрешён», в SPEC такого требования нет; запись `100755` | `FAIL (not_regular_file)` обоими способами: HANDOFF требований не создаёт |
| B. Способ G2 выбран, чтобы обойти `FAIL` по режиму в G1 (или наоборот) | итог тот же: правило одно; выбор способа на итог не влияет |
| C. Contents API или коннектор вернул текст без `mode` из дерева commit | режим не проверен → `NOT_VERIFIED`, а не `PASS` |

---

## K. Регрессия «до (`8b3a622c…`) → после» (`DOC_REVIEW`, red-before / green-after)

«До» — правило на commit `8b3a622c49af58409340965ecb5f0849c3befd7f` (HEAD PR #72, строки по этому commit). «После» — правило в этой редакции. Это логическая проверка текста, а не исполнение кода: runtime `NOT_RUN`, CI не запускался. Самопроверка автора — **не** независимый QA.

| # | Замечание | Кейс | До (`8b3a622c…`) | После |
|---|---|---|---|---|
| R29 | Codex P2 #4611549410 | TC-43 A, B, D, F − | preflight L86: отбор `decision: APPROVE` **до** выбора последнего; `REJECT`/`CHANGES` не попадают в выборку, раннее `APPROVE` → S4 `PASS` — **red** | S4 п.1–3: все решения G0 по `created_at`, действующее — последнее действительное; `REJECT` → `BLOCKED (g0_rejected)`, `CHANGES` → `BLOCKED (g0_changes_requested)` — **green** |
| R30 | Codex P2 #4611549410 | TC-43 C, E; TC-44 E + | последнее `APPROVE` по хэшу → `PASS` | без регрессии: последнее действительное `APPROVE` по хэшу S3 → `PASS` |
| R31 | Codex P2 #4611549410 | TC-44 A–D, F, G − | отредактированный или relay-G0 недействителен; неоднозначность не описана | S4 п.2, п.4: недействительное `APPROVE` пропускается; недействительное или одновременное `REJECT`/`CHANGES` → `STOP (owner_decision_ambiguous)`; `g0_missing`, `base_mismatch` сохранены — **green**, без ослабления |
| R32 | Codex P2 #4611549429 | TC-45 A, C, D + | evidence-qa L49: любой `BLOCKED` обрывает цепочку, исключение только для `session_lost` → после `lease_expired` и HEAD-`BLOCKED` RESUME прав не даёт, `STOP` — **red** | §2 п.1: таблица восстановимых `BLOCKED` (§8.1, §8.2) → новый действительный RESUME возвращает права; preflight S6.1 п.3 согласован — **green** |
| R33 | Codex P2 #4611549429 | TC-45 B + | `session_lost` до RESUME → `PASS` | без регрессии (TC-34) |
| R34 | Codex P2 #4611549429 | TC-46 A–L − | самовозобновление, поддельный и истёкший RESUME → `STOP`; устаревший `head_sha`, повторная публикация, RESUME после `RELEASE` не описаны | все варианты → `STOP` / `BLOCKED`: новый lease только из RESUME, fencing, `head_sha`, идемпотентность, `REASSIGN`/`RELEASE` прекращают цепочку — **green**, без ослабления |
| R35 | Codex P2 #4611549445 | TC-47 B | G1 L121 допускает режим, который прямо требует SPEC; G2 L128 жёстко `mode: 100644` → G1 `PASS`, G2 `FAIL (not_regular_file)` на одном дереве — **red** | единое правило «требуемый режим записи» для G1 и G2 → оба `PASS` — **green** |
| R36 | Codex P2 #4611549445 | TC-47 A, C–G; TC-48 − | `100644` по умолчанию; symlink, submodule, каталог → `FAIL`; `100644` при требовании `100755` и выбор способа для обхода не описаны | одинаковый `FAIL (not_regular_file)` обоими способами; HANDOFF требований не создаёт — **green** |
| R37 | AC-6 #75 | TC-26 | адаптеры закрепляли `d55f6e55…8b5f` (preflight) и `267cebfa…aeb8` (evidence-qa) | адаптеры закрепляют SHA-256 новых канонических файлов; старые → `BLOCKED (canonical_skill_mismatch)` |
| R38 | без регрессии | TC-17…TC-42 | green в `8b3a622c…` | разделы A–I не переписаны (дополнена только шапка); прежние правила S3, S5–S9, E1–E9 сохранены по смыслу |

## L. Покрытие критериев Issue #75

| AC #75 | Где |
|---|---|
| AC-1 PREFLIGHT, CLAIM, ASSIGN, PRE_WRITE, PRE_HANDOFF | CLAIM, ASSIGN и HANDOFF задачи в #75 |
| AC-2 PR #72, три замечания, история | вне файлов: HANDOFF задачи; разделы A–I не переписаны |
| AC-3 S4: последнее решение | preflight S4 п.1–6, шаблон отчёта; TC-43, TC-44; R29–R31 |
| AC-4 RESUME после восстановимого `BLOCKED` | evidence-qa §2 п.1; preflight S6.1 п.3; TC-45, TC-46; R32–R34 |
| AC-5 E5-G2 = G1 по режиму | evidence-qa E5-G «требуемый режим записи», G1 п.3, G2 п.2, E6; TC-47, TC-48; R35–R36 |
| AC-6 хэши адаптеров | `.claude/skills/*/SKILL.md`; R37; HANDOFF |
| AC-7 регрессии | разделы J, K; `DOC_REVIEW`, runtime `NOT_RUN` |
| AC-8 история, scope | HANDOFF задачи |
| AC-9, AC-10 HANDOFF, QA, G2 | вне scope этих файлов: независимый QA и новое личное G2 не выполняются этой редакцией |

Разделы J–L тоже выполняются только чтением: нельзя публиковать сообщения, скачивать вложения или менять Issues.
