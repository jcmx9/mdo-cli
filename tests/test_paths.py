from pathlib import Path
from unittest.mock import patch

from mdo.core.paths import fonts_dir, mdo_base_dir, profiles_dir


def test_mdo_base_dir_returns_path() -> None:
    result = mdo_base_dir()
    assert isinstance(result, Path)
    assert result.name == ".mdo"


@patch("mdo.core.paths.platform.system", return_value="Darwin")
def test_mdo_base_dir_macos(mock_sys: object) -> None:
    result = mdo_base_dir()
    assert result == Path.home() / ".mdo"


@patch("mdo.core.paths.platform.system", return_value="Linux")
def test_mdo_base_dir_linux(mock_sys: object) -> None:
    result = mdo_base_dir()
    assert result == Path.home() / ".mdo"


@patch("mdo.core.paths.platform.system", return_value="Windows")
def test_mdo_base_dir_windows(mock_sys: object) -> None:
    result = mdo_base_dir()
    assert result == Path.home() / ".mdo"


def test_profiles_dir() -> None:
    result = profiles_dir()
    assert result == mdo_base_dir() / "profiles"


def test_fonts_dir_default() -> None:
    result = fonts_dir()
    # Gibt ~/.mdo/fonts/ zurück (oder den Legacy-Pfad falls der existiert)
    assert result.name == "fonts"


@patch("mdo.core.paths.Path.exists", return_value=False)
def test_fonts_dir_no_existing(mock_exists: object) -> None:
    result = fonts_dir()
    assert result == mdo_base_dir() / "fonts"
