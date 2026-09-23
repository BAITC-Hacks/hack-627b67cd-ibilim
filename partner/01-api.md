# API — замороженный контракт

Между бэком (A) и вебом (B). **Менять только правкой этого файла**, иначе второй человек
пишет против несуществующего ответа. База: `/api`. Всё JSON, кроме загрузки фото (multipart).
Ошибки: `{"error": {"code": "...", "message": "..."}}` + соответствующий HTTP-статус.

Авторизации в MVP нет: `?role=teacher` или `?role=student&student_id=3` в query.
Заглушка сознательная, в README названа честно.

---

## GET /api/health
```json
{ "ok": true, "db": "ok", "llm": "ok", "version": "0.1.0" }
```

## GET /api/classes
```json
[{ "id": 1, "name": "7А", "subject": "Алгебра", "grade": 7, "language": "ru", "students": 12 }]
```

## GET /api/classes/{id}/plan
Календарно-тематический план (КТП). Это и есть `lesson` из БД.
```json
{
  "class": { "id": 1, "name": "7А", "subject": "Алгебра" },
  "quarter": 1,
  "lessons": [
    { "id": 14, "date": "2026-09-23", "topic": "Формулы сокращённого умножения",
      "objectives": ["7.2.1.4", "7.2.1.5"], "status": "planned", "has_pack": false },
    { "id": 15, "date": "2026-09-25", "topic": "Разность квадратов",
      "objectives": ["7.2.1.6"], "status": "planned", "has_pack": false }
  ]
}
```
`status`: `planned | done | skipped`.

## GET /api/lessons/{id}
```json
{
  "id": 14, "date": "2026-09-23", "class_id": 1,
  "topic": "Формулы сокращённого умножения",
  "objectives": [
    { "code": "7.2.1.4", "text_ru": "применяет формулы сокращённого умножения",
      "text_kk": "...", "prerequisites": ["7.2.1.1"] }
  ],
  "textbook_ref": "§14, стр. 87",
  "pack": null
}
```

## POST /api/lessons/{id}/pack
Генерирует пакет урока (КСП). Идемпотентно: если пакет есть — возвращает его, если
`?force=true` — перегенерирует. Долгий вызов (до ~30 c), фронт показывает лоадер.
```json
{
  "lesson_id": 14,
  "ksp": {
    "goals": ["7.2.1.4"],
    "outcomes": ["Применяет формулу квадрата суммы", "Различает квадрат суммы и сумму квадратов"],
    "stages": [
      { "minutes": 5, "title": "Актуализация", "activity": "..." },
      { "minutes": 15, "title": "Новый материал", "activity": "..." }
    ],
    "differentiation": "...",
    "assessment": "формативное, дескрипторы ниже"
  },
  "explanation": "Текст объяснения темы для доски...",
  "common_mistakes": [
    { "mistake": "(a+b)² = a²+b²", "why": "...", "fix": "..." }
  ],
  "classwork": [ { "item_id": "c1", "level": 1, "statement": "...", "answer": "..." } ],
  "homework_template": [
    { "template_id": "h1", "objective_code": "7.2.1.4", "level": 2,
      "statement_tpl": "Раскройте скобки: (x + {a})²",
      "params": { "a": [2, 3, 5, 7] },
      "answer_rule": "x^2 + 2*{a}*x + {a}^2",
      "descriptors": ["применяет формулу квадрата суммы — 1 балл",
                      "верно выполняет умножение — 1 балл"] }
  ]
}
```

## POST /api/lessons/{id}/homework
Разворачивает шаблоны в персональные задания для каждого ученика класса:
60% — цели урока, 40% — просевшие цели из `mastery`.
```json
{ "lesson_id": 14, "generated": 12,
  "students": [ { "student_id": 3, "name": "Айдар", "items": 5,
                  "focus": ["7.2.1.4", "7.2.1.1"] } ] }
```

## GET /api/students/{id}/homework?lesson_id=14
Экран ученика.
```json
{
  "student": { "id": 3, "name": "Айдар", "class": "7А" },
  "lesson": { "id": 14, "date": "2026-09-23", "topic": "Формулы сокращённого умножения" },
  "items": [
    { "item_id": 501, "objective_code": "7.2.1.4", "level": 2,
      "statement": "Раскройте скобки: (x + 3)²", "input": "text" },
    { "item_id": 502, "objective_code": "7.2.1.1", "level": 1,
      "statement": "Вычислите: 2³ · 2⁴", "input": "text" }
  ],
  "submitted": false
}
```

## POST /api/submissions
Сдача с веба или телефона. Телеметрия обязательна — она кормит детектор.
```json
{
  "student_id": 3, "lesson_id": 14, "channel": "web",
  "answers": [
    { "item_id": 501, "answer": "x^2 + 6x + 9",
      "telemetry": { "seconds": 92, "pastes": 0, "edits": 7 } }
  ]
}
```
Ответ — результат проверки:
```json
{
  "submission_id": 77,
  "results": [
    { "item_id": 501, "score": 2, "max_score": 2, "correct": true,
      "confidence": 0.96, "needs_teacher": false,
      "descriptors_hit": ["применяет формулу квадрата суммы", "верно выполняет умножение"],
      "feedback": "Верно. Обрати внимание на удвоенное произведение — именно там чаще всего теряют 6x.",
      "ai_index": { "score": 0.08, "level": "low", "reasons": [] } }
  ],
  "mastery_updated": [ { "objective_code": "7.2.1.4", "before": 0.20, "after": 0.55 } ]
}
```

## POST /api/submissions/photo  (multipart/form-data)
Поля: `file` (image), `student_id`, `lesson_id`, `channel=paper|phone`.
Ответ — тот же объект, что у `POST /api/submissions`, плюс:
```json
{ "ocr": { "qr_found": true, "items_detected": 5, "low_confidence_items": [503] } }
```
Если QR не найден — `qr_found: false`, бэк пытается сопоставить по порядку, все результаты
уходят с `needs_teacher: true`.

## GET /api/students/{id}/mastery
```json
{
  "student": { "id": 3, "name": "Айдар" },
  "objectives": [
    { "code": "7.2.1.1", "text": "...", "mastery": 0.92, "status": "ok", "attempts": 6 },
    { "code": "7.2.1.4", "text": "...", "mastery": 0.20, "status": "gap",
      "blocks": ["7.2.2.1"], "attempts": 3 }
  ]
}
```
`status`: `ok | weak | gap | not_taught`.

## GET /api/classes/{id}/mastery
Сводка учителю — то, что краснеет на демо.
```json
{
  "class": { "id": 1, "name": "7А" },
  "objectives": [
    { "code": "7.2.1.4", "text": "...", "avg": 0.41, "failed": 14, "total": 28,
      "recommendation": "10 минут повторения на следующем уроке: разбор (a+b)² на числах" }
  ],
  "students": [ { "id": 3, "name": "Айдар", "gaps": ["7.2.1.4"], "avg": 0.61 } ]
}
```

## GET /api/teacher/review-queue?class_id=1
Очередь «подтвердите»: низкая уверенность проверки или высокий индекс помощи.
```json
[
  { "result_id": 903, "student": "Айдар", "item_id": 501,
    "statement": "...", "student_answer": "...", "proposed_score": 1, "confidence": 0.44,
    "reason": "low_confidence",
    "ai_index": { "score": 0.81, "level": "high",
      "reasons": [
        "метод «подобие треугольников» относится к цели 8.1.2.3 (2 четверть 8 класса)",
        "ответ вставлен из буфера, 4 секунды на задание",
        "освоенность цели у ученика 0.20, работа без помарок"
      ] } }
]
```

## POST /api/results/{id}/confirm
```json
{ "score": 2, "teacher_comment": "зачёт" }
```
→ `{ "ok": true, "mastery_updated": [ ... ] }`

## GET /api/print/homework/{lesson_id}
Отдаёт **HTML-страницу для печати** (не JSON): по листу на ученика, разрыв страницы между
учениками, в углу QR с `student_id|lesson_id|item_ids`. Открывается в новой вкладке,
печатается `window.print()`. MVP-2.

---

## Порядок вызовов на демо

```
GET  /api/classes/1/plan          → учитель видит завтрашний урок
POST /api/lessons/14/pack         → готовый КСП и задания
POST /api/lessons/14/homework     → персональные варианты на класс
GET  /api/students/3/homework     → ученик открывает своё
POST /api/submissions             → сдал, получил разбор
GET  /api/classes/1/mastery       → карта класса покраснела
GET  /api/teacher/review-queue    → карточка с индексом внешней помощи
```
