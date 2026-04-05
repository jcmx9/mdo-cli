from unittest.mock import patch

from mdo.core.fonts import REQUIRED_FONTS, check_fonts


def test_all_fonts_found() -> None:
    fc_output = "Source Serif 4\nSource Sans 3\nSource Code Pro\n"
    with patch("mdo.core.fonts.subprocess.run") as mock_run:
        mock_run.return_value.stdout = fc_output
        mock_run.return_value.returncode = 0
        missing = check_fonts()
    assert missing == []


def test_comma_separated_families() -> None:
    fc_output = "Source Serif 4,Source Serif 4 SmText\nSource Sans 3\nSource Code Pro\n"
    with patch("mdo.core.fonts.subprocess.run") as mock_run:
        mock_run.return_value.stdout = fc_output
        mock_run.return_value.returncode = 0
        missing = check_fonts()
    assert missing == []


def test_missing_font_detected() -> None:
    fc_output = "Source Serif 4\n"
    with patch("mdo.core.fonts.subprocess.run") as mock_run:
        mock_run.return_value.stdout = fc_output
        mock_run.return_value.returncode = 0
        missing = check_fonts()
    assert "Source Sans 3" in missing
    assert "Source Code Pro" in missing
    assert "Source Serif 4" not in missing


def test_all_fonts_missing() -> None:
    with patch("mdo.core.fonts.subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        missing = check_fonts()
    assert set(missing) == set(REQUIRED_FONTS)


def test_fc_list_not_found() -> None:
    with patch("mdo.core.fonts.subprocess.run", side_effect=FileNotFoundError):
        missing = check_fonts()
    assert set(missing) == set(REQUIRED_FONTS)
