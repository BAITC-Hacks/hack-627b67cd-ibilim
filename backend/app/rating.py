"""Рейтинг готовности бизнес-задачи 0–100 — главная геймификация (ТЗ §4, 25 баллов оценки).

Владелец — Codex. Считает **код, а не модель**: одинаковая карточка → одинаковый рейтинг,
у каждого балла есть объяснение. Правила — docs/03-rating.md (пишет Codex вместе с кодом:
README цитирует формулу оттуда). Формат ответа — объект Rating в docs/02-api.md.
"""

import re

FIELDS = [
    "title", "context", "need", "users", "data", "constraints",
    "expected_result", "success_criteria", "contact", "interaction_format",
]

# ключ, подпись, вес из ТЗ §4, поля карточки
INDICATORS = [
    ("context_need", "Контекст и потребность", 20, ("context", "need")),
    ("data", "Данные и материалы", 20, ("data",)),
    ("expected_result", "Ожидаемый результат", 15, ("expected_result",)),
    ("success_criteria", "Критерии успеха", 15, ("success_criteria",)),
    ("constraints", "Ограничения", 10, ("constraints",)),
    ("users", "Пользователи", 10, ("users",)),
    ("business_link", "Связь с бизнесом", 10, ("contact", "interaction_format")),
]

# нижняя граница, ключ, подпись (ТЗ §4)
LEVELS = [(90, "priority", "приоритетная"), (70, "ready", "готовая"), (40, "working", "рабочая"), (0, "draft", "черновик")]


def level(score: int) -> tuple[str, str]:
    """48 → ("working", "рабочая")."""
    for minimum, key, label in LEVELS:
        if score >= minimum:
            return key, label
    return "draft", "черновик"


_EMPTY = {"-", "—", "?", "нет", "не знаю", "н/д", "неизвестно", "пока нет", "нет данных"}
_NUMBER = re.compile(r"\d")
_CONTACT = re.compile(r"(?:[\w.+-]+@[\w.-]+\.[A-Za-zА-Яа-я]{2,}|\+?\d[\d\s()\-]{7,}\d|@[\w.]{3,}|https?://\S+)", re.I)
_SOURCE = re.compile(r"датчик|таблиц|выгруз|баз[аы]|crm|erp|журнал|api|csv|excel|xlsx|json|sql|документ|отч[её]т|опрос", re.I)
_FORMAT = re.compile(r"\b(?:csv|xlsx?|json|sql|api|pdf)\b|excel", re.I)
_METRIC = re.compile(r"точност|времен|скорост|ошиб|дол[яюи]|процент|выручк|охват|эконом|конверси|качеств|дн[яей]|час[аов]|минут", re.I)
_CONSTRAINT = re.compile(r"срок|бюджет|стоимост|тенге|доступ|персональн|безопасност|зако|нельзя|только|конфиденциаль|обезлич", re.I)
_FILLER = re.compile(
    r"(?:см\.?\s*(?:выше|ниже)|смотри\s+выше|уточним\s+позже|уточняется|"
    r"аналогично|tbd|todo|позже|дополним\s+позже|будет\s+позже)", re.I,
)
_KEYWORDS = {
    "api", "crm", "csv", "erp", "excel", "json", "pdf", "sql", "xls", "xlsx",
    "бюджет", "время", "выгрузка", "датчик", "датчики", "конверсия", "метрика",
    "ошибки", "скорость", "срок", "таблица", "таблицы", "точность",
}
_VOWELS = set("aeiouyаеёиоуыэюяәіөүұ")
_REPEATED = re.compile(r"([a-zа-яёәіөүұ])\1{3,}", re.I)
_FIELD_LABELS = {
    "context": "Контекст", "need": "Потребность", "users": "Пользователи",
    "data": "Данные", "constraints": "Ограничения",
    "expected_result": "Ожидаемый результат", "success_criteria": "Критерии успеха",
    "contact": "Контакт", "interaction_format": "Формат взаимодействия",
}
_SCORED_FIELDS = tuple(field for field in FIELDS if field in _FIELD_LABELS)


def _value(card: dict, key: str) -> str:
    value = card.get(key, "")
    return value.strip() if isinstance(value, str) else ""


def _present(value: str) -> bool:
    normalized = re.sub(r"\s+", " ", value.strip().lower()).strip(" .!,;:")
    return normalized not in _EMPTY and len(re.findall(r"[A-Za-zА-Яа-яЁё]", normalized)) >= 3


def _words(value: str) -> int:
    return len(re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", value))


def _parts(card: dict, key: str, soup_fields: set[str] | frozenset[str] = frozenset()) -> list[tuple[int, bool, str, str]]:
    context = _value(card, "context")
    need = _value(card, "need")
    data = _value(card, "data")
    expected = _value(card, "expected_result")
    criteria = _value(card, "success_criteria")
    constraints = _value(card, "constraints")
    users = _value(card, "users")
    contact = _value(card, "contact")
    interaction = _value(card, "interaction_format")
    if key == "context_need":
        return [
            (6, _present(context), "описан текущий контекст", "опишите текущую ситуацию"),
            (6, _present(need), "сформулирована потребность", "укажите, что нужно изменить"),
            (4, _present(context) and bool(_NUMBER.search(context)), "контекст подкреплён числом", "добавьте число к текущей ситуации"),
            (4, _present(need) and bool(_NUMBER.search(need)), "потребность подкреплена числом", "укажите целевой объём или срок"),
        ]
    if key == "data":
        return [
            (8, _present(data), "данные или материалы описаны", "укажите имеющиеся данные или материалы"),
            (6, _present(data) and "data" not in soup_fields and bool(_SOURCE.search(data)), "назван источник данных", "назовите источник: выгрузка, датчики, CRM или документы"),
            (3, _present(data) and "data" not in soup_fields and bool(_FORMAT.search(data)), "указан формат данных", "укажите формат: CSV, Excel, JSON, API или PDF"),
            (3, _present(data) and bool(_NUMBER.search(data)), "указан объём или период данных", "добавьте объём или период данных числом"),
        ]
    if key == "expected_result":
        return [
            (8, _present(expected), "результат описан", "опишите ожидаемый результат"),
            (4, _present(expected) and _words(expected) >= 6, "результат изложен подробно", "уточните вид результата и способ применения"),
            (3, _present(expected) and bool(_NUMBER.search(expected)), "результат содержит число", "добавьте целевой объём или срок"),
        ]
    if key == "success_criteria":
        return [
            (5, _present(criteria), "критерий указан", "укажите критерий успеха"),
            (7, _present(criteria) and bool(_NUMBER.search(criteria)), "задано числовое значение", "добавьте измеримый целевой показатель"),
            (3, _present(criteria) and "success_criteria" not in soup_fields and bool(_METRIC.search(criteria)), "названа измеряемая метрика", "назовите метрику: точность, время, ошибки или конверсия"),
        ]
    if key == "constraints":
        return [
            (5, _present(constraints), "ограничения описаны", "укажите ограничения проекта"),
            (3, _present(constraints) and bool(_NUMBER.search(constraints)), "есть числовая граница", "добавьте бюджет, срок или иной предел числом"),
            (2, _present(constraints) and bool(_CONSTRAINT.search(constraints)), "назван вид ограничения", "уточните срок, бюджет, доступ или безопасность"),
        ]
    if key == "users":
        return [
            (6, _present(users), "пользователи названы", "назовите пользователей результата"),
            (4, _present(users) and _words(users) >= 4, "роль пользователей уточнена", "уточните роль и задачу пользователей"),
        ]
    return [
        (6, bool(_CONTACT.search(contact)), "есть проверяемый формат контакта", "укажите email, телефон, @ник или ссылку"),
        (4, _present(interaction), "указан формат взаимодействия", "укажите формат встреч или обратной связи"),
    ]


def _total(card: dict, soup_fields: set[str] | frozenset[str] = frozenset()) -> int:
    return sum(weight for key, _, _, _ in INDICATORS
               for weight, passed, _, _ in _parts(card, key, soup_fields) if passed)


def _tokens(value: str) -> list[str]:
    return re.findall(r"[a-zа-яёәіөүұ0-9]+", value.lower())


def _filler(value: str) -> bool:
    return bool(_FILLER.fullmatch(value.strip().strip(" .,!?:;…—-")))


def _gibberish(value: str) -> bool:
    letters = re.findall(r"[a-zа-яёәіөүұ]+", value.lower())
    if not letters:
        return False
    if any(_REPEATED.search(word) for word in letters):
        return True
    return any(len(word) >= 4 for word in letters) and not any(
        char in _VOWELS for word in letters for char in word
    ) and not all(word in _KEYWORDS for word in letters)


def _keyword_soup(value: str) -> bool:
    words = _tokens(value)
    return bool(words) and len(words) < 5 and sum(word in _KEYWORDS for word in words) / len(words) >= 0.8


def _duplicate(value: str, previous: str) -> bool:
    words, earlier = set(_tokens(value)), set(_tokens(previous))
    return bool(words and earlier) and len(words & earlier) / max(len(words), len(earlier)) >= 0.8


def _penalties(card: dict) -> list[dict]:
    effective = dict(card)
    penalties = []
    current = _total(effective)

    for field in _SCORED_FIELDS:
        value = _value(effective, field)
        if not value:
            continue
        key = "filler" if _filler(value) else "gibberish" if _gibberish(value) else None
        if key is None:
            continue
        effective[field] = ""
        updated = _total(effective)
        points = current - updated
        if points:
            label = "Отписка" if key == "filler" else "Бессмысленный текст"
            penalties.append({"key": key, "label": label, "points": points,
                              "explain": f"Поле «{_FIELD_LABELS[field]}» не содержит полезного описания — его баллы сняты"})
        current = updated

    seen = []
    for field in _SCORED_FIELDS:
        value = _value(effective, field)
        if not _present(value):
            continue
        repeated = next((earlier for earlier in seen if _duplicate(value, _value(effective, earlier))), None)
        if repeated is None:
            seen.append(field)
            continue
        effective[field] = ""
        updated = _total(effective)
        points = current - updated
        if points:
            penalties.append({"key": "duplicate", "label": "Повтор текста", "points": points,
                              "explain": f"Поля «{_FIELD_LABELS[repeated]}» и «{_FIELD_LABELS[field]}» почти совпадают — текст засчитан один раз"})
        current = updated

    soup_fields: set[str] = set()
    for field in ("data", "success_criteria"):
        if not _keyword_soup(_value(effective, field)):
            continue
        soup_fields.add(field)
        updated = _total(effective, soup_fields)
        points = current - updated
        if points:
            penalties.append({"key": "keyword_soup", "label": "Набор ключевых слов", "points": points,
                              "explain": f"В поле «{_FIELD_LABELS[field]}» перечислены ключевые слова без описания — бонусы сняты"})
        current = updated
    return penalties


def score(card: dict) -> dict:
    """Карточка (любое подмножество FIELDS) → объект Rating из docs/02-api.md.

    Баллы показателя — сумма простых проверок, каждая объяснима словами: поле заполнено
    содержательно (не «-», «нет», «не знаю», «?»), есть число / процент / срок, названы
    источники данных, контакт похож на email / телефон / @ник / ссылку и т.п.
    explain — за что начислено; hint — что добавить ради оставшихся баллов (пусто при максимуме).
    missing — ключи показателей с 0 баллов; next_best — показатели с gain = max − points > 0,
    по убыванию gain. Без LLM и без БД.
    """
    breakdown = []
    missing = []
    next_best = []
    total = 0
    for key, label, maximum, _ in INDICATORS:
        checks = _parts(card, key)
        points = sum(weight for weight, passed, _, _ in checks if passed)
        total += points
        earned = [f"{description} (+{weight})" for weight, passed, description, _ in checks if passed]
        hints = [hint for _, passed, _, hint in checks if not passed]
        hint = "; ".join(hints)
        breakdown.append({
            "key": key, "label": label, "points": points, "max": maximum,
            "explain": "; ".join(earned) if earned else "Содержательных сведений пока нет",
            "hint": hint,
        })
        if points == 0:
            missing.append(key)
        if points < maximum:
            next_best.append({"key": key, "label": label, "gain": maximum - points, "hint": hint})
    next_best.sort(key=lambda item: -item["gain"])
    penalties = _penalties(card)
    total = max(0, total - sum(item["points"] for item in penalties))
    key, label = level(total)
    next_level = next(
        ({"key": next_key, "label": next_label, "points_needed": minimum - total}
         for minimum, next_key, next_label in reversed(LEVELS) if minimum > total),
        None,
    )
    return {
        "score": total, "level": key, "level_label": label,
        "breakdown": breakdown, "missing": missing, "next_best": next_best,
        "next_level": next_level, "penalties": penalties,
    }
