"""ИИ-функции кейса: разбор черновика с уточняющими вопросами и сборка карточки из ответов.

Владелец — Claude. Правила ТЗ §5: ИИ не добавляет фактов — у каждого значения есть дословная
цитата из текста пользователя, код её проверяет; итог правит и подтверждает человек.
Нет API или ответ не прошёл проверку — локальная заглушка, это видно в ai.mode.
"""

import json
import re

from . import llm, rating

FIELDS = rating.FIELDS
MIN_QUESTIONS = 3

LABELS = {
    "title": "Название", "context": "Контекст", "need": "Потребность", "users": "Пользователи",
    "data": "Данные и материалы", "constraints": "Ограничения",
    "expected_result": "Ожидаемый результат", "success_criteria": "Критерии успеха",
    "contact": "Контакт", "interaction_format": "Формат взаимодействия",
}

# банк вопросов заглушки и добор, если модель спросила меньше трёх
QUESTION_BANK = {
    "context": "Что происходит сейчас: как задача решается сегодня и в чём проблема?",
    "need": "Что именно нужно изменить или получить? (например: сократить ручную обработку заявок вдвое)",
    "data": "Какие данные или материалы вы дадите команде? (выгрузки, примеры, API, документы — и за какой период)",
    "expected_result": "Какой результат вы ждёте от команды? (прототип, модель, дашборд, бот, отчёт)",
    "success_criteria": "По каким измеримым признакам вы примете решение? (например: точность от 80%, ответ быстрее 1 минуты)",
    "constraints": "Какие есть ограничения: сроки, технологии, доступы, бюджет?",
    "users": "Кто будет пользоваться решением и сколько их? (например: 20 операторов колл-центра)",
    "contact": "Как с вами связаться? (email, телефон или Telegram)",
    "interaction_format": "Как будет устроена работа с командой: консультации, созвоны, обратная связь?",
    "title": "Как коротко назвать задачу?",
}

# порядок вопросов: сначала самые «дорогие» показатели ТЗ §4
_FIELD_ORDER = [f for _, _, _, fields in sorted(rating.INDICATORS, key=lambda i: -i[2]) for f in fields] + ["title"]

_FIELD_ITEM = {
    "type": "object",
    "properties": {
        "field": {"type": "string", "enum": FIELDS},
        "value": {"type": "string"},
        "quote": {"type": "string"},
    },
    "required": ["field", "value", "quote"],
    "additionalProperties": False,
}

ANALYZE_SCHEMA = {
    "type": "object",
    "properties": {
        "fields": {"type": "array", "items": _FIELD_ITEM},
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"field": {"type": "string", "enum": FIELDS}, "question": {"type": "string"}},
                "required": ["field", "question"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["fields", "questions"],
    "additionalProperties": False,
}

CARD_SCHEMA = {
    "type": "object",
    "properties": {"fields": {"type": "array", "items": _FIELD_ITEM}},
    "required": ["fields"],
    "additionalProperties": False,
}

_RULES = (
    "Используй только сведения из текста пользователя. Для каждого заполненного поля верни "
    "value — коротко и по-деловому — и quote: точную копию фрагмента текста пользователя, символ "
    "в символ, без перефразирования, на которой основано значение. Не добавляй фактов, цифр, "
    "сроков, данных и контактов, которых нет в тексте; нет сведений — не включай поле. "
    "Пиши по-русски."
)

ANALYZE_SYSTEM = (
    "Ты помогаешь представителю бизнеса оформить задачу для студенческих команд. Тебе дают "
    "черновик — описание потребности своими словами.\n"
    "1) Разложи по полям карточки то, что в черновике сказано явно. " + _RULES + "\n"
    "2) Задай от 3 до 5 уточняющих вопросов о том, чего не хватает. Начинай с самых весомых "
    "показателей рейтинга: контекст и потребность (20), данные и материалы (20), ожидаемый "
    "результат (15), критерии успеха (15), ограничения (10), пользователи (10), связь с бизнесом (10). "
    "Каждый вопрос — одно короткое предложение (до 20 слов) про одно поле, простым языком "
    "бизнеса, без технических терминов. В скобках — короткий пример ответа (3–8 слов), "
    "реалистичный для казахстанской компании. Не спрашивай о том, что уже есть в черновике."
)

CARD_SYSTEM = (
    "Ты собираешь карточку бизнес-задачи из черновика и ответов бизнеса на уточняющие вопросы. "
    "Один ответ может заполнять несколько полей. " + _RULES
)


# --- проверка «без выдуманных фактов» --------------------------------------------------------

def _norm(text: str) -> str:
    text = text.lower().replace("ё", "е")
    text = re.sub(r"[«»\"'“”„`]", "", text)
    return re.sub(r"\s+", " ", text).strip(" .,;:!?-—()")


# числа, email, ссылки, @ники — самые частые выдуманные факты: каждый должен быть в тексте пользователя
_FACTS = re.compile(r"https?://\S+|[\w.+-]+@[\w-]+\.[\w.-]+|@\w{3,}|\d+(?:[.,]\d+)?")


def _stems(text: str) -> list[str]:
    return [w[:5] for w in re.findall(r"\w+", text) if len(w) > 2]


def _quoted(quote: str, haystack: str) -> bool:
    """Цитата есть в тексте дословно или почти: ≥80% её слов (по основам) встречаются в тексте."""
    q = _norm(quote)
    if len(q) < 3:
        return False
    if q in haystack:
        return True
    words, known = _stems(q), set(_stems(haystack))
    return len(words) >= 2 and sum(w in known for w in words) / len(words) >= 0.8


def _verify(items: list[dict], source: str) -> tuple[dict, dict, list[str]]:
    """Ответ модели → (card, sources, warnings): остаются только значения с цитатой из текста."""
    haystack = _norm(source)
    card, sources, warnings = {}, {}, []
    for item in items:
        field, value, quote = item.get("field"), item.get("value", "").strip(), item.get("quote", "")
        if field not in FIELDS or not value or field in card:  # одно значение на поле — без дублей
            continue
        label = LABELS[field]
        if not _quoted(quote, haystack):
            warnings.append(f"{label}: цитата не найдена в тексте — значение отброшено")
            continue
        invented = [t for t in _FACTS.findall(value) if _norm(t) not in haystack]
        if invented:
            warnings.append(f"{label}: «{', '.join(invented)}» нет в тексте — значение отброшено")
            continue
        card[field] = value
        sources[field] = quote.strip()
    return card, sources, warnings


def _questions(raw: list[dict], filled: set[str]) -> tuple[list[dict], list[str]]:
    """Вопросы модели без дублей по полям + добор из банка до MIN_QUESTIONS."""
    questions, seen, warnings = [], set(), []
    for q in raw:
        field, text = q.get("field"), q.get("question", "").strip()
        if field in FIELDS and text and field not in seen:
            questions.append({"field": field, "text": text})
            seen.add(field)
    if len(questions) < MIN_QUESTIONS:
        warnings.append(f"модель задала {len(questions)} вопроса — добрали из базы вопросов")
        for field in _FIELD_ORDER:
            if len(questions) >= MIN_QUESTIONS:
                break
            if field not in seen and field not in filled:
                questions.append({"field": field, "text": QUESTION_BANK[field]})
                seen.add(field)
    return questions[:5], warnings


# --- заглушка: детерминированно и без выдумок ------------------------------------------------

_CONTACT = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+|\+?\d[\d\s()-]{8,}\d|@\w{3,}|https?://\S+")


def _stub_analyze(draft_text: str) -> dict:
    text = draft_text.strip()
    first = re.split(r"(?<=[.!?])\s+|\n", text, maxsplit=1)[0].strip()
    card = {"context": text, "title": first[:80]}
    sources = {"context": text, "title": first[:80]}
    contact = _CONTACT.search(text)
    if contact:
        card["contact"] = sources["contact"] = contact.group(0).strip()
    questions = [
        {"field": f, "text": QUESTION_BANK[f]} for f in _FIELD_ORDER if f not in card
    ][:MIN_QUESTIONS + 1]
    return {"card": card, "sources": sources, "questions": questions}


def _stub_card(qa: list[dict]) -> tuple[dict, dict]:
    """Каждый ответ — в поле, к которому относился вопрос, дословно."""
    card, sources = {}, {}
    for item in qa:
        answer = (item.get("answer") or "").strip()
        if answer:
            field = item["field"]
            card[field] = f"{card[field]}\n{answer}" if field in card else answer
            sources.setdefault(field, answer)
    return card, sources


# --- публичные функции --------------------------------------------------------------------

def analyze_draft(draft_text: str, industry: str) -> dict:
    """Черновик → {"card", "sources", "questions": [{field, text}], "ai": {mode, attempts, warnings}}."""
    user = json.dumps({"industry": industry, "draft": draft_text, "fields": LABELS}, ensure_ascii=False)

    def validate(data: dict) -> None:
        if not data.get("questions"):
            raise ValueError("нет уточняющих вопросов — нужно от 3 до 5")

    try:
        data, attempts = llm.call_json("analyze_draft", ANALYZE_SYSTEM, user, ANALYZE_SCHEMA, validate)
    except llm.LLMUnavailable as exc:
        stub = _stub_analyze(draft_text)
        return {**stub, "ai": {"mode": "stub", "attempts": exc.attempts, "warnings": [f"ИИ недоступен: {exc}"]}}

    card, sources, warnings = _verify(data["fields"], draft_text)
    questions, q_warnings = _questions(data["questions"], set(card))
    return {
        "card": card, "sources": sources, "questions": questions,
        "ai": {"mode": "llm", "attempts": attempts, "warnings": warnings + q_warnings},
    }


def build_card(draft_text: str, qa: list[dict], card: dict, sources: dict) -> dict:
    """Черновик + ответы → {"card", "sources", "ai"}. Поля, которые правил человек, ИИ не трогает."""
    answered = [q for q in qa if (q.get("answer") or "").strip()]
    source_text = "\n".join([draft_text] + [q["answer"] for q in answered])
    manual = {f for f, s in sources.items() if s == "manual"}
    user = json.dumps({
        "draft": draft_text,
        "answers": [{"field": q["field"], "question": q["text"], "answer": q["answer"]} for q in answered],
        "current_card": {f: v for f, v in card.items() if v},
        "fields": LABELS,
    }, ensure_ascii=False)

    try:
        data, attempts = llm.call_json("build_card", CARD_SYSTEM, user, CARD_SCHEMA)
        new_card, new_sources, warnings = _verify(data["fields"], source_text)
        meta = {"mode": "llm", "attempts": attempts, "warnings": warnings}
        # ответ, который модель никуда не разложила, не теряем: дословно в его поле
        for q in answered:
            if q["field"] not in new_card:
                new_card[q["field"]] = q["answer"].strip()
                new_sources[q["field"]] = q["answer"].strip()
    except llm.LLMUnavailable as exc:
        new_card, new_sources = _stub_card(answered)
        meta = {"mode": "stub", "attempts": exc.attempts, "warnings": [f"ИИ недоступен: {exc}"]}

    merged, merged_sources = dict(card), dict(sources)
    for field, value in new_card.items():
        if field in manual:
            continue
        merged[field] = value
        merged_sources[field] = new_sources[field]
    return {"card": merged, "sources": merged_sources, "ai": meta}


# --- ИИ-студент: проверка карточки глазами команды -------------------------------------------

STUDENT_SCHEMA = {
    "type": "object",
    "properties": {
        "can_start": {"type": "boolean"},
        "first_week": {"type": "array", "items": {"type": "string"}},
        "assumptions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string", "enum": FIELDS},
                    "assumption": {"type": "string"},
                    "question": {"type": "string"},
                },
                "required": ["field", "assumption", "question"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["can_start", "first_week", "assumptions"],
    "additionalProperties": False,
}

STUDENT_SYSTEM = (
    "Ты — студенческая команда из 3 человек. Тебе дали карточку задачи от бизнеса. Попробуй "
    "составить план первой недели работы — 3–4 шага, каждый до 10 слов, — опираясь только на карточку. "
    "Каждый раз, когда для плана тебе пришлось что-то додумать, потому что в карточке этого нет "
    "или сказано размыто, — запиши допущение: к какому полю оно относится, что ты предположил "
    "и какой короткий вопрос (до 15 слов) задал бы бизнесу; не больше 4 самых важных допущений. Не придумывай фактов о бизнесе. can_start = true, "
    "только если можно начать работу без важных допущений. Пиши по-русски, коротко."
)


def student_check(card: dict) -> dict:
    """Карточка → {"can_start", "first_week", "assumptions", "ai"}: мутные места, а не только пустые."""
    filled = {f: v for f, v in card.items() if v}
    try:
        data, attempts = llm.call_json(
            "student_check", STUDENT_SYSTEM,
            json.dumps({"card": filled, "fields": LABELS}, ensure_ascii=False), STUDENT_SCHEMA,
        )
        assumptions = [a for a in data["assumptions"] if a.get("field") in FIELDS and a.get("question", "").strip()][:6]
        return {"can_start": bool(data["can_start"]) and not assumptions,
                "first_week": [s for s in data["first_week"] if s.strip()][:5],
                "assumptions": assumptions, "ai": {"mode": "llm", "attempts": attempts, "warnings": []}}
    except llm.LLMUnavailable as exc:
        # заглушка: пустые поля — те места, где команде точно придётся гадать
        assumptions = [
            {"field": f, "assumption": f"«{LABELS[f]}» не указано — придётся предполагать самим",
             "question": QUESTION_BANK[f]}
            for f in _FIELD_ORDER if not card.get(f)
        ][:6]
        return {"can_start": not assumptions, "first_week": [], "assumptions": assumptions,
                "ai": {"mode": "stub", "attempts": exc.attempts, "warnings": [f"ИИ недоступен: {exc}"]}}


def spec() -> dict:
    """Промпты, формат входа и выхода, обработка некорректного ответа — то, что ТЗ §5 требует показать."""
    return {
        "mode": llm.mode(),
        "model": llm.MODEL,
        "calls": [
            {
                "name": "analyze_draft",
                "purpose": "разобрать черновик по полям карточки и задать 3–5 уточняющих вопросов",
                "system": ANALYZE_SYSTEM,
                "input_example": {"industry": "Агро", "draft": "Хотим понимать, какие поля скоро потребуют полива", "fields": LABELS},
                "output_schema": ANALYZE_SCHEMA,
            },
            {
                "name": "build_card",
                "purpose": "собрать карточку из черновика и ответов бизнеса",
                "system": CARD_SYSTEM,
                "input_example": {
                    "draft": "Хотим понимать, какие поля скоро потребуют полива",
                    "answers": [{"field": "data", "question": QUESTION_BANK["data"], "answer": "выгрузка с датчиков влажности за 2 года, CSV"}],
                    "current_card": {"context": "Хотим понимать, какие поля скоро потребуют полива"},
                    "fields": LABELS,
                },
                "output_schema": CARD_SCHEMA,
            },
            {
                "name": "student_check",
                "purpose": "ИИ-студент пробует спланировать первую неделю по карточке и отмечает допущения",
                "system": STUDENT_SYSTEM,
                "input_example": {"card": {"need": "Понять, какие поля скоро потребуют полива",
                                           "data": "выгрузка с датчиков"}, "fields": LABELS},
                "output_schema": STUDENT_SCHEMA,
            },
        ],
        "validation": [
            "ответ модели — JSON по строгой схеме (Structured Outputs, strict: true)",
            "у каждого значения есть дословная цитата из текста пользователя — иначе значение отброшено",
            "числа, email, ссылки и @ники в значении должны встречаться в тексте пользователя",
            "вопросов не меньше 3 — недостающие добираются из базы вопросов по самым весомым показателям",
            "поля, которые правил человек, ИИ не перезаписывает",
        ],
        "invalid_response": (
            "не JSON или не прошла проверка — повтор с причиной отказа, всего до 3 попыток; "
            "нет ключа, сеть или попытки кончились — локальная заглушка: черновик целиком в контекст, "
            "вопросы из базы, ответы дословно в свои поля (ai.mode = stub)"
        ),
    }
