import logging
import platform
from pathlib import Path

logger = logging.getLogger(__name__)

PACKAGE_NAME = "din5008a"
FALLBACK_VERSION = "0.1.1"


def mdo_config_dir() -> Path:
    """Return the mdo config directory (~/.mdo)."""
    return Path.home() / ".mdo"


def profiles_dir() -> Path:
    """Return the mdo profiles directory (~/.mdo/profiles)."""
    return mdo_config_dir() / "profiles"


def fonts_dir() -> Path:
    """Return the mdo fonts directory.

    Checks ~/.mdo/fonts/ first, falls back to legacy ~/.local/share/mdo/fonts/.
    """
    new_path = mdo_config_dir() / "fonts"
    if new_path.exists():
        return new_path
    legacy_path = Path.home() / ".local" / "share" / "mdo" / "fonts"
    if legacy_path.exists():
        return legacy_path
    return new_path


def letters_dir() -> Path:
    """Return the letters directory (~/MarkdownOffice)."""
    return Path.home() / "MarkdownOffice"


def typst_packages_dir() -> Path:
    """Return the local Typst packages directory for the current OS."""
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "typst" / "packages" / "local"
    if system == "Linux":
        return Path.home() / ".local" / "share" / "typst" / "packages" / "local"
    return Path.home() / "AppData" / "Roaming" / "typst" / "packages" / "local"


def find_installed_version() -> str:
    """Find the latest installed version of din5008a."""
    pkg_dir = typst_packages_dir() / PACKAGE_NAME
    if not pkg_dir.exists():
        return FALLBACK_VERSION

    versions = sorted(
        (d.name for d in pkg_dir.iterdir() if d.is_dir()),
        key=lambda v: tuple(int(x) for x in v.split(".")),
        reverse=True,
    )
    return versions[0] if versions else FALLBACK_VERSION
