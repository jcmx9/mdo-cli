import datetime
from pathlib import Path

import yaml
from typer.testing import CliRunner

from mdo.cli import app

runner = CliRunner()


def test_new_with_explicit_filename(profile_yaml: Path, work_dir: Path) -> None:
    result = runner.invoke(app, ["new", "--silent", "test_letter.md"])
    assert result.exit_code == 0
    p = work_dir / "test_letter.md"
    assert p.exists()
    content = p.read_text()
    assert "---" in content
    assert "date: null" in content
    assert "JJJJ-MM-TT" in content
    assert "subject: null" in content
    assert "recipient:" in content
    assert "attachments:" in content
    assert "Sehr geehrte Damen und Herren," in content


def test_new_auto_filename(profile_yaml: Path, work_dir: Path) -> None:
    result = runner.invoke(app, ["new", "--silent"])
    assert result.exit_code == 0
    today = datetime.date.today().isoformat()
    expected = work_dir / f"{today}_Brief01.md"
    assert expected.exists()


def test_new_auto_counter_increments(profile_yaml: Path, work_dir: Path) -> None:
    today = datetime.date.today().isoformat()
    (work_dir / f"{today}_Brief01.md").write_text("existing")
    result = runner.invoke(app, ["new", "--silent"])
    assert result.exit_code == 0
    expected = work_dir / f"{today}_Brief02.md"
    assert expected.exists()


def test_new_includes_profile_fields(profile_yaml: Path, work_dir: Path) -> None:
    result = runner.invoke(app, ["new", "--silent", "letter.md"])
    assert result.exit_code == 0
    content = (work_dir / "letter.md").read_text()
    parts = content.split("---")
    fm = yaml.safe_load(parts[1])
    assert fm["name"] == "Test User"
    assert fm["street"] == "Teststrasse 1"
    assert fm["closing"] == "Mit freundlichem Gruß"
    assert fm["date"] is None
    assert fm["subject"] is None
    assert isinstance(fm["recipient"], list)


def test_new_fails_without_profile(work_dir: Path) -> None:
    result = runner.invoke(app, ["new", "--silent"])
    assert result.exit_code != 0
    assert "profile.yaml" in result.output
