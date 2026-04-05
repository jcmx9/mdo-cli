from pathlib import Path

import pytest
import yaml


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
        "signature": None,
        "closing": "Mit freundlichem Gruß",
    }


@pytest.fixture
def profile_yaml(work_dir: Path, profile_data: dict[str, object]) -> Path:
    p = work_dir / "profile.yaml"
    p.write_text(yaml.dump(profile_data, allow_unicode=True, default_flow_style=False))
    return p
