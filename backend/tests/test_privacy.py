from app import privacy

IIN = "900101300017"  # 01.01.1990, мужчина XX века, контрольная цифра 7


def test_valid_iin_is_masked():
    text, found = privacy.mask(f"Выгрузка клиентов, пример ИИН {IIN}", "data")
    assert IIN not in text and "[ИИН скрыт]" in text
    assert found[0]["kind"] == "iin" and found[0]["field"] == "data"


def test_wrong_check_digit_and_bin_are_not_masked():
    for number in ("900101300018", "180340000001", "123456789012"):  # чужая контрольная цифра, БИН, случайное
        text, found = privacy.mask(f"номер {number}", "data")
        assert number in text and found == []


def test_card_number_is_masked_but_phone_is_not():
    text, found = privacy.mask("карта 4111 1111 1111 1111, звонить +7 701 123 45 67", "contact")
    assert "[номер карты скрыт]" in text and "+7 701 123 45 67" in text
    assert [f["kind"] for f in found] == ["card"]


def test_personal_data_warning_disappears_when_anonymized():
    card = {"data": "Выгрузка клиентов с ФИО и телефонами клиентов за год"}
    warned = privacy.warnings(card)
    assert warned and warned[0]["kind"] == "personal_data" and "ФИО" in warned[0]["message"]
    card["constraints"] = "Данные передадим обезличенными"
    assert privacy.warnings(card) == []


def test_merge_keeps_one_finding_per_kind_and_field():
    a = [{"kind": "iin", "field": "draft"}]
    b = [{"kind": "iin", "field": "draft"}, {"kind": "iin", "field": "data"}]
    assert privacy.merge(a, b) == [{"kind": "iin", "field": "draft"}, {"kind": "iin", "field": "data"}]
