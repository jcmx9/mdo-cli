from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from mdo.cli import app

runner = CliRunner()

LETTER_CONTENT = """---
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
signature: null
closing: Mit freundlichem Gruß
date: null
subject: Testbetreff
recipient:
  - Firma GmbH
  - Strasse 1
  - 12345 Stadt
---

Sehr geehrte Damen und Herren,

dies ist ein **Test**.
"""

INVALID_MD = """---
title: Just a random markdown file
---

Some content.
"""


def _mock_subprocess_run(cmd: list[str], **kwargs: object) -> MagicMock:
    """Mock that handles both typst --version and typst compile."""
    result = MagicMock()
    result.returncode = 0
    result.stderr = ""
    result.stdout = "typst 0.14.2"
    return result


@patch("mdo.commands.compile.check_fonts", return_value=[])
@patch("mdo.commands.compile.subprocess.run", side_effect=_mock_subprocess_run)
def test_compile_generates_pdf(mock_run: MagicMock, mock_fonts: MagicMock, work_dir: Path) -> None:
    (work_dir / "brief.md").write_text(LETTER_CONTENT)
    result = runner.invoke(app, ["compile", "brief.md"])
    assert result.exit_code == 0
    # Verify typst compile was called with correct args
    compile_call = [c for c in mock_run.call_args_list if "compile" in c.args[0]]
    assert len(compile_call) == 1
    assert "--pdf-standard" in compile_call[0].args[0]
    assert "a-2b" in compile_call[0].args[0]


@patch("mdo.commands.compile.check_fonts", return_value=["Source Serif 4"])
def test_compile_aborts_on_missing_fonts(mock_fonts: MagicMock, work_dir: Path) -> None:
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
@patch("mdo.commands.compile.subprocess.run", side_effect=_mock_subprocess_run)
def test_compile_with_signature(mock_run: MagicMock, mock_fonts: MagicMock, work_dir: Path) -> None:
    content = LETTER_CONTENT.replace("signature: null", "signature: unterschrift.svg")
    (work_dir / "brief.md").write_text(content)
    (work_dir / "unterschrift.svg").write_text("<svg></svg>")
    result = runner.invoke(app, ["compile", "brief.md"])
    assert result.exit_code == 0


@patch("mdo.commands.compile.check_fonts", return_value=[])
def test_compile_missing_signature_file(mock_fonts: MagicMock, work_dir: Path) -> None:
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
    (work_dir / "profile.yaml").write_text("name: Test")
    result = runner.invoke(app, ["compile", "profile.yaml"])
    assert result.exit_code != 0


def test_compile_warns_empty_recipient(work_dir: Path) -> None:
    content = LETTER_CONTENT.replace(
        "recipient:\n  - Firma GmbH\n  - Strasse 1\n  - 12345 Stadt",
        "recipient: []",
    )
    (work_dir / "brief.md").write_text(content)
    result = runner.invoke(app, ["compile", "brief.md"])
    assert result.exit_code != 0
    assert "recipient" in result.output.lower()
