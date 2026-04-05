from mdo.core.typst_builder import build_typst


def test_basic_output() -> None:
    result = build_typst(
        sender={
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
        },
        recipient=["Firma GmbH", "Strasse 1", "12345 Stadt"],
        date="05. April 2026",
        subject="Testbetreff",
        body="Sehr geehrte Damen und Herren,\n\nein Absatz.",
        closing="Mit freundlichem Gruß",
        signature=None,
    )
    assert '#import "@local/din5008a:0.1.1": din5008a, bullet' in result
    assert 'name: "Max Mustermann"' in result
    assert 'street: "Musterstrasse 1"' in result
    assert 'city: "12345 Musterstadt"' in result
    assert 'qr: true' in result
    assert 'date: "05. April 2026"' in result
    assert 'subject: "Testbetreff"' in result
    assert '"Firma GmbH"' in result
    assert "Sehr geehrte Damen und Herren," in result
    assert "Mit freundlichem Gruß" in result


def test_with_signature() -> None:
    result = build_typst(
        sender={"name": "Test", "street": "", "zip": "", "city": "",
                "phone": "", "email": "", "iban": "", "bic": "", "bank": "",
                "qr_code": False},
        recipient=["Empfaenger"],
        date="01. Januar 2026",
        subject="Test",
        body="Text.",
        closing="Gruß",
        signature="unterschrift.svg",
    )
    assert '#image("unterschrift.svg", width: 40mm)' in result


def test_no_signature() -> None:
    result = build_typst(
        sender={"name": "Test", "street": "", "zip": "", "city": "",
                "phone": "", "email": "", "iban": "", "bic": "", "bank": "",
                "qr_code": False},
        recipient=["Empfaenger"],
        date="01. Januar 2026",
        subject="Test",
        body="Text.",
        closing="Gruß",
        signature=None,
    )
    assert "#image" not in result
    assert "Gruß" in result


def test_qr_false() -> None:
    result = build_typst(
        sender={"name": "Test", "street": "", "zip": "", "city": "",
                "phone": "", "email": "", "iban": "", "bic": "", "bank": "",
                "qr_code": False},
        recipient=["Empfaenger"],
        date="01. Januar 2026",
        subject="Test",
        body="Text.",
        closing="Gruß",
        signature=None,
    )
    assert "qr: false" in result
