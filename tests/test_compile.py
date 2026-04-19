from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from mdo.cli import app

runner = CliRunner()

LETTER_CONTENT = """\
---
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
date: 05. April 2026
subject: Testbetreff
recipient:
  - Firma GmbH
  - Strasse 1
  - 12345 Stadt
open: false
reveal: false
---

Sehr geehrte Damen und Herren,

dies ist ein **Test**.
"""

INVALID_MD = """\
---
title: Just a random markdown file
---

Some content.
"""


def _mock_subprocess_run(cmd: list[str], **kwargs: object) -> MagicMock:
    """Mock that handles typst, pandoc, and other subprocess calls."""
    result = MagicMock()
    result.returncode = 0
    result.stderr = ""
    result.stdout = ""
    if cmd[0] == "pandoc" and "-f" in cmd:
        result.stdout = "Sehr geehrte Damen und Herren,\n\ndies ist ein #strong[Test]."
    elif cmd[0] == "typst" and "compile" in cmd:
        pdf_path = Path(cmd[-1])
        pdf_path.write_bytes(b"%PDF-1.4 fake")
    elif "--version" in cmd:
        result.stdout = f"{cmd[0]} 0.1.0"
    return result


@patch("mdo.core.compiler.check_fonts", return_value=[])
@patch("mdo.core.compiler.subprocess.run", side_effect=_mock_subprocess_run)
@patch("mdo.core.markdown.subprocess.run", side_effect=_mock_subprocess_run)
def test_compile_generates_pdf(
    mock_md: MagicMock, mock_run: MagicMock, mock_fonts: MagicMock, work_dir: Path
) -> None:
    (work_dir / "brief.md").write_text(LETTER_CONTENT)
    result = runner.invoke(app, ["compile", "brief.md"])
    assert result.exit_code == 0


@patch("mdo.core.compiler.check_fonts", return_value=["Source Serif 4"])
def test_compile_aborts_on_missing_fonts(mock_fonts: MagicMock, work_dir: Path) -> None:
    (work_dir / "brief.md").write_text(LETTER_CONTENT)
    result = runner.invoke(app, ["compile", "brief.md"])
    assert result.exit_code != 0
    assert "Source Serif 4" in result.output


def test_compile_file_not_found(work_dir: Path) -> None:
    result = runner.invoke(app, ["compile", "nonexistent.md"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


@patch("mdo.core.compiler.check_fonts", return_value=[])
@patch("mdo.core.compiler.subprocess.run", side_effect=_mock_subprocess_run)
@patch("mdo.core.markdown.subprocess.run", side_effect=_mock_subprocess_run)
def test_compile_with_signature(
    mock_md: MagicMock, mock_run: MagicMock, mock_fonts: MagicMock, work_dir: Path
) -> None:
    content = LETTER_CONTENT.replace("signature: null", "signature: unterschrift.svg")
    (work_dir / "brief.md").write_text(content)
    (work_dir / "unterschrift.svg").write_text("<svg></svg>")
    result = runner.invoke(app, ["compile", "brief.md"])
    assert result.exit_code == 0


@patch("mdo.core.compiler.check_fonts", return_value=[])
@patch("mdo.core.compiler.subprocess.run", side_effect=_mock_subprocess_run)
@patch("mdo.core.markdown.subprocess.run", side_effect=_mock_subprocess_run)
def test_compile_missing_signature_file(
    mock_md: MagicMock, mock_run: MagicMock, mock_fonts: MagicMock, work_dir: Path
) -> None:
    content = LETTER_CONTENT.replace("signature: null", "signature: unterschrift.svg")
    (work_dir / "brief.md").write_text(content)
    result = runner.invoke(app, ["compile", "brief.md"])
    assert result.exit_code != 0


def test_compile_rejects_profile_yaml(work_dir: Path) -> None:
    (work_dir / "profile.yaml").write_text("name: Test")
    result = runner.invoke(app, ["compile", "profile.yaml"])
    assert result.exit_code != 0


@patch("mdo.core.compiler.check_fonts", return_value=[])
@patch("mdo.core.compiler.subprocess.run", side_effect=_mock_subprocess_run)
@patch("mdo.core.markdown.subprocess.run", side_effect=_mock_subprocess_run)
def test_compile_warns_empty_recipient(
    mock_md: MagicMock, mock_run: MagicMock, mock_fonts: MagicMock, work_dir: Path
) -> None:
    content = LETTER_CONTENT.replace(
        "recipient:\n  - Firma GmbH\n  - Strasse 1\n  - 12345 Stadt",
        "recipient: []",
    )
    (work_dir / "brief.md").write_text(content)
    result = runner.invoke(app, ["compile", "brief.md"])
    assert result.exit_code != 0
    assert "recipient" in result.output.lower()


@patch("mdo.core.compiler.check_fonts", return_value=[])
@patch("mdo.core.compiler.subprocess.run", side_effect=_mock_subprocess_run)
@patch("mdo.core.markdown.subprocess.run", side_effect=_mock_subprocess_run)
def test_compile_rejects_invalid_frontmatter(
    mock_md: MagicMock, mock_run: MagicMock, mock_fonts: MagicMock, work_dir: Path
) -> None:
    (work_dir / "random.md").write_text(INVALID_MD)
    result = runner.invoke(app, ["compile", "random.md"])
    assert result.exit_code != 0


@patch("mdo.core.compiler.check_fonts", return_value=[])
@patch("mdo.core.compiler.subprocess.run", side_effect=_mock_subprocess_run)
@patch("mdo.core.markdown.subprocess.run", side_effect=_mock_subprocess_run)
def test_compile_cleans_up_temp_files(
    mock_md: MagicMock, mock_run: MagicMock, mock_fonts: MagicMock, work_dir: Path
) -> None:
    (work_dir / "brief.md").write_text(LETTER_CONTENT)
    runner.invoke(app, ["compile", "brief.md"])
    assert not (work_dir / "brief.typ").exists()
    assert not (work_dir / "brief.json").exists()
