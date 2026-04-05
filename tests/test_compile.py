from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from mdo.cli import app

runner = CliRunner()

LETTER_CONTENT = """---
name: Test User
street: Teststrasse 1
zip: "12345"
city: Teststadt
phone: "0123 456789"
email: test@example.de
iban: DE89 3704 0044 0532 0130 00
bic: COBADEFFXXX
bank: Testbank
qr_code: true
signature: null
closing: Mit freundlichem Gruß
date: null
subject: Testbetreff
recipient:
  - Firma GmbH
  - Strasse 1
  - "12345 Stadt"
---

Sehr geehrte Damen und Herren,

dies ist ein **Test**.
"""

INVALID_MD = """---
title: Just a random markdown file
---

Some content.
"""


@patch("mdo.commands.compile.check_fonts", return_value=[])
@patch("subprocess.run")
def test_compile_generates_pdf(mock_run, mock_fonts, work_dir: Path) -> None:
    mock_run.return_value.returncode = 0
    mock_run.return_value.stderr = ""
    mock_run.return_value.stdout = ""
    (work_dir / "brief.md").write_text(LETTER_CONTENT)
    result = runner.invoke(app, ["compile", "brief.md"])
    assert result.exit_code == 0


@patch("mdo.commands.compile.check_fonts", return_value=["Source Serif 4"])
def test_compile_aborts_on_missing_fonts(mock_fonts, work_dir: Path) -> None:
    (work_dir / "brief.md").write_text(LETTER_CONTENT)
    result = runner.invoke(app, ["compile", "brief.md"])
    assert result.exit_code != 0
    assert "Source Serif 4" in result.output
    assert "requirements" in result.output


def test_compile_file_not_found(work_dir: Path) -> None:
    result = runner.invoke(app, ["compile", "nonexistent.md"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


@patch("mdo.commands.compile.check_fonts", return_value=[])
@patch("subprocess.run")
def test_compile_with_signature(mock_run, mock_fonts, work_dir: Path) -> None:
    mock_run.return_value.returncode = 0
    mock_run.return_value.stderr = ""
    mock_run.return_value.stdout = ""
    content = LETTER_CONTENT.replace("signature: null", "signature: unterschrift.svg")
    (work_dir / "brief.md").write_text(content)
    (work_dir / "unterschrift.svg").write_text("<svg></svg>")
    result = runner.invoke(app, ["compile", "brief.md"])
    assert result.exit_code == 0


@patch("mdo.commands.compile.check_fonts", return_value=[])
def test_compile_missing_signature_file(mock_fonts, work_dir: Path) -> None:
    content = LETTER_CONTENT.replace("signature: null", "signature: unterschrift.svg")
    (work_dir / "brief.md").write_text(content)
    result = runner.invoke(app, ["compile", "brief.md"])
    assert result.exit_code != 0
    assert "unterschrift" in result.output.lower()


def test_compile_rejects_invalid_md(work_dir: Path) -> None:
    (work_dir / "random.md").write_text(INVALID_MD)
    result = runner.invoke(app, ["compile", "random.md"])
    assert result.exit_code != 0
    assert "invalid" in result.output.lower() or "missing" in result.output.lower()


def test_compile_rejects_profile_yaml(work_dir: Path) -> None:
    # profile.yaml is not a letter
    (work_dir / "profile.yaml").write_text("name: Test")
    result = runner.invoke(app, ["compile", "profile.yaml"])
    assert result.exit_code != 0
