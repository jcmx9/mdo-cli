from pathlib import Path

import yaml
from typer.testing import CliRunner

from mdo.cli import app

runner = CliRunner()


def test_profile_creates_yaml_with_defaults(work_dir: Path) -> None:
    # Press Enter for all prompts — 14 prompts (name..signature_width + qr/sig/closing)
    result = runner.invoke(app, ["profile"], input="\n" * 14)
    assert result.exit_code == 0
    p = work_dir / "profile.yaml"
    assert p.exists()
    data = yaml.safe_load(p.read_text())
    assert data["name"] == "Max Mustermann"
    assert data["qr_code"] is True
    assert data["signature"] is True
    assert data["closing"] == "Mit freundlichem Gruß"
    assert data["accent"] is None
    assert "street" in data
    assert "zip" in data
    assert "city" in data
    assert "phone" in data
    assert "email" in data
    assert "iban" in data
    assert "bic" in data
    assert "bank" in data


def test_profile_creates_yaml_with_custom_values(work_dir: Path) -> None:
    inputs = (
        "Anna Weber\nLindenallee 12\n80331\nMuenchen\n089 123\n"
        "anna@example.de\nDE91 1234\nBFSWDE33\nTestbank\n#265282\n"
        "null\nja\nunterschrift.svg\nMit herzlichen Gruessen\n"
    )
    result = runner.invoke(app, ["profile"], input=inputs)
    assert result.exit_code == 0
    data = yaml.safe_load((work_dir / "profile.yaml").read_text())
    assert data["name"] == "Anna Weber"
    assert data["city"] == "Muenchen"
    assert data["zip"] == 80331  # yaml parses unquoted number


def test_profile_no_quotes_on_zip(work_dir: Path) -> None:
    result = runner.invoke(app, ["profile"], input="\n" * 14)
    assert result.exit_code == 0
    raw = (work_dir / "profile.yaml").read_text()
    assert "zip: 12345" in raw
    assert "'12345'" not in raw
    assert '"12345"' not in raw


def test_profile_aborts_if_exists(work_dir: Path) -> None:
    (work_dir / "profile.yaml").write_text("name: Old")
    result = runner.invoke(app, ["profile"], input="\n")
    assert result.exit_code != 0
    assert "already exists" in result.output
