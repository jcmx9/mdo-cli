from unittest.mock import patch

from mdo.core.fonts import REQUIRED_FONTS, check_fonts


def test_all_fonts_found() -> None:
    fc_output = (
        "/Library/Fonts/SourceSerif4.ttf: Source Serif 4:style=Regular\n"
        "/Library/Fonts/SourceSans3.ttf: Source Sans 3:style=Regular\n"
        "/Library/Fonts/SourceCodePro.ttf: Source Code Pro:style=Regular\n"
    )
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = fc_output
        mock_run.return_value.returncode = 0
        missing = check_fonts()
    assert missing == []


def test_missing_font_detected() -> None:
    fc_output = "/Library/Fonts/SourceSerif4.ttf: Source Serif 4:style=Regular\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = fc_output
        mock_run.return_value.returncode = 0
        missing = check_fonts()
    assert "Source Sans 3" in missing
    assert "Source Code Pro" in missing
    assert "Source Serif 4" not in missing


def test_all_fonts_missing() -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        missing = check_fonts()
    assert set(missing) == set(REQUIRED_FONTS)


def test_fc_list_not_found() -> None:
    with patch("subprocess.run", side_effect=FileNotFoundError):
        missing = check_fonts()
    assert set(missing) == set(REQUIRED_FONTS)
