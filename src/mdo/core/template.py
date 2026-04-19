"""Template installation and update for din5008a."""

import json
import logging
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from mdo.core.paths import PACKAGE_NAME, find_installed_version, typst_packages_dir
from mdo.exceptions import TemplateError, ToolNotFoundError

logger = logging.getLogger(__name__)

REPO_URL = "https://github.com/jcmx9/typst-DIN5008a.git"
REPO_API_URL = "https://api.github.com/repos/jcmx9/typst-DIN5008a/releases/latest"
EXCLUDE_DIRS = {".git", ".github", "docs", "tests", "scripts", "template"}


def _read_version(repo_dir: Path) -> str:
    """Read package version from typst.toml."""
    toml_path = repo_dir / "typst.toml"
    if not toml_path.exists():
        msg = "typst.toml not found in template repo"
        raise TemplateError(msg)
    content = toml_path.read_text()
    match = re.search(r'^version\s*=\s*"(.+?)"', content, re.MULTILINE)
    if not match:
        msg = "version not found in typst.toml"
        raise TemplateError(msg)
    return match.group(1)


def _copy_template(src: Path, target: Path) -> None:
    """Copy template files from src to target, excluding non-package dirs."""
    target.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in EXCLUDE_DIRS:
            continue
        dest = target / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)


def install_template_git() -> Path:
    """Install template via git clone. Returns install path."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / "repo"
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", REPO_URL, str(tmp_path)],
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError:
            msg = "git not found"
            raise ToolNotFoundError(msg) from None
        except subprocess.CalledProcessError as e:
            msg = f"git clone failed:\n{e.stderr}"
            raise TemplateError(msg) from None

        version = _read_version(tmp_path)
        target = typst_packages_dir() / PACKAGE_NAME / version
        _copy_template(tmp_path, target)
        logger.info("Installed %s v%s to %s", PACKAGE_NAME, version, target)
        return target


def install_template_http() -> Path:
    """Install template via HTTP download from GitHub releases."""
    try:
        result = subprocess.run(
            ["curl", "-sL", REPO_API_URL],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        msg = "curl not found"
        raise ToolNotFoundError(msg) from None

    data = json.loads(result.stdout)
    zip_url = data.get("zipball_url")
    if not zip_url:
        msg = "No zipball_url in GitHub release"
        raise TemplateError(msg)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        zip_path = tmp_path / "release.zip"

        try:
            subprocess.run(
                ["curl", "-sL", "-o", str(zip_path), zip_url],
                check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            msg = f"Download failed: {e}"
            raise TemplateError(msg) from None

        extract_dir = tmp_path / "extracted"
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)

        subdirs = list(extract_dir.iterdir())
        if len(subdirs) != 1 or not subdirs[0].is_dir():
            msg = "Unexpected zip structure"
            raise TemplateError(msg)

        repo_dir = subdirs[0]
        version = _read_version(repo_dir)
        target = typst_packages_dir() / PACKAGE_NAME / version
        _copy_template(repo_dir, target)
        logger.info("Installed %s v%s to %s", PACKAGE_NAME, version, target)
        return target


def install_template(method: str = "auto") -> Path:
    """Install template. method: 'git', 'http', 'auto'.

    'auto' tries git first, falls back to http.
    """
    if method == "git":
        return install_template_git()
    if method == "http":
        return install_template_http()
    try:
        return install_template_git()
    except ToolNotFoundError:
        logger.debug("git not available, falling back to HTTP download")
        return install_template_http()


def get_installed_version() -> str | None:
    """Return the installed template version, or None if not installed."""
    return find_installed_version()
