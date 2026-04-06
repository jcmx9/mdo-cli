from pathlib import Path

import pytest


@pytest.fixture
def work_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def profile_data() -> dict[str, object]:
    return {
        "name": "Test User",
        "street": "Teststrasse 1",
        "zip": "12345",
        "city": "Teststadt",
        "phone": "0123 456789",
        "email": "test@example.de",
        "iban": "DE89 3704 0044 0532 0130 00",
        "bic": "COBADEFFXXX",
        "bank": "Testbank",
        "qr_code": True,
        "signature": True,
        "closing": "Mit freundlichem Gruß",
        "accent": None,
    }


PROFILE_YAML_CONTENT = """\
name: Test User
street: Teststrasse 1
zip: 12345
city: Teststadt
phone: 0123 456789
email: test@example.de
iban: DE89 3704 0044 0532 0130 00
bic: COBADEFFXXX
bank: Testbank
qr_code: true
signature: true
closing: Mit freundlichem Gruß
accent: null
"""


@pytest.fixture
def profile_yaml(work_dir: Path) -> Path:
    p = work_dir / "profile.yaml"
    p.write_text(PROFILE_YAML_CONTENT, encoding="utf-8")
    return p
