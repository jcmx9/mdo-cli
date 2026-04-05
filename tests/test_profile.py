from pathlib import Path

import yaml
from typer.testing import CliRunner

from mdo.cli import app

runner = CliRunner()


def test_profile_creates_yaml(work_dir: Path) -> None:
    result = runner.invoke(app, ["profile", "Max Mustermann"])
    assert result.exit_code == 0
    p = work_dir / "profile.yaml"
    assert p.exists()
    data = yaml.safe_load(p.read_text())
    assert data["name"] == "Max Mustermann"
    assert data["qr_code"] is True
    assert data["signature"] is None
    assert data["closing"] == "Mit freundlichem Gruß"
    assert "street" in data
    assert "zip" in data
    assert "city" in data
    assert "phone" in data
    assert "email" in data
    assert "iban" in data
    assert "bic" in data
    assert "bank" in data


def test_profile_aborts_if_exists(work_dir: Path) -> None:
    (work_dir / "profile.yaml").write_text("name: Old")
    result = runner.invoke(app, ["profile", "New Name"])
    assert result.exit_code != 0
    assert "already exists" in result.output
