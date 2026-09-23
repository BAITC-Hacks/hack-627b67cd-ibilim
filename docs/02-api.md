# API — контракт между бэком и вебом

**Менять только правкой этого файла.** Копия для веба — `partner/01-api.md`, держим байт в байт.
База `/api`, всё JSON. Ошибки: `{"error": {"code": "...", "message": "..."}}` —
`400 bad_request`, `404 not_found`, `409 conflict`, `422 validation_error`, `501 not_implemented`.

Авторизации нет (ТЗ §7 это разрешает): в вебе переключатель «я — бизнес X / я — команда Y»,
`business_id` или `team_id` передаётся в теле запроса или в query.

---

## Справочники

### GET /api/meta
Подписи, фильтры, шкала рейтинга и примеры черновиков — всё, что вебу не надо зашивать.
```json
{
  "industries": ["Агро", "Ритейл", "Логистика", "Образование", "Финансы"],
  "fields": [
    { "key": "title", "label": "Название" },
    { "key": "context", "label": "Контекст" },
    { "key": "need", "label": "Потребность" },
    { "key": "users", "label": "Пользователи" },
    { "key": "data", "label": "Данные и материалы" },
    { "key": "constraints", "label": "Ограничения" },
    { "key": "expected_result", "label": "Ожидаемый результат" },
    { "key": "success_criteria", "label": "Критерии успеха" },
    { "key": "contact", "label": "Контакт" },
    { "key": "interaction_format", "label": "Формат взаимодействия" }
  ],
  "indicators": [
    { "key": "context_need", "label": "Контекст и потребность", "max": 20, "fields": ["context", "need"] },
    { "key": "data", "label": "Данные и материалы", "max": 20, "fields": ["data"] },
    { "key": "expected_result", "label": "Ожидаемый результат", "max": 15, "fields": ["expected_result"] },
    { "key": "success_criteria", "label": "Критерии успеха", "max": 15, "fields": ["success_criteria"] },
    { "key": "constraints", "label": "Ограничения", "max": 10, "fields": ["constraints"] },
    { "key": "users", "label": "Пользователи", "max": 10, "fields": ["users"] },
    { "key": "business_link", "label": "Связь с бизнесом", "max": 10, "fields": ["contact", "interaction_format"] }
  ],
  "levels": [
    { "key": "draft", "label": "черновик", "min": 0, "max": 39 },
    { "key": "working", "label": "рабочая", "min": 40, "max": 69 },
    { "key": "ready", "label": "готовая", "min": 70, "max": 89 },
    { "key": "priority", "label": "приоритетная", "min": 90, "max": 100 }
  ],
  "draft_examples": [ { "industry": "Агро", "text": "Хотим понимать, какие поля скоро потребуют полива" } ]
}
```

### GET /api/businesses
```json
[ { "id": 1, "name": "ТОО «Агро Север»", "industry": "Агро" } ]
```

### GET /api/teams
```json
[ { "id": 2, "name": "DataCats", "interests": ["агро", "аналитика"], "skills": ["python", "ml"],
    "technologies": ["FastAPI", "pandas"], "points": 0 } ]
```

---

## Задача: от черновика до публикации

Во всех ответах этого раздела — один объект **Task**:
```json
{
  "id": 7,
  "status": "card",
  "business": { "id": 1, "name": "ТОО «Агро Север»" },
  "industry": "Агро",
  "draft_text": "Хотим понимать, какие поля скоро потребуют полива",
  "card": {
    "title": "Прогноз полива по полям", "context": "Хотим понимать, какие поля скоро потребуют полива",
    "need": "", "users": "", "data": "Выгрузка с датчиков влажности за 2 года, CSV",
    "constraints": "", "expected_result": "", "success_criteria": "", "contact": "", "interaction_format": ""
  },
  "sources": {
    "context": "Хотим понимать, какие поля скоро потребуют полива",
    "data": "есть выгрузка с датчиков влажности за 2 года, CSV",
    "title": "manual"
  },
  "questions": [
    { "id": 31, "field": "data", "text": "Какие данные уже есть: датчики, выгрузки, карты полей?",
      "answer": "есть выгрузка с датчиков влажности за 2 года, CSV" }
  ],
  "rating": { "score": 38, "level": "draft", "level_label": "черновик", "breakdown": [], "missing": [], "next_best": [] },
  "confirmed": false,
  "official": null,
  "position": { "place": 3, "of": 6, "projected": true },
  "audience": { "recommended": false, "teams": [ { "id": 2, "name": "DataCats", "match": ["агро", "полив"] } ] },
  "privacy": [
    { "kind": "iin", "field": "data", "message": "в тексте был ИИН — скрыт до публикации и до отправки в ИИ",
      "hint": "не публикуйте идентификаторы людей: команде нужны обезличенные данные" }
  ],
  "history": [
    { "at": "2026-09-23T13:40:00Z", "event": "draft", "score": 12, "level": "draft", "confirmed": false },
    { "at": "2026-09-23T13:42:10Z", "event": "answers", "score": 38, "level": "draft", "confirmed": false }
  ],
  "ai": { "mode": "llm", "attempts": 1, "warnings": [] },
  "proposals": 0,
  "published_at": null
}
```
- `status`: `new` (черновик разобран, ждём ответов) → `card` (карточка собрана) → `published`.
- `card` — всегда все 10 ключей из `meta.fields`; незаполненное поле — `""`.
- `sources[поле]` — **дословная цитата** из черновика или ответа, на которой ИИ основал значение,
  либо `"manual"`, если поле правил человек. ИИ-значение без найденной в тексте цитаты
  отбрасывается и пишется в `ai.warnings` — так ИИ не добавляет фактов от себя (ТЗ §5).
- `rating` — рейтинг **текущей** карточки (предпросмотр); `official` — `{ "score", "level" }`
  последней **подтверждённой** версии или `null`. Каталог сортирует по `official`.
- `position` — место в каталоге: у опубликованной задачи — по `official`; у неопубликованной
  `projected: true` — куда она встанет по текущему `rating`, если её подтвердить и опубликовать
  («опубликуйте — будете 3-й из 6»). Это и есть «рейтинг влияет на позицию» из ТЗ §9.
- `audience.teams` — команды, чьи интересы, навыки и технологии совпали с задачей;
  `recommended: true`, если по текущему рейтингу задача уровня `working` и выше — только тогда ей
  разрешено попадать в рекомендации этим командам (ТЗ §4). Бизнес видит, **кому** покажут задачу.
- `privacy` — что нашла проверка персональных данных. `kind`: `iin` (ИИН с верной контрольной
  цифрой) и `card` (номер карты по алгоритму Луна) **маскируются** в тексте до сохранения и до
  отправки в ИИ; `personal_data` (ФИО, паспорт, адрес, диагноз, зарплата…) — предупреждение,
  пропадает, когда в тексте сказано, что данные обезличены. Закон РК «О персональных данных и их защите».
- `history.event`: `draft | answers | edit | confirm` — лента роста рейтинга для демо.
- `ai.mode`: `llm` или `stub` — API недоступен или ответ модели не прошёл проверку, сработала
  локальная заглушка. `attempts` — сколько раз спрашивали модель.

Объект **Rating** — считает код по правилам `docs/03-rating.md`, не модель:
```json
{
  "score": 48, "level": "working", "level_label": "рабочая",
  "breakdown": [
    { "key": "context_need", "label": "Контекст и потребность", "points": 16, "max": 20,
      "explain": "описано, что происходит сейчас и что нужно изменить",
      "hint": "добавьте цифры: сколько времени или денег теряется сейчас" }
  ],
  "missing": ["data", "success_criteria"],
  "next_best": [
    { "key": "data", "label": "Данные и материалы", "gain": 20,
      "hint": "укажите, какие данные есть: выгрузки, примеры, API",
      "then": { "score": 68, "level": "working", "place": 2, "of": 6, "teams": ["DataCats", "RouteLab"] } }
  ],
  "next_level": { "key": "ready", "label": "готовая", "points_needed": 22 },
  "penalties": [
    { "key": "duplicate", "label": "Повтор текста", "points": 6,
      "explain": "одинаковый текст в полях «Данные» и «Ожидаемый результат» — засчитан один раз" }
  ]
}
```
`penalties` — защита от накрутки: повтор текста в разных полях, набор ключевых слов без смысла,
отписки («см. выше», «уточним позже»), бессмысленный набор букв. `score` уже за вычетом штрафов.
`next_best[].then` — **что даст улучшение**: рейтинг, место в каталоге и команды, которым задачу
начнут рекомендовать, если довести этот показатель до максимума. Есть только в `Task.rating`;
в `POST /api/rating/preview` — без `then`.
`breakdown` — все 7 показателей по порядку `meta.indicators`; `hint` пустой, если балл максимальный.
`missing` — ключи показателей с 0 баллов. `next_best` — что даст больше всего баллов, по убыванию `gain`.
`next_level` — сколько баллов не хватает до следующего уровня; `null` на `priority`.

### POST /api/tasks
```json
{ "business_id": 1, "industry": "Агро", "draft_text": "Хотим понимать, какие поля скоро потребуют полива" }
```
→ `201`, Task со `status: "new"`: ИИ перенёс в карточку то, что есть в черновике, и задал
**не меньше трёх** вопросов (`questions`) — по самым «дорогим» недостающим показателям.
`400` — пустой черновик.

### GET /api/tasks/{id}
→ Task.

### GET /api/tasks?business_id=1
→ `[Task]` — «мои задачи» бизнеса, новые сверху.

### POST /api/tasks/{id}/answers
```json
{ "answers": [ { "question_id": 31, "answer": "есть выгрузка с датчиков влажности за 2 года, CSV" } ] }
```
→ Task со `status: "card"`, `confirmed: false`: ИИ собрал карточку из черновика и ответов.
Пустой ответ — вопрос пропущен.

### PUT /api/tasks/{id}/card
```json
{ "card": { "title": "Прогноз полива по полям", "success_criteria": "точность прогноза не ниже 80%" } }
```
→ Task: ручная правка любых полей (можно часть), `sources` этих полей — `"manual"`,
`confirmed: false`, `rating` пересчитан. `official` не меняется до подтверждения.

### POST /api/tasks/{id}/confirm
→ Task: бизнес подтвердил текущую карточку — `confirmed: true`, `official` пересчитан, в
`history` событие `confirm`. У опубликованной задачи позиция в каталоге меняется сразу.

### POST /api/tasks/{id}/publish
→ Task со `status: "published"`. `409 conflict` — карточка не подтверждена или нет названия.
Низкий рейтинг публикации не мешает: задача видна в каталоге с пометкой «требует уточнения».

### POST /api/tasks/{id}/assist
**Помощник карточки**: для 2–3 самых «дорогих» слабых полей предлагает готовую формулировку —
только из слов бизнеса (черновик, ответы, другие поля), с цитатой и проверкой, как у карточки.
Каждое предложение уже просчитано: сколько баллов даст. Ничего не сохраняет — «Применить» делает
веб обычным `PUT /api/tasks/{id}/card` с `{ "card": { field: value } }`.
```json
{ "suggestions": [
    { "field": "success_criteria", "label": "Критерии успеха", "current": "",
      "value": "Экономия воды на 15% при точности прогноза не ниже 80%",
      "quote": "Хотим экономить воду на 15%, точность прогноза от 80%", "gain": 15, "then_score": 77 } ],
  "ai": { "mode": "llm", "attempts": 1, "warnings": [] } }
```
Предложения с выдуманными фактами отброшены (`ai.warnings`), без прироста балла — не показываются.
Без ключа — `suggestions: []` и честная пометка в `ai.warnings`: помощник работает только с ИИ.

### POST /api/tasks/{id}/student-check
**ИИ-студент**: модель играет студенческую команду и пробует спланировать первую неделю только по
карточке. Каждое место, где пришлось додумать, — допущение с вопросом бизнесу. Ловит не пустые
поля, а мутные («данные — выгрузка», но в каком формате и за какой период?). Ничего не сохраняет.
```json
{ "can_start": false,
  "first_week": ["Собрать и изучить выгрузку с датчиков", "Сделать прототип прогноза и дашборд"],
  "assumptions": [ { "field": "data", "assumption": "выгрузка в CSV за один сезон",
                     "question": "Какие поля в выгрузке и за какой период?" } ],
  "ai": { "mode": "llm", "attempts": 1, "warnings": [] } }
```
`can_start: true` — допущений нет, команда может начать без уточнений. Без ключа — заглушка:
допущения по пустым полям.

### POST /api/rating/preview
```json
{ "card": { "context": "...", "need": "..." } }
```
→ Rating. Живой пересчёт, пока бизнес печатает; ничего не сохраняет.

---

## Каталог

### GET /api/catalog?industry=Агро&level=ready
Все опубликованные задачи, по убыванию `official.score` (при равенстве — новее выше).
Фильтры необязательные. Низкий рейтинг задачу не скрывает.
```json
[
  { "id": 7, "title": "Прогноз полива по полям", "industry": "Агро", "business": "ТОО «Агро Север»",
    "summary": "Хотим понимать, какие поля скоро потребуют полива…", "score": 81, "level": "ready",
    "level_label": "готовая", "needs_clarification": false, "highlight": false,
    "proposals": 2, "published_at": "2026-09-23T13:50:00Z" }
]
```
`needs_clarification` — уровень `draft` (0–39); `highlight` — уровень `priority` (90–100).

### GET /api/teams/{id}/recommendations
Подсказка команде: опубликованные задачи уровня `working` и выше, совпадающие с её интересами,
навыками и технологиями. Каталог это не ограничивает.
```json
[ { "task_id": 7, "title": "Прогноз полива по полям", "score": 81, "level": "ready", "match": ["python", "агро"] } ]
```

---

## Отклики и выбор бизнеса

Объект **Proposal**:
```json
{ "id": 12, "task_id": 7,
  "team": { "id": 2, "name": "DataCats", "skills": ["python", "ml"], "technologies": ["FastAPI", "pandas"] },
  "idea": "Модель влажности почвы по данным датчиков и погоде", "plan": "1) EDA 2) модель 3) дашборд",
  "timeline": "2 недели", "link": "https://github.com/datacats/irrigation",
  "status": "submitted", "comment": "", "created_at": "2026-09-23T14:05:00Z", "decided_at": null }
```
`status`: `submitted | accepted | rejected`. `team.skills` и `team.technologies` — чтобы бизнес
сравнивал отклики не только по тексту.

### POST /api/tasks/{id}/proposals
```json
{ "team_id": 2, "idea": "...", "plan": "...", "timeline": "2 недели", "link": "https://github.com/..." }
```
→ `201`, Proposal. Любая команда, на любую опубликованную задачу, без лимита на число откликов.
`409` — задача не опубликована; `400` — пустые идея, план или срок, ссылка не `http(s)://`.

### GET /api/tasks/{id}/proposals
→ `[Proposal]` — экран бизнеса: сравнить отклики.

### GET /api/teams/{id}/proposals
→ `[Proposal]` — экран команды: мои отклики и решения по ним.

### POST /api/proposals/{id}/decision
```json
{ "decision": "accept", "comment": "Нравится план с пилотом на одном поле" }
```
→ Proposal. `decision`: `accept | reject`. Только ручное решение бизнеса: можно принять
несколько откликов или ни одного. Автоматического назначения нет и не будет.

### POST /api/proposals/{id}/milestones — MVP-2
```json
{ "title": "Прототип показан бизнесу" }
```
→ `{ "proposal_id": 12, "team_points": 10 }` — бизнес подтвердил этап, команда получила баллы
за фактический прогресс (шаг 8 ТЗ). Только для `accepted`, иначе `409`.

---

## Панель программы AI Sana

### GET /api/stats
Агрегаты для владельца программы, без персональных данных.
```json
{
  "tasks": { "total": 7, "published": 6, "avg_score": 73.5, "avg_growth": 58.0,
             "by_level": [ { "key": "draft", "label": "черновик", "count": 1 } ] },
  "industries": [ { "industry": "Агро", "tasks": 2, "avg_score": 64.0, "proposals": 3 } ],
  "proposals": { "total": 6, "accepted": 2, "rejected": 1, "pending": 3, "avg_hours_to_decision": 1.5 },
  "teams": [ { "id": 2, "name": "DataCats", "points": 10, "proposals": 2, "accepted": 1, "skills": ["python"] } ]
}
```
`avg_growth` — насколько в среднем вырос рейтинг задачи от черновика до последней версии: эффект
геймификации. `avg_hours_to_decision` — как быстро бизнес отвечает студентам.

---

## ИИ

### GET /api/ai/spec
То, что ТЗ §5 требует показать: промпты, формат входа и выхода, обработка некорректного ответа.
```json
{
  "mode": "llm", "model": "gpt-5",
  "calls": [
    { "name": "analyze_draft", "system": "...", "input_example": {}, "output_schema": {} },
    { "name": "build_card", "system": "...", "input_example": {}, "output_schema": {} }
  ],
  "invalid_response": "строгая JSON-схема → до 2 повторов → проверка цитат → локальная заглушка"
}
```

---

## Порядок вызовов на демо (ТЗ §11)
```
POST /api/tasks                    → слабый черновик, рейтинг низкий, 3+ вопроса
POST /api/tasks/{id}/answers       → карточка собрана, рейтинг вырос
PUT  /api/tasks/{id}/card          → бизнес дописал по подсказкам next_best, рейтинг ещё выше
POST /api/tasks/{id}/confirm       → подтвердил
POST /api/tasks/{id}/publish       → задача в каталоге на своей позиции
GET  /api/catalog                  → видно место задачи среди остальных
POST /api/tasks/{id}/proposals     → команда откликнулась
GET  /api/tasks/{id}/proposals     → бизнес сравнивает
POST /api/proposals/{id}/decision  → принял или отклонил вручную
```
