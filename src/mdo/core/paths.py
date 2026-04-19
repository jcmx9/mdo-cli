import logging
import platform
from pathlib import Path

logger = logging.getLogger(__name__)

PACKAGE_NAME = "din5008a"
FALLBACK_VERSION = "0.1.1"


def mdo_base_dir() -> Path:
    """Return the mdo base directory (~/.mdo)."""
    return Path.home() / ".mdo"


def profiles_dir() -> Path:
    """Return the mdo profiles directory (~/.mdo/profiles)."""
    return mdo_base_dir() / "profiles"


def fonts_dir() -> Path:
    """Return the mdo fonts directory (~/.mdo/fonts)."""
    return mdo_base_dir() / "fonts"


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
