import json

from mdo.core.models import LetterData
from mdo.core.typst_builder import build_typst_files


def _make_data(**overrides: object) -> LetterData:
    defaults: dict[str, object] = {
        "name": "Max Mustermann",
        "street": "Musterstrasse 1",
        "zip": "12345",
        "city": "Musterstadt",
        "phone": "0123 456789",
        "email": "max@example.de",
        "iban": "DE89 3704 0044 0532 0130 00",
        "bic": "COBADEFFXXX",
        "bank": "Testbank",
        "qr_code": True,
        "recipient": ["Firma GmbH", "Strasse 1", "12345 Stadt"],
        "date": "05. April 2026",
        "subject": "Testbetreff",
        "closing": "Mit freundlichem Gruß",
    }
    defaults.update(overrides)
    return LetterData(**defaults)  # type: ignore[arg-type]


def test_basic_output() -> None:
    data = _make_data()
    typ, json_str = build_typst_files(data=data, body="Sehr geehrte Damen und Herren,")
    assert '#import "@local/din5008a:' in typ
    assert "din5008a, bullet" in typ
    assert 'json("brief.json")' in typ
    assert "Sehr geehrte Damen und Herren," in typ

    parsed = json.loads(json_str)
    assert parsed["sender"]["name"] == "Max Mustermann"
    assert parsed["sender"]["city"] == "12345 Musterstadt"
    assert parsed["sender"]["qr"] is True
    assert parsed["date"] == "05. April 2026"
    assert parsed["subject"] == "Testbetreff"
    assert parsed["recipient"] == ["Firma GmbH", "Strasse 1", "12345 Stadt"]
    assert parsed["closing"] == "Mit freundlichem Gruß"


def test_with_signature() -> None:
    data = _make_data(signature="unterschrift.svg")
    typ, json_str = build_typst_files(data=data, body="Text.")
    parsed = json.loads(json_str)
    assert parsed["signature"] == "unterschrift.svg"
    assert "image(data.signature" in typ


def test_no_signature() -> None:
    data = _make_data(signature=None)
    _, json_str = build_typst_files(data=data, body="Text.")
    parsed = json.loads(json_str)
    assert parsed["signature"] is None


def test_qr_false() -> None:
    data = _make_data(qr_code=False)
    _, json_str = build_typst_files(data=data, body="Text.")
    parsed = json.loads(json_str)
    assert parsed["sender"]["qr"] is False


def test_accent_in_json() -> None:
    data = _make_data(accent="#265282")
    _, json_str = build_typst_files(data=data, body="Text.")
    parsed = json.loads(json_str)
    assert parsed["accent"] == "#265282"


def test_attachments_in_json() -> None:
    data = _make_data(attachments=["Lebenslauf", "Zeugnis"])
    _, json_str = build_typst_files(data=data, body="Text.")
    parsed = json.loads(json_str)
    assert parsed["attachments"] == ["Lebenslauf", "Zeugnis"]


def test_special_chars_in_json() -> None:
    data = _make_data(name='Max "der" Muster', subject='Test "Betreff"')
    _, json_str = build_typst_files(data=data, body="Text.")
    parsed = json.loads(json_str)
    assert parsed["sender"]["name"] == 'Max "der" Muster'
    assert parsed["subject"] == 'Test "Betreff"'
