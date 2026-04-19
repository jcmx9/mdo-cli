from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mdo.core.compiler import compile_letter, parse_letter
from mdo.exceptions import FontError, FrontmatterError, ToolNotFoundError

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
---

Sehr geehrte Damen und Herren,

dies ist ein **Test**.
"""


class TestParseLetter:
    def test_valid_letter(self, tmp_path: Path) -> None:
        p = tmp_path / "brief.md"
        p.write_text(LETTER_CONTENT)
        fm, body = parse_letter(p)
        assert fm["name"] == "Test User"
        assert "Test" in body

    def test_invalid_frontmatter(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.md"
        p.write_text("No frontmatter here")
        with pytest.raises(FrontmatterError):
            parse_letter(p)

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            parse_letter(tmp_path / "nonexistent.md")


def _mock_subprocess_run(cmd: list[str], **kwargs: object) -> MagicMock:
    result = MagicMock()
    result.returncode = 0
    result.stderr = ""
    result.stdout = ""
    if cmd[0] == "pandoc" and "-f" in cmd:
        result.stdout = "Converted text."
    elif cmd[0] == "typst" and "compile" in cmd:
        pdf_path = Path(cmd[-1])
        pdf_path.write_bytes(b"%PDF-1.4 fake")
    elif "--version" in cmd:
        result.stdout = f"{cmd[0]} 0.1.0"
    return result


class TestCompileLetter:
    @patch("mdo.core.compiler.check_fonts", return_value=[])
    @patch("mdo.core.compiler.subprocess.run", side_effect=_mock_subprocess_run)
    @patch("mdo.core.markdown.subprocess.run", side_effect=_mock_subprocess_run)
    def test_returns_pdf_path_and_data(
        self,
        mock_md: MagicMock,
        mock_run: MagicMock,
        mock_fonts: MagicMock,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "brief.md"
        p.write_text(LETTER_CONTENT)
        pdf_path, data = compile_letter(p)
        assert isinstance(pdf_path, Path)
        assert pdf_path.suffix == ".pdf"
        assert data.name == "Test User"

    @patch("mdo.core.compiler.check_fonts", return_value=["Source Serif 4"])
    def test_raises_on_missing_fonts(self, mock_fonts: MagicMock, tmp_path: Path) -> None:
        p = tmp_path / "brief.md"
        p.write_text(LETTER_CONTENT)
        with pytest.raises(FontError):
            compile_letter(p)

    @patch("mdo.core.compiler.check_fonts", return_value=[])
    @patch("mdo.core.compiler.subprocess.run", side_effect=FileNotFoundError)
    def test_raises_on_missing_tool(
        self, mock_run: MagicMock, mock_fonts: MagicMock, tmp_path: Path
    ) -> None:
        p = tmp_path / "brief.md"
        p.write_text(LETTER_CONTENT)
        with pytest.raises(ToolNotFoundError):
            compile_letter(p)

    def test_raises_on_wrong_extension(self, tmp_path: Path) -> None:
        p = tmp_path / "brief.txt"
        p.write_text("content")
        with pytest.raises(ValueError, match=r"\.txt"):
            compile_letter(p)

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            compile_letter(tmp_path / "nonexistent.md")
