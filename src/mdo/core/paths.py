import platform
from pathlib import Path

PACKAGE_NAME = "din5008a"
FALLBACK_VERSION = "0.1.1"


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
