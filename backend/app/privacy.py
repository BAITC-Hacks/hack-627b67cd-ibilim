"""Персональные данные в тексте задачи — Закон РК «О персональных данных и их защите».

Владелец — Claude. Каталог открыт всем командам, поэтому ИИН и номера карт маскируются до
сохранения и до отправки в ИИ. Упоминания ФИО, паспортов, диагнозов и т.п. — предупреждение,
пока в тексте не сказано, что данные обезличены. Без LLM: ИИН проверяется по контрольной
цифре и дате рождения, карта — по алгоритму Луна, поэтому случайные числа и БИН не задеваются.
"""

import re
from datetime import date

HINT = "команде нужны обезличенные данные: уберите идентификаторы людей или укажите, что выгрузка будет обезличена"

_IIN = re.compile(r"(?<!\d)\d{12}(?!\d)")
_CARD = re.compile(r"(?<!\d)\d(?:[ -]?\d){12,18}(?!\d)")
_ANONYMIZED = re.compile(r"обезлич|анонимиз|без персональн|без фио|псевдонимиз", re.I)

_PERSONAL = {
    "ФИО": r"\bфио\b|фамили[яиюей]+ и имен",
    "паспортные данные": r"паспорт|удостоверени[еяй] личности",
    "адреса проживания": r"адрес[а-я]* (?:проживания|клиент|жител|покупател|пациент)",
    "даты рождения": r"дат[аыу] рождения",
    "медицинские данные": r"диагноз|медицинск[а-я]* (?:карт|данн|истори)",
    "сведения о зарплатах": r"зарплат|заработн[а-я]* плат",
    "телефоны людей": r"телефон[а-я]* (?:клиент|покупател|пациент|сотрудник|жител|студент)",
}


def iin_valid(digits: str) -> bool:
    """ИИН: ГГММДД + код века и пола 1–6 + номер + контрольная цифра."""
    d = [int(c) for c in digits]
    if not 1 <= d[6] <= 6:
        return False
    try:
        date(1800 + 100 * ((d[6] - 1) // 2) + int(digits[:2]), int(digits[2:4]), int(digits[4:6]))
    except ValueError:
        return False
    check = sum(a * w for a, w in zip(d[:11], range(1, 12))) % 11
    if check == 10:
        check = sum(a * w for a, w in zip(d[:11], (3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2))) % 11
    return check != 10 and check == d[11]


def luhn_valid(digits: str) -> bool:
    total = 0
    for i, c in enumerate(reversed(digits)):
        n = int(c) * (2 if i % 2 else 1)
        total += n - 9 if n > 9 else n
    return total % 10 == 0


def mask(text: str, field: str) -> tuple[str, list[dict]]:
    """Скрывает ИИН и номера карт → (текст, находки)."""
    findings: list[dict] = []

    def hide_iin(m: re.Match) -> str:
        if not iin_valid(m.group(0)):
            return m.group(0)
        findings.append({"kind": "iin", "field": field, "hint": HINT,
                         "message": "в тексте был ИИН — скрыт до публикации и до отправки в ИИ"})
        return "[ИИН скрыт]"

    def hide_card(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group(0))
        if not (13 <= len(digits) <= 19 and luhn_valid(digits)):
            return m.group(0)
        findings.append({"kind": "card", "field": field, "hint": HINT,
                         "message": "в тексте был номер банковской карты — скрыт до публикации и до отправки в ИИ"})
        return "[номер карты скрыт]"

    return _CARD.sub(hide_card, _IIN.sub(hide_iin, text)), findings


def warnings(texts: dict[str, str]) -> list[dict]:
    """Поле → текст. Упоминания персональных данных, если нигде не сказано об обезличивании."""
    if any(_ANONYMIZED.search(t) for t in texts.values()):
        return []
    found = []
    for field, text in texts.items():
        labels = [label for label, pattern in _PERSONAL.items() if re.search(pattern, text, re.I)]
        if labels:
            found.append({"kind": "personal_data", "field": field, "hint": HINT,
                          "message": f"упомянуты {', '.join(labels)} — в открытый каталог такие данные попасть не должны"})
    return found


def merge(old: list[dict], new: list[dict]) -> list[dict]:
    """Накопленные находки маскирования без повторов по (kind, field)."""
    seen = {(f["kind"], f["field"]) for f in old}
    return old + [f for f in new if (f["kind"], f["field"]) not in seen and not seen.add((f["kind"], f["field"]))]
