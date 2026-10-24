# Аудит репозитория: лишние файлы и технические риски

_2026-10-24. Предложения агента [А]; в репозитории пока ничего не изменено. Р1–Р5 решает заказчик; У1–У9 — инженерная
уборка с очевидным решением (принцип P1); Т1–Т5 — риски. До выборов (27.10) предлагается делать только то, что не трогает
сайт (§7)._

## 1. Итог

- В git **2 189 файлов**. Сайт, `make data` и `make check` читают из них около ста (§2).
- `local/` по `README.md` и `.gitignore` «не в git», но в git лежат **1 914 его файлов (87 % репозитория)**. Их
  опубликовали 2026-10-18 через `git add -f` по замечанию внешнего аудита («minor 10»). Сайт на них не ссылается: в
  `export/quiz_texts.json` и `web/src` нет ссылок на GitHub.
- **Процедура живёт в песочнице**: 16 скриптов, которые запускают навыки (`label-check`, `nested-themes`, `new-statements`,
  `split-themes`), лежат в `local/research/scripts/` вперемешку с ~57 разовыми исследованиями.
- `jef/positions/mk_topic_positions.csv` (9 МБ) переписывается каждым `make data`, а дальше его никто не читает:
  **52 версии, 376 МБ в истории**. Локальный `.git` — 233 МБ (5 691 несжатый объект), на GitHub — 55 МБ.
- Все 7 веток (4 локальные и 3 на GitHub) и рабочая копия `.claude/worktrees/site-seo` (129 МБ, из них `node_modules`)
  уже целиком в `main`.
- Состояние на 2026-10-24: `make check` — OK; тесты фронта 257 из 257; проверка типов чистая; ответов людей, ключей и
  `.env` в git нет.

## 2. Что на самом деле работает (остаётся при любом решении)

| Слой | Файлы |
|---|---|
| Сайт | `web/` (`src/`, `public/`, `functions/`, `scripts/`, `index.html`, `how-it-works.html`, конфиги), `export/` (три файла данных, тексты, схемы) |
| `make data` | `pipeline/positions.py`, `labels.py`, `export.py`, `quiz_select.py`, `quiz_match.py`, `quiz_flow.py`, `quiz_report.py`, `texts.py` |
| Проверки | `pipeline/check_invariants.py`, `export/golden.json`, `export/stats.json`, тесты `web/src/**/*.test.ts(x)`, `.github/workflows/web.yml` |
| Входы конвейера в git | `jef/directions/`: `DIRECTIONS_LIST.csv`, `merge3/directions_final.json`, `registry.csv`, `labels/batch_01…12.jsonl`, `labels/split*_choice.jsonl` (10), `split/plan*.json` (10), `labels/overrides.json`, `labels/nested_removals.json`, `labels/packages_agent.jsonl`, `labels/packages_whole.jsonl`, `labels/label_check_coverage.csv`, `relevance/relevance_q2.jsonl`; `jef/quiz/statements.csv`, `statement_meta.csv`; все 7 файлов `manual/` |
| Промежуточные выходы, которые читаются дальше | `jef/positions/list_topic_positions.csv`, `list_coverage.csv`, `government_layer_list.csv`, `list_topic_votes.csv`, `README.md` |
| Входы вне git | `knesset.duckdb` (25 МБ), `data/bills/bill.json` (9,6 МБ), `data/person_to_position_24_25.json` (1,5 МБ), `data/cec/mk_persons.json` |
| Выгрузка (разово, только с израильского адреса) | `pipeline/export_votes.py`, `fetch_bills.py`, `bill_texts.py`, `odata4.py`, `cec_parse.py`, `cec_match.py`, `build/` |
| Процедура | `.claude/skills/*/SKILL.md`, `prompts/`; запись решений проверок — `jef/directions/labels/borderline_resolved.csv` |

## 3. Правило уборки (одно для всех файлов, P0)

Файл остаётся в git, если выполняется хотя бы одно условие:

1. его читает сайт, `make data`, `make check` или сборка фронта;
2. на него ссылается действующее решение: `jef/quiz/statements.csv` (столбец `change`), `jef/directions/registry.csv`
   (`source`), `jef/directions/labels/overrides.json`, SU, TECHNICAL, METHODOLOGY, комментарий в коде конвейера;
3. это процедура: навык, его промпт, скрипт, который навык запускает;
4. это документ из таблицы CLAUDE.md «одно место для каждого вида»;
5. это вход или выход скрипта, которым сделаны данные, лежащие в git (разметка — скрипты Jev; списки кандидатов —
   сохранённые страницы Центральной избирательной комиссии для `cec_parse.py`).

Всё остальное — в `local/` вне git или в истории git.

## 4. Решения заказчика

### Р1. `local/` в git

Состав (подробно — приложение А): `local/research/` — 1 522 файла (проверки меток по утверждениям — 870 файлов в 77
папках, аудиты утверждений — 188, скрипты — 73, остальное — эксперименты); `local/jef/` — 323 (прогоны и тесты Jev 1–7,
слепые входы, черновики слияния тем, старые версии утверждений); `local/evidence/` — 59 (страницы Центральной
избирательной комиссии — 41, копия независимой проверки); `local/docs/` — 5; `local/manual/` — 3.

Дубли: `local/research/independent/` совпадает с `local/evidence/independent_2026-10-12/` файл в файл.

| Вариант | Что в git | Последствия |
|---|---|---|
| а) убрать целиком | ничего (`git rm -r --cached local/`, на диске всё остаётся) | ссылки в WORKLOG (78 строк), `statements.csv` (113), `registry.csv` (59) на GitHub не открываются |
| **б) по правилу §3 (рекомендую)** | около 300 файлов в 38 папках (приложение В) + страницы Центральной избирательной комиссии (правило 5) | проверки меток по утверждениям (870 файлов) упоминает только WORKLOG — они уходят из git |
| б+) как б, плюс всё, на что ссылается WORKLOG | ещё около 900 файлов, в основном проверки меток | публично видно, как проверялась каждая снятая и перевёрнутая метка |
| в) как есть | 1 914 файлов | — |

Сайт не задевает ни один вариант.

### Р2. Выходы `positions.py`, которые дальше никто не читает

| Файл | Размер | Что это |
|---|---|---|
| `jef/positions/mk_topic_positions.csv` | 9 МБ, 52 версии в истории | позиция каждого бывшего депутата по каждой теме |
| `jef/positions/against_camp_examples.csv` | 1,7 МБ, 22 версии | примеры голосов против своего лагеря, для разбора |
| `jef/positions/government_layer_mk.csv` | — | слой правительства по каждому депутату |
| `jef/positions/candidates_notes.csv` | — | пометки по кандидатам |
| `jef/positions/run_log.txt` | — | журнал прогона |

- **а) Рекомендую:** внести в `.gitignore`; файлы пересоздаёт `make data`, `jef/positions/README.md` говорит, что они
  локальные. Эталонные случаи и экспорт не меняются.
- б) Оставить: позиция каждого бывшего депутата видна на GitHub.

### Р3. `docs/archive/`

11 файлов, 350 КБ (PROGRESS, DECISIONS_LOG, METHOD_AUDIT и др.). Всё это есть и в истории git. На архив ссылаются
CLAUDE.md (2 раза), README (1), WORKLOG (4), `web/DATA_REQUESTS.md` (2).

- **а) Рекомендую оставить:** это место, назначенное в CLAUDE.md, и он небольшой.
- б) Удалить; правило CLAUDE.md «закрытый документ — в `docs/archive/`» заменить на «закрытый документ удаляется, в
  WORKLOG — строка с коммитом».

### Р4. История git

- **а) Рекомендую не переписывать.** Репозиторий публичный, сайт публикуется из `main`; переписанная история ломает
  чужие копии и ссылки на коммиты. 55 МБ на GitHub терпимо.
- б) После выборов вычистить `mk_topic_positions.csv` и `local/` из истории (`git filter-repo`, принудительная
  отправка) — только по явному решению.

### Р5. `web/design-variants/` и `web/src/assets/hero-pattern.svg`

`layout-A/` — снимок вёрстки, сохранённый по просьбе заказчика («откати к версии А»); `desktop-C.md/.png`,
`desktop-L.md/.png` (2 МБ картинок) — варианты фона для широкого окна. `hero-pattern.svg` нужен только отклонённому
варианту L и нигде не используется.

- **а) Рекомендую:** поставить метки git (`layout-A` — коммит до системы контрольных точек; `desktop-L`), удалить
  папку и svg, поправить `web/CLAUDE.md` (строки 213, 301) и `web/DECISIONS.md` (E17, E20). Откат остаётся одной
  командой. Изменение в `web/` запускает публикацию той же сборки — делать после выборов.
- б) Оставить как есть.

## 5. Инженерная уборка (без решения заказчика)

| № | Что | Действие | Поправить вместе |
|---|---|---|---|
| У1 | `jef/quiz/GUIDELINES.md` | используется (SU п. 40 [У], навык `new-statements`), но это инструкция агенту, не данные → перенести в `.claude/skills/new-statements/rules.md`. Убрать «рабочая гипотеза заказчика» (в SU правила утверждены), ссылку на `directions_74.csv` (его нет), строку о шести вариантах ответа (на сайте четыре, [У] 2026-10-23) заменить ссылкой на ответы в `export/quiz_texts.json`. Правила 1–9 не меняются | SU п. 40, TECHNICAL (раздел о `statements.csv`), `new-statements/SKILL.md` (шаг 3), `prompts/draft.md` |
| У2 | 16 скриптов процедуры в `local/research/scripts/` (приложение Б) | перенести в `tools/` (в git). Результаты они по-прежнему пишут в `local/research/<tag>/`. Остальные ~57 скриптов — исследования, остаются в `local/` | `ROOT` в каждом скрипте (сейчас на 4 уровня вверх, станет на 2); пути в 6 навыках и промптах, `pipeline/CLAUDE.md`, CLAUDE.md (строка о `local/research/scripts/`) |
| У3 | `pipeline/`: скрипты, которых нет в `make data` | `jef_run.py` (ранний подход, читает `local/research/questions.json`) и `jev_roles.py` (эксперимент) → `local/`. `jev_directions_test.py` (клиент Jev: `ask`, `q_applies`, `q_side`, чтение списка тем — его импортируют все скрипты Jev и `new_statements.py`), `jev_label.py`, `jev_packages.py`, `jev_split.py`, `jev_relevance.py`, `build_registry.py`, `jef/directions/labels/run_rest.py` → `pipeline/labeling/` (как сделаны метки и реестр; не запускаются: у Jev нет кредитов, реестр собран один раз) | `ROOT` и импорты по имени модуля в перенесённых скриптах и в `tools/new_statements.py`; `pipeline/CLAUDE.md` «Order» |
| У4 | мёртвые файлы в `jef/` | удалить `jef/positions/candidate_directions_74.csv` (от набора из 74 утверждений, 2026-10-17; никто не пишет и не читает) и `jef/quiz/pilot_answers.csv` (пустой русский лист на 65 старых утверждений, сейчас их 123). `jef/quiz/match_calibration.txt` (вывод подбора K, решено K = 0) → `quiz_match.py --calibrate` пишет в `local/research/` | строка «Usage» в `pipeline/quiz_match.py` |
| У5 | `docs/DESIGN_BRIEF.md` | устарел (шкала из пяти ответов, «8 общих + 7 уточняющих»), ни один документ не ссылается → `docs/archive/` | строка в `docs/archive/README.md` |
| У6 | страницы Центральной избирательной комиссии `local/evidence/cec/raw/` (38 файлов) | единственная копия источника списков кандидатов в git (правило 5) → `manual/cec_pages/` | `pipeline/cec_parse.py` (докстринг), TECHNICAL |
| У7 | git | удалить локальные ветки `site-seo`, `texts-from-export`, `trial-list-details`, `web/figma-layout` и worktree `.claude/worktrees/site-seo` (незакоммиченного нет); ветки на GitHub `texts-from-export`, `web/figma-layout`, `web/list-details` — только с ок заказчика; `.claude/worktrees/` → `.gitignore`; локально `git gc` | — |
| У8 | мелочи в коде (pyflakes) | `positions.py`: лишний `import glob`; `quiz_report.py`: лишний `import glob`, неиспользуемые `st`, `nv` (стр. 146), f-строка без подстановок (стр. 159) | `make data` не должен менять `export/` |
| У9 | описания структуры | после Р1: `README.md` и CLAUDE.md («`local/` — не в git»), `local/README.md` (что публикуется и по какому правилу), строка `tools/` в таблице структуры | — |

Файлы разметки, которые читают только скрипты Jev (`full_order.csv`, `packages_input.jsonl`, `packages_skipped.json`,
`packages.jsonl` — отклонённые метки Jev для пакетов, `split_relabel.jsonl`), остаются на месте по правилу 5.

## 6. Технические риски

| № | Риск | Предложение |
|---|---|---|
| Т1 | **Воспроизводимость держится на одном ноутбуке.** `knesset.duckdb` и `data/` (522 МБ) есть только здесь; заново скачать можно только с израильского адреса. Пропадёт ноутбук — `make data` и `make check` не запустить нигде | снимок базы и трёх файлов из `data/`, которые читает конвейер (§2, ~36 МБ), в приватное хранилище; как восстановить — в TECHNICAL |
| Т2 | **Автопроверка на GitHub (`web.yml`) проверяет только фронт.** `make check` и совпадение `export/` с конвейером проверяются только руками; правка `export/*.json` вручную уйдёт на сайт без проверки | после Т1: отдельная проверка — восстановить снимок, `make check`, `make data`, `git diff --exit-code export/` |
| Т3 | **Процедура в песочнице**: навыки запускают скрипты из папки, которая «не в git»; новый скрипт там не попадёт в git, и никто об этом не предупредит | У2 |
| Т4 | **Метки собираются примерно из 35 файлов в порядке, зашитом в `labels.py`**: 12 пачек Jev → 10 этапов разбиения → правки → снятие вложенных тем → релевантность. Работает и проверяется инвариантами, но новый этап требует правки кода; имена — история (`merge3`, `plan2…10`, `split2…10_choice`); один и тот же список 255 тем лежит в двух файлах (`DIRECTIONS_LIST.csv` читает `positions.py`, `merge3/directions_final.json` — `export.py` и `quiz_report.py`) | после выборов: файл-перечень этапов и один файл тем; критерий — `export/` и эталонные случаи не меняются ни на байт |
| Т5 | **Объём документов около 700 КБ.** `web/CLAUDE.md` (33 КБ) загружается в каждую сессию по фронту; `web/DECISIONS.md` — 116 КБ; WORKLOG — 79 КБ | сократить `web/CLAUDE.md` до правил (подробности — в DECISIONS); закрытые раунды WORKLOG — в архив |

Что в порядке: производственный код компактный (около 3,6 тыс. строк Python в `pipeline/`), конвейер и порядок шагов
описаны, инварианты и эталонные случаи работают, фронт покрыт тестами.

## 7. Порядок работ

Каждый шаг — отдельный коммит, после каждого `make check` → OK; коммит — по согласованию.

**До 27.10** (не трогают `export/` и `web/`, публикация сайта не запускается):

1. У1, У4, У5, У8. Проверка: `make data` не меняет `export/`, `make check` OK.
2. У2, У3, У6. Проверка: каждый перенесённый скрипт импортируется (`python3 -c "import …"`), `make check` OK.
3. Р1, Р2 по решению заказчика; затем У9.
4. У7.

**После выборов:** Р5, Р4 (если решено), Т1, Т2, Т4, Т5.

## Приложение А. Состав `local/` в git

| Папка | Файлов | Что внутри |
|---|---|---|
| `local/research/label_check_*` (77 папок) | 870 | проверки меток по каждому утверждению |
| `local/research/statement_audit*` | 188 | аудиты текстов утверждений |
| `local/research/scripts/` | 73 | 16 скриптов процедуры (приложение Б) + исследования |
| остальное `local/research/` | ~390 | эксперименты: веса, центрирование, варианты голосов, порядок вопросов, пороги, новые утверждения по раундам |
| `local/jef/directions/` | 274 | прогоны и тесты Jev 1–7, слепые входы, разметка пакетов агентом, черновики слияния тем, логи пачек |
| `local/jef/quiz/` | 25 | старые версии утверждений (`statements_v2…v4`), черновик 74, сверки |
| `local/jef/h9_check/` | 24 | независимая проверка разметки агентом |
| `local/evidence/` | 59 | страницы Центральной избирательной комиссии (41), независимая проверка 2026-10-12, пилоты Jev |
| `local/docs/`, `local/manual/`, `README.md`, `MOVED.txt` | 10 | ранние документы, каталог вопросов первого подхода |

## Приложение Б. Скрипты процедуры (→ `tools/`)

| Навык | Скрипты |
|---|---|
| `label-check` | `core_full_input.py`, `label_check_drafts_input.py`, `label_check_t5_input.py`, `label_check_step.py`, `flip_check.py`, `add_check_input.py`, `add_check_step.py` |
| `nested-themes` | `theme_overlap.py`, `nested_pairs_input.py`, `nested_apply.py` |
| `new-statements` | `new_statements.py`, `statement_audit.py` (+ `label_check_drafts_input.py`) |
| `split-themes` | `basket_split_input.py`, `basket_split_plan.py`, `basket_choice_run.py`, `basket_choice_apply.py` (+ `label_check_t5_input.py`) |

`flow_core_clar.py` и `k_persona.py` упоминаются в комментариях `quiz_flow.py` и `quiz_match.py` как исследования за
решениями — остаются в `local/` (правило 2).

## Приложение В. Папки `local/`, на которые ссылаются действующие решения (вариант Р1 б)

`local/jef/directions/` (59 файлов), `local/jef/h9_check/` (6), `local/docs/jef-task.md`;
`local/research/`: `a_centering` (19), `audit_split7` (1), `basket_split2` (7), `flip_recheck` (5),
`label_accuracy_sample` (1), `label_check_q5_kkl` (4), `label_check_qr2` (1), `new_statements_round2…6` (47),
`other_camp` (1), `positions_test` (1), `r8_labels` (9), `relevance_impact` (37), `secondary_weight_v2` (34),
`statement_audit`, `statement_audit_new`, `statement_audit_removals`, `statement_audit_round2`,
`statement_audit_q3/q15/q18/q19/q38/q42/q45/q88/q92` (33 вместе), `theme_overlap` (20), `vote_sign_check` (8),
`wording_balance` (2).

Источники ссылок: `jef/quiz/statements.csv`, `jef/directions/registry.csv`, `jef/directions/labels/overrides.json`, SU,
TECHNICAL, METHODOLOGY, `export/WEB_CONTRACT.md`, код `pipeline/`, навыки и их промпты. Ссылки из `jef_run.py` на
`local/research/questions.json` и `gold/` исчезнут вместе с ним (У3).
