# Модель данных

SQLite, файл `backend/ibilim.db`. Всё сходится на `objective.code` — это единственный ключ,
связывающий программу, урок, задание, проверку и пробел ученика.

DDL лежит в `backend/app/schema.sql` и является источником правды; здесь — смысл полей.

## objective — цель обучения

Единица государственной программы. Код: `класс.раздел.подраздел.номер` → `7.2.1.4`.

| поле | смысл |
|---|---|
| `code` | PK, `7.2.1.4` |
| `grade`, `subject` | 7, «Алгебра» |
| `section`, `subsection` | «Многочлены» / «Формулы сокращённого умножения» |
| `quarter` | четверть из долгосрочного плана |
| `hours` | часы на раздел, нужны планировщику |
| `text_ru`, `text_kk` | формулировка цели на двух языках |
| `prerequisites` | JSON-массив кодов: на что опирается цель |
| `order_index` | порядок внутри четверти |

`prerequisites` — то, на чём держится и персональная домашка, и детектор. Размечается один раз:
LLM предлагает, человек подтверждает.

## textbook_unit — мост к бумажному учебнику

`textbook_id`, `label` («§14, стр. 87»), `objective_codes` (JSON).
**Только метаданные.** Контента учебника в базе нет и не будет.

## klass, student, schedule_slot, calendar

- `klass`: `name` («7А»), `grade`, `subject`, `language` (`ru|kk`), `textbook_id`.
- `student`: `klass_id`, `name`. Ни почты, ни телефона — принципиально.
- `schedule_slot`: `klass_id`, `weekday` (1–7), `lesson_no`. Из него планировщик берёт даты.
- `calendar`: `quarter`, `starts_on`, `ends_on`, `holidays` (JSON дат).

## lesson — это и есть КТП

| поле | смысл |
|---|---|
| `id`, `klass_id`, `date` | одна строка = один урок в расписании |
| `objective_codes` | JSON-массив кодов на этот урок |
| `topic` | человеческое название темы |
| `status` | `planned | done | skipped` (пропущенные двигают план) |

## lesson_pack — сгенерированный урок

`lesson_id` (unique), `ksp` (JSON), `explanation`, `common_mistakes` (JSON),
`classwork` (JSON), `homework_template` (JSON), `model`, `created_at`.

Кеш генерации живёт отдельно: `gen_cache(key, payload)`, где
`key = sha256(objective_code + level + language + prompt_version)`. Один сгенерированный
вариант обслуживает тысячи классов — на этом держится экономика (см. `docs/01-product.md`).

## assignment_item — конкретное задание конкретному ученику

| поле | смысл |
|---|---|
| `student_id`, `lesson_id`, `objective_code`, `level` (1–3) | адресация |
| `seed` | параметры варианта: у каждого свои числа |
| `statement` | развёрнутое условие |
| `answer` | эталон (строка-выражение для sympy или текст) |
| `descriptors` | JSON: критерии с баллами |
| `origin` | `today` (цель урока) или `gap` (добор пробела) |

## submission / item_result

- `submission`: `student_id`, `lesson_id`, `channel` (`web|phone|paper`), `created_at`, `raw` (JSON/путь к фото).
- `item_result`: `submission_id`, `item_id`, `answer_raw`, `score`, `max_score`, `correct`,
  `confidence`, `needs_teacher`, `descriptors_hit` (JSON), `feedback`,
  `ai_index`, `ai_reasons` (JSON), `telemetry` (JSON), `teacher_confirmed`.

`confidence` ниже порога (0.7) → `needs_teacher = 1` и строка уходит в очередь учителю.
Никаких автоматических санкций по `ai_index` — только очередь.

## mastery — карта пробелов

`student_id`, `objective_code`, `value` (0…1), `attempts`, `updated_at`. PK — пара.

Обновление после каждой проверки, экспоненциальное сглаживание:

```
value = round(0.6 * value_old + 0.4 * (score / max_score), 3)
```

Первая попытка — `value = score / max_score`. Статус для UI:
`>= 0.8 ok`, `0.5–0.8 weak`, `< 0.5 gap`, нет записи — `not_taught`.

## Демо-данные (сид)

Класс 7А, 12 учеников, один раздел алгебры (6 целей), три профиля:
сильный (mastery 0.85+), средний, отстающий с явным провалом по `7.2.1.4`.
Имена вымышленные. Профили нужны, чтобы персональная домашка на демо действительно
получалась разной — это видно на экране и это главный кадр.
