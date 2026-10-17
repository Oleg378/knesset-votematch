# elections-research

Исследование открытых данных Кнессета для квиза, который сопоставляет взгляды пользователя с позициями партий.

## С чего начать

1. **[docs/METHODOLOGY.md](docs/METHODOLOGY.md)** — коротко: что делаем и каким принципам следуем.
2. **[docs/SHARED_UNDERSTANDING.md](docs/SHARED_UNDERSTANDING.md)** — рабочий документ: термины, решения со статусами (утверждено / предложение агента / открыто), открытые вопросы.
3. **[docs/PROGRESS.md](docs/PROGRESS.md)** — что сделано, что делаем сейчас, что дальше. Принципы P0 (единообразие) и P1 (агент не решает сам при неоднозначности) обязательны.

## Документы (`docs/`)

| Файл | Что внутри |
| --- | --- |
| [SHARED_UNDERSTANDING.md](docs/SHARED_UNDERSTANDING.md) | Рабочий документ: термины, решения со статусами, открытые вопросы |
| [PROGRESS.md](docs/PROGRESS.md) | Что сделано, что делаем сейчас, что дальше |
| [knesset-data-research.md](local/docs/knesset-data-research.md) | Постановка задачи |
| [report.md](local/docs/report.md) | Результаты: что проверено, цифры, как выгружать |
| [METHODOLOGY.md](docs/METHODOLOGY.md) | Методология: что делаем и принципы (1 страница) |
| [TECHNICAL.md](docs/TECHNICAL.md) | Технический справочник: конвейер, формулы, ограничения данных |
| [archive/](local/docs/archive/) | Архив реестра решений с обоснованиями по ID |
| [knesset-vote-attribution-hypothesis.md](local/docs/knesset-vote-attribution-hypothesis.md) | Гипотеза об атрибутах голосований |
| [jef-task.md](local/docs/jef-task.md) | Разметка через jef (TypeSafe Jev): задание и журнал экспериментов |
| [VERIFICATION.md](docs/VERIFICATION.md) | Протокол проверок: что, когда и кем проверяется |

## Структура

Правила и структура для агентов — [CLAUDE.md](CLAUDE.md).

| Папка | Что внутри |
| --- | --- |
| `pipeline/` | Python: выгрузка из OData Кнессета (только с израильского IP), `build/` → `knesset.duckdb`, разметка Jev, позиции, квиз, экспорт |
| `export/` | Контракт данных для фронта: `quiz_data.v1.json`, JSON Schema, золотые тест-кейсы |
| `web/` | Фронт: React + Vite + TypeScript, статическая сборка. Спецификация — `web/SPEC.md` |
| `jef/` | Направления, разметка, позиции, утверждения квиза |
| `manual/` | Таблицы, которые ведёт человек (списки ЦИК, сопоставление кандидатов, английские имена) |
| `local/research/` | Эксперименты и ранние подходы; не продакшен |
| `local/evidence/` | Схемы сервисов и выборки ответов, подтверждающие выводы |
| `data/`, `knesset.duckdb` | Выгрузки и база (не в git, воспроизводятся скриптами) |

## Быстрый старт

```bash
python3 pipeline/export_votes.py 2021-04-06 2026-11-10 data/export   # ~30 мин, нужен израильский IP
(cd pipeline && python3 fetch_bills.py)                              # законопроекты, инициаторы, комиссии
python3 pipeline/build/build.py                                      # база knesset.duckdb, 2–3 с
# Jev (ключ в .env): pipeline/jev_label.py, pipeline/jev_packages.py, pipeline/jev_split.py; тексты: pipeline/bill_texts.py
# Списки 2026: pipeline/cec_parse.py, pipeline/cec_match.py (страницы комиссии — local/evidence/cec/raw/)
make data                                                            # позиции и экспорт для фронта
```
