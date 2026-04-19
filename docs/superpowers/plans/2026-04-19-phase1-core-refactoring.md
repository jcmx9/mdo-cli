# Phase 1: Core-Refactoring — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Python-Kernlogik von CLI-Abhängigkeiten (Typer) entkoppeln, Multi-Profil-Support einführen und die Architektur für Flutter-Integration vorbereiten.

**Architecture:** Die Logik aus `commands/` wird in `core/` extrahiert. Core-Funktionen werfen Exceptions statt `typer.Exit()`. Commands werden zu dünnen Wrappern. Profile wandern von einzelner `profile.yaml` zu `~/.mdo/profiles/`. Template-Update bekommt HTTP als Alternative zu Git.

**Tech Stack:** Python 3.12+, Pydantic v2, PyYAML, pytest, ruff, mypy

---

## File Structure

### Modified Files

| File | Responsibility |
|------|---------------|
| `src/mdo/core/paths.py` | Erweitert: `mdo_base_dir()`, `profiles_dir()`, `fonts_dir()` |
| `src/mdo/core/models.py` | Erweitert: `ProfileConfig` hierher migriert |
| `src/mdo/commands/compile.py` | Wird dünner: delegiert an `core/compiler.py` |
| `src/mdo/commands/profile.py` | Wird dünner: delegiert an `core/profile.py` |
| `src/mdo/commands/update.py` | Wird dünner: delegiert an `core/template.py` |
| `src/mdo/commands/install_fonts.py` | `mdo_fonts_dir()` entfernt (lebt jetzt in `core/paths.py`) |
| `src/mdo/cli.py` | Neuer Command: `mdo profile list`, `mdo profile delete` |
| `src/mdo/config.py` | Wird gelöscht (nach `core/models.py` migriert) |

### New Files

| File | Responsibility |
|------|---------------|
| `src/mdo/core/compiler.py` | Compile-Pipeline ohne Typer-Abhängigkeit |
| `src/mdo/core/profile.py` | Multi-Profil: load/save/list/delete |
| `src/mdo/core/template.py` | Template install via Git oder HTTP |
| `tests/test_paths.py` | Tests für erweiterte Pfad-Funktionen |
| `tests/test_core_profile.py` | Tests für Multi-Profil-Logic |
| `tests/test_core_compiler.py` | Tests für Core-Compiler |
| `tests/test_core_template.py` | Tests für Template-Install |

---

### Task 1: Pfad-Funktionen erweitern (`core/paths.py`)

**Files:**
- Modify: `src/mdo/core/paths.py`
- Create: `tests/test_paths.py`

- [ ] **Step 1: Failing Tests schreiben**

```python
# tests/test_paths.py
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


def test_fonts_dir() -> None:
    result = fonts_dir()
    assert result == mdo_base_dir() / "fonts"
```

- [ ] **Step 2: Tests ausführen — FAIL erwartet**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest tests/test_paths.py -v`
Expected: FAIL — `ImportError: cannot import name 'mdo_base_dir'`

- [ ] **Step 3: Implementierung**

`src/mdo/core/paths.py` — drei Funktionen hinzufügen:

```python
import logging
import platform
from pathlib import Path

logger = logging.getLogger(__name__)

PACKAGE_NAME = "din5008a"
FALLBACK_VERSION = "0.1.1"


def mdo_base_dir() -> Path:
    """Return the mdo base directory (~/.mdo/)."""
    return Path.home() / ".mdo"


def profiles_dir() -> Path:
    """Return the profiles directory (~/.mdo/profiles/)."""
    return mdo_base_dir() / "profiles"


def fonts_dir() -> Path:
    """Return the mdo-specific fonts directory (~/.mdo/fonts/)."""
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
```

- [ ] **Step 4: Tests ausführen — PASS erwartet**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest tests/test_paths.py -v`
Expected: PASS

- [ ] **Step 5: `commands/install_fonts.py` — `mdo_fonts_dir()` durch `fonts_dir()` ersetzen**

In `src/mdo/commands/install_fonts.py`:
- `mdo_fonts_dir()` Funktion entfernen
- Import ändern: `from mdo.core.paths import fonts_dir`
- Alle `mdo_fonts_dir()` Aufrufe durch `fonts_dir()` ersetzen

In `src/mdo/commands/compile.py`:
- Import ändern: `from mdo.commands.install_fonts import mdo_fonts_dir` → `from mdo.core.paths import fonts_dir`
- Alle `mdo_fonts_dir()` Aufrufe durch `fonts_dir()` ersetzen

- [ ] **Step 6: Alle Tests ausführen — PASS erwartet**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest -v`
Expected: PASS — alle bestehenden Tests grün

- [ ] **Step 7: Lint + Type-Check**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/ && uv run mypy src/`
Expected: Keine Fehler

- [ ] **Step 8: Commit**

```bash
git add src/mdo/core/paths.py src/mdo/commands/install_fonts.py src/mdo/commands/compile.py tests/test_paths.py
git commit -m "refactor(core): add mdo_base_dir/profiles_dir/fonts_dir to paths module"
```

---

### Task 2: `ProfileConfig` nach `core/models.py` migrieren

**Files:**
- Modify: `src/mdo/core/models.py`
- Delete: `src/mdo/config.py`
- Modify: `src/mdo/commands/profile.py` (Import-Update)
- Modify: `src/mdo/commands/new.py` (Import-Update)

- [ ] **Step 1: Failing Test schreiben**

```python
# In tests/test_typst_builder.py oder direkt testen:
# Prüfen, dass ProfileConfig aus core.models importierbar ist
```

Einfacher: direkt den Import testen in einem bestehenden Test.

Kein separater Test nötig — die bestehenden Tests für `profile` und `new` validieren das implizit.

- [ ] **Step 2: `ProfileConfig` in `core/models.py` einfügen**

Am Ende von `src/mdo/core/models.py` hinzufügen:

```python
class ProfileConfig(BaseModel):
    """Validated sender profile from profile.yaml."""

    name: str
    street: str
    zip: str
    city: str
    phone: str = ""
    email: str = ""
    iban: str = ""
    bic: str = ""
    bank: str = ""
    accent: str | None = None
    signature_width: int | None = None
    qr_code: bool = False
    signature: bool = True
    closing: str = "Mit freundlichem Gruß"
    open: bool = True
    reveal: bool = True

    @field_validator("zip", mode="before")
    @classmethod
    def coerce_zip_profile(cls, v: object) -> str:
        """YAML parses bare numbers like 12345 as int."""
        return str(v)

    @field_validator("accent")
    @classmethod
    def valid_hex_color_profile(cls, v: str | None) -> str | None:
        """Validate accent as hex color or None."""
        if v is None:
            return None
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            msg = f"accent must be a hex color like #B03060, got '{v}'"
            raise ValueError(msg)
        return v
```

**Hinweis:** Die Validator-Methoden brauchen eigene Namen (`coerce_zip_profile`, `valid_hex_color_profile`), weil in derselben Datei `LetterData` bereits `coerce_zip` und `valid_hex_color` hat. Alternativ: einen gemeinsamen Validator als freie Funktion extrahieren und in beiden Models nutzen.

**Besserer Ansatz — gemeinsame Validatoren:**

```python
def _coerce_to_str(v: object) -> str:
    """YAML parses bare numbers like 12345 as int."""
    return str(v)


def _validate_hex_color(v: str | None) -> str | None:
    """Validate hex color or None."""
    if v is None:
        return None
    if not re.match(r"^#[0-9a-fA-F]{6}$", v):
        msg = f"accent must be a hex color like #B03060, got '{v}'"
        raise ValueError(msg)
    return v
```

Dann in beiden Models:
```python
coerce_zip = field_validator("zip", mode="before")(_coerce_to_str)
valid_hex_color = field_validator("accent")(_validate_hex_color)
```

- [ ] **Step 3: `src/mdo/config.py` löschen**

```bash
rm src/mdo/config.py
```

- [ ] **Step 4: Imports in `commands/profile.py` und `commands/new.py` aktualisieren**

Alle `from mdo.config import ProfileConfig` → `from mdo.core.models import ProfileConfig`

Prüfen mit: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run ruff check src/ && grep -r "from mdo.config" src/`

- [ ] **Step 5: Alle Tests ausführen**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest -v`
Expected: PASS

- [ ] **Step 6: Lint + Type-Check**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run ruff check src/ tests/ && uv run mypy src/`
Expected: Keine Fehler

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor(models): migrate ProfileConfig to core/models.py"
```

---

### Task 3: Multi-Profil-Modul (`core/profile.py`)

**Files:**
- Create: `src/mdo/core/profile.py`
- Create: `tests/test_core_profile.py`

- [ ] **Step 1: Failing Tests schreiben**

```python
# tests/test_core_profile.py
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from mdo.core.models import ProfileConfig
from mdo.core.profile import delete_profile, list_profiles, load_profile, save_profile


@pytest.fixture
def profiles_path(tmp_path: Path) -> Path:
    """Temporary profiles directory."""
    d = tmp_path / ".mdo" / "profiles"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def _mock_profiles_dir(profiles_path: Path):  # type: ignore[no-untyped-def]
    """Patch profiles_dir to use tmp_path."""
    with patch("mdo.core.profile.profiles_dir", return_value=profiles_path):
        yield


@pytest.fixture
def sample_profile() -> ProfileConfig:
    return ProfileConfig(
        name="Max Mustermann",
        street="Musterstrasse 1",
        zip="12345",
        city="Musterstadt",
    )


@pytest.mark.usefixtures("_mock_profiles_dir")
class TestSaveProfile:
    def test_save_default(self, profiles_path: Path, sample_profile: ProfileConfig) -> None:
        result = save_profile(sample_profile)
        assert result == profiles_path / "default.yaml"
        assert result.exists()
        data = yaml.safe_load(result.read_text())
        assert data["name"] == "Max Mustermann"

    def test_save_named(self, profiles_path: Path, sample_profile: ProfileConfig) -> None:
        result = save_profile(sample_profile, name="work")
        assert result == profiles_path / "work.yaml"
        assert result.exists()


@pytest.mark.usefixtures("_mock_profiles_dir")
class TestLoadProfile:
    def test_load_existing(self, profiles_path: Path, sample_profile: ProfileConfig) -> None:
        save_profile(sample_profile, name="test")
        loaded = load_profile("test")
        assert loaded.name == "Max Mustermann"
        assert loaded.street == "Musterstrasse 1"

    def test_load_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_profile("nonexistent")

    def test_load_default(self, profiles_path: Path, sample_profile: ProfileConfig) -> None:
        save_profile(sample_profile)
        loaded = load_profile()
        assert loaded.name == "Max Mustermann"


@pytest.mark.usefixtures("_mock_profiles_dir")
class TestListProfiles:
    def test_list_empty(self) -> None:
        assert list_profiles() == []

    def test_list_multiple(self, profiles_path: Path, sample_profile: ProfileConfig) -> None:
        save_profile(sample_profile, name="default")
        save_profile(sample_profile, name="work")
        names = list_profiles()
        assert sorted(names) == ["default", "work"]


@pytest.mark.usefixtures("_mock_profiles_dir")
class TestDeleteProfile:
    def test_delete_existing(self, profiles_path: Path, sample_profile: ProfileConfig) -> None:
        save_profile(sample_profile, name="temp")
        delete_profile("temp")
        assert not (profiles_path / "temp.yaml").exists()

    def test_delete_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            delete_profile("nonexistent")

    def test_delete_default_raises(self, profiles_path: Path, sample_profile: ProfileConfig) -> None:
        save_profile(sample_profile)
        with pytest.raises(ValueError, match="default"):
            delete_profile("default")
```

- [ ] **Step 2: Tests ausführen — FAIL erwartet**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest tests/test_core_profile.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mdo.core.profile'`

- [ ] **Step 3: Implementierung**

```python
# src/mdo/core/profile.py
"""Multi-profile management for mdo."""

import logging
from pathlib import Path

import yaml

from mdo.core.models import ProfileConfig
from mdo.core.paths import profiles_dir

logger = logging.getLogger(__name__)


def save_profile(config: ProfileConfig, name: str = "default") -> Path:
    """Save a profile to ~/.mdo/profiles/{name}.yaml."""
    target_dir = profiles_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{name}.yaml"
    data = config.model_dump()
    path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    logger.debug("Profile saved to %s", path)
    return path


def load_profile(name: str = "default") -> ProfileConfig:
    """Load a profile from ~/.mdo/profiles/{name}.yaml."""
    path = profiles_dir() / f"{name}.yaml"
    if not path.exists():
        msg = f"Profile not found: {path}"
        raise FileNotFoundError(msg)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ProfileConfig.model_validate(data)


def list_profiles() -> list[str]:
    """Return all available profile names."""
    target_dir = profiles_dir()
    if not target_dir.exists():
        return []
    return sorted(p.stem for p in target_dir.glob("*.yaml"))


def delete_profile(name: str) -> None:
    """Delete a profile. Cannot delete 'default'."""
    if name == "default":
        msg = "Cannot delete the default profile"
        raise ValueError(msg)
    path = profiles_dir() / f"{name}.yaml"
    if not path.exists():
        msg = f"Profile not found: {path}"
        raise FileNotFoundError(msg)
    path.unlink()
    logger.debug("Profile deleted: %s", path)
```

- [ ] **Step 4: Tests ausführen — PASS erwartet**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest tests/test_core_profile.py -v`
Expected: PASS

- [ ] **Step 5: Lint + Type-Check**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run ruff check src/mdo/core/profile.py tests/test_core_profile.py && uv run mypy src/`
Expected: Keine Fehler

- [ ] **Step 6: Commit**

```bash
git add src/mdo/core/profile.py tests/test_core_profile.py
git commit -m "feat(core): add multi-profile support (load/save/list/delete)"
```

---

### Task 4: Template-Modul (`core/template.py`)

**Files:**
- Create: `src/mdo/core/template.py`
- Create: `tests/test_core_template.py`
- Modify: `src/mdo/commands/update.py` (wird dünner)

- [ ] **Step 1: Failing Tests schreiben**

```python
# tests/test_core_template.py
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mdo.core.template import get_installed_version, install_template_git, install_template_http


@patch("mdo.core.template.typst_packages_dir")
@patch("mdo.core.template.subprocess.run")
def test_install_git(mock_run: MagicMock, mock_dir: MagicMock, tmp_path: Path) -> None:
    mock_dir.return_value = tmp_path / "packages"

    def fake_clone(cmd: list[str], **kwargs: object) -> MagicMock:
        repo_dir = Path(cmd[-1])
        repo_dir.mkdir(parents=True)
        src_dir = repo_dir / "src"
        src_dir.mkdir()
        (src_dir / "lib.typ").write_text("// template")
        (repo_dir / "typst.toml").write_text('[package]\nversion = "0.3.0"\n')
        (repo_dir / ".git").mkdir()
        result = MagicMock()
        result.returncode = 0
        return result

    mock_run.side_effect = fake_clone
    path = install_template_git()
    assert "0.3.0" in str(path)
    assert (path / "src" / "lib.typ").exists()
    assert not (path / ".git").exists()


@patch("mdo.core.template.typst_packages_dir")
@patch("mdo.core.template.subprocess.run")
def test_install_http(mock_run: MagicMock, mock_dir: MagicMock, tmp_path: Path) -> None:
    mock_dir.return_value = tmp_path / "packages"

    def fake_curl(cmd: list[str], **kwargs: object) -> MagicMock:
        result = MagicMock()
        result.returncode = 0
        if "api.github.com" in cmd[-1]:
            result.stdout = json.dumps({
                "tag_name": "v0.3.0",
                "zipball_url": "https://github.com/fake/archive/v0.3.0.zip",
            })
        elif "-o" in cmd:
            # Simulate zip download — create a fake zip
            import io
            import zipfile

            zip_path = Path(cmd[cmd.index("-o") + 1])
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                zf.writestr("repo-abc123/typst.toml", '[package]\nversion = "0.3.0"\n')
                zf.writestr("repo-abc123/src/lib.typ", "// template")
            zip_path.write_bytes(buf.getvalue())
        return result

    mock_run.side_effect = fake_curl
    path = install_template_http()
    assert "0.3.0" in str(path)
    assert (path / "src" / "lib.typ").exists()


@patch("mdo.core.template.find_installed_version", return_value="0.2.0")
def test_get_installed_version(mock_ver: MagicMock) -> None:
    assert get_installed_version() == "0.2.0"


@patch("mdo.core.template.find_installed_version", return_value="0.1.1")
def test_get_installed_version_fallback(mock_ver: MagicMock) -> None:
    # 0.1.1 is the fallback, meaning no real version found
    assert get_installed_version() == "0.1.1"
```

- [ ] **Step 2: Tests ausführen — FAIL erwartet**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest tests/test_core_template.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implementierung**

```python
# src/mdo/core/template.py
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

    tag = data.get("tag_name", "")
    logger.debug("Downloading release %s from %s", tag, zip_url)

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

        # GitHub zipball contains a single top-level directory
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
    # auto
    try:
        return install_template_git()
    except ToolNotFoundError:
        logger.debug("git not available, falling back to HTTP download")
        return install_template_http()


def get_installed_version() -> str | None:
    """Return the installed template version, or None if not installed."""
    version = find_installed_version()
    return version
```

- [ ] **Step 4: Tests ausführen — PASS erwartet**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest tests/test_core_template.py -v`
Expected: PASS

- [ ] **Step 5: `commands/update.py` auf Core delegieren**

```python
# src/mdo/commands/update.py
import typer

from mdo.core.template import install_template
from mdo.exceptions import TemplateError, ToolNotFoundError


def update() -> None:
    """Download/update the din5008a Typst template."""
    try:
        target = install_template(method="git")
    except ToolNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except TemplateError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    typer.echo(f"Installed template to {target}")
```

- [ ] **Step 6: Alle Tests ausführen**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest -v`
Expected: PASS — bestehende `test_update.py` Tests müssen evtl. angepasst werden (Mock-Pfade ändern sich)

- [ ] **Step 7: `test_update.py` anpassen**

Die Mocks müssen auf `mdo.core.template.subprocess.run` und `mdo.core.template.typst_packages_dir` zeigen statt auf `mdo.commands.update.*`.

```python
# tests/test_update.py
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from mdo.cli import app

runner = CliRunner()


@patch("mdo.core.template.typst_packages_dir")
@patch("mdo.core.template.subprocess.run")
def test_update_installs_template(mock_run: MagicMock, mock_dir: MagicMock, tmp_path: Path) -> None:
    mock_dir.return_value = tmp_path / "packages"

    def fake_clone(cmd: list[str], **kwargs: object) -> MagicMock:
        repo_dir = Path(cmd[-1])
        repo_dir.mkdir(parents=True)
        src_dir = repo_dir / "src"
        src_dir.mkdir()
        (src_dir / "lib.typ").write_text("// template")
        (repo_dir / "typst.toml").write_text('[package]\nversion = "0.2.0"\n')
        (repo_dir / "version.typ").write_text('#let version = "0.2.0"')
        (repo_dir / ".git").mkdir()
        result = MagicMock()
        result.returncode = 0
        return result

    mock_run.side_effect = fake_clone

    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0
    assert "0.2.0" in result.output

    installed = tmp_path / "packages" / "din5008a" / "0.2.0"
    assert (installed / "src" / "lib.typ").exists()
    assert (installed / "typst.toml").exists()
    assert not (installed / ".git").exists()


@patch("mdo.core.template.subprocess.run", side_effect=FileNotFoundError)
def test_update_git_not_found(mock_run: MagicMock) -> None:
    result = runner.invoke(app, ["update"])
    assert result.exit_code != 0
```

- [ ] **Step 8: Lint + Type-Check**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run ruff check src/ tests/ && uv run mypy src/`
Expected: Keine Fehler

- [ ] **Step 9: Commit**

```bash
git add src/mdo/core/template.py src/mdo/commands/update.py tests/test_core_template.py tests/test_update.py
git commit -m "feat(core): add template module with git and http install methods"
```

---

### Task 5: Core-Compiler (`core/compiler.py`)

**Files:**
- Create: `src/mdo/core/compiler.py`
- Create: `tests/test_core_compiler.py`
- Modify: `src/mdo/commands/compile.py`

- [ ] **Step 1: Failing Tests schreiben**

```python
# tests/test_core_compiler.py
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mdo.core.compiler import compile_letter, parse_letter
from mdo.exceptions import CompileError, FontError, FrontmatterError, ToolNotFoundError

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
        # Create a fake PDF at the output path
        pdf_path = Path(cmd[-1])
        pdf_path.write_bytes(b"%PDF-1.4 fake")
    return result


class TestCompileLetter:
    @patch("mdo.core.compiler.check_fonts", return_value=[])
    @patch("mdo.core.compiler.subprocess.run", side_effect=_mock_subprocess_run)
    @patch("mdo.core.markdown.subprocess.run", side_effect=_mock_subprocess_run)
    def test_returns_pdf_path(
        self, mock_md: MagicMock, mock_run: MagicMock, mock_fonts: MagicMock, tmp_path: Path
    ) -> None:
        p = tmp_path / "brief.md"
        p.write_text(LETTER_CONTENT)
        result = compile_letter(p)
        assert isinstance(result, Path)
        assert result.suffix == ".pdf"

    @patch("mdo.core.compiler.check_fonts", return_value=["Source Serif 4"])
    def test_raises_on_missing_fonts(self, mock_fonts: MagicMock, tmp_path: Path) -> None:
        p = tmp_path / "brief.md"
        p.write_text(LETTER_CONTENT)
        with pytest.raises(FontError):
            compile_letter(p)

    @patch("mdo.core.compiler.check_fonts", return_value=[])
    @patch("mdo.core.compiler.subprocess.run", side_effect=FileNotFoundError)
    def test_raises_on_missing_typst(
        self, mock_run: MagicMock, mock_fonts: MagicMock, tmp_path: Path
    ) -> None:
        p = tmp_path / "brief.md"
        p.write_text(LETTER_CONTENT)
        with pytest.raises(ToolNotFoundError):
            compile_letter(p)
```

- [ ] **Step 2: Tests ausführen — FAIL erwartet**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest tests/test_core_compiler.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implementierung**

```python
# src/mdo/core/compiler.py
"""Core compile pipeline — no CLI dependencies."""

import logging
import re
import subprocess
from pathlib import Path

import yaml
from pydantic import ValidationError

from mdo.core.fonts import check_fonts
from mdo.core.markdown import md_to_typst
from mdo.core.models import LetterData
from mdo.core.paths import fonts_dir
from mdo.core.typst_builder import build_typst_files
from mdo.exceptions import CompileError, FontError, FrontmatterError, ToolNotFoundError

logger = logging.getLogger(__name__)

GERMAN_MONTHS = {
    "Januar": "01",
    "Februar": "02",
    "März": "03",
    "April": "04",
    "Mai": "05",
    "Juni": "06",
    "Juli": "07",
    "August": "08",
    "September": "09",
    "Oktober": "10",
    "November": "11",
    "Dezember": "12",
}


def _sanitize(text: str) -> str:
    """Remove characters that are problematic in filenames."""
    return re.sub(r'[/\\:*?"<>|]', "", text).strip()


def _build_filename(data: LetterData) -> str | None:
    """Build filename as YYYY-MM-DD_recipient - subject."""
    if not data.date or not data.recipient or not data.subject:
        return None

    m = re.match(r"(\d{2})\.\s+(\S+)\s+(\d{4})", data.date)
    if m:
        day, month_name, year = m.group(1), m.group(2), m.group(3)
        month = GERMAN_MONTHS.get(month_name, "01")
        date_str = f"{year}-{month}-{day}"
    else:
        date_str = data.date

    recipient = _sanitize(data.recipient[0])
    subject = _sanitize(data.subject)

    if not recipient or not subject:
        return None

    return f"{date_str}_{recipient} - {subject}"


def parse_letter(path: Path) -> tuple[dict[str, object], str]:
    """Parse a letter .md into (frontmatter_dict, body_text).

    Raises:
        FileNotFoundError: If the file does not exist.
        FrontmatterError: If the frontmatter is invalid.
    """
    if not path.exists():
        msg = f"File not found: {path}"
        raise FileNotFoundError(msg)

    content = path.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) < 3:
        msg = "Invalid frontmatter in file"
        raise FrontmatterError(msg)
    fm = yaml.safe_load(parts[1])
    if not isinstance(fm, dict):
        msg = "Invalid frontmatter in file"
        raise FrontmatterError(msg)
    body = parts[2].strip()
    return fm, body


def _check_tool(name: str) -> None:
    """Check that an external tool is available."""
    try:
        subprocess.run([name, "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        msg = f"{name} not found"
        raise ToolNotFoundError(msg) from None


def _resolve_signature(data: LetterData, letter_dir: Path) -> None:
    """Resolve signature field: True → auto-detect, string → verify exists."""
    if data.signature is True:
        found = None
        for ext in ("svg", "png", "jpg", "gif"):
            candidate = letter_dir / f"unterschrift.{ext}"
            if candidate.exists():
                found = str(candidate.name)
                break
        data.signature = found
    elif isinstance(data.signature, str) and not (letter_dir / data.signature).exists():
        msg = f"Signature file not found: {data.signature}"
        raise FileNotFoundError(msg)


def compile_letter(
    letter_path: Path,
    *,
    keep_typ: bool = False,
    auto_rename: bool = True,
) -> Path:
    """Full compile pipeline: Parse → Validate → Convert → Compile → Rename.

    Returns the path to the generated PDF.

    Raises:
        FileNotFoundError: File not found.
        FontError: Required fonts missing.
        ToolNotFoundError: External tool not found.
        FrontmatterError: Invalid frontmatter.
        CompileError: Typst compilation failed.
    """
    if not letter_path.exists():
        msg = f"File not found: {letter_path}"
        raise FileNotFoundError(msg)

    if letter_path.suffix != ".md":
        msg = f"Expected a .md file, got '{letter_path.suffix}'"
        raise ValueError(msg)

    # Font check
    missing = check_fonts(fonts_dir())
    if missing:
        msg = f"Missing fonts: {', '.join(missing)}"
        raise FontError(msg)

    # Tool check
    _check_tool("typst")
    _check_tool("pandoc")

    # Parse
    fm, body = parse_letter(letter_path)

    # Validate
    try:
        data = LetterData.model_validate(fm)
    except ValidationError as e:
        errors = "; ".join(
            f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in e.errors()
        )
        msg = f"Validation failed: {errors}"
        raise FrontmatterError(msg) from None

    # Signature
    _resolve_signature(data, letter_path.parent)

    # Convert body
    typst_body = md_to_typst(body)

    # Build files
    typ_content, json_content = build_typst_files(data=data, body=typst_body)

    typ_path = letter_path.with_suffix(".typ")
    json_path = letter_path.with_name("brief.json")
    pdf_path = letter_path.with_suffix(".pdf")

    try:
        typ_path.write_text(typ_content, encoding="utf-8")
        json_path.write_text(json_content, encoding="utf-8")

        # Compile
        typst_cmd = ["typst", "compile", "--pdf-standard", "a-2b"]
        fdir = fonts_dir()
        if fdir.exists():
            typst_cmd.extend(["--font-path", str(fdir)])
        typst_cmd.extend([str(typ_path), str(pdf_path)])

        result = subprocess.run(
            typst_cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            msg = f"typst compile failed:\n{result.stderr}"
            raise CompileError(msg)

        # Auto-rename
        if auto_rename:
            final_name = _build_filename(data)
            if final_name and pdf_path.exists():
                try:
                    final_md = letter_path.parent / f"{final_name}.md"
                    final_pdf = letter_path.parent / f"{final_name}.pdf"
                    if final_md != letter_path:
                        letter_path.rename(final_md)
                    pdf_path.rename(final_pdf)
                    pdf_path = final_pdf
                    if keep_typ and typ_path.exists():
                        final_typ = letter_path.parent / f"{final_name}.typ"
                        typ_path.rename(final_typ)
                        typ_path = final_typ
                except OSError:
                    pass

        return pdf_path

    finally:
        if not keep_typ and typ_path.exists():
            typ_path.unlink()
        if json_path.exists():
            json_path.unlink()
```

- [ ] **Step 4: Tests ausführen — PASS erwartet**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest tests/test_core_compiler.py -v`
Expected: PASS

- [ ] **Step 5: Lint + Type-Check**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run ruff check src/mdo/core/compiler.py tests/test_core_compiler.py && uv run mypy src/`
Expected: Keine Fehler

- [ ] **Step 6: Commit**

```bash
git add src/mdo/core/compiler.py tests/test_core_compiler.py
git commit -m "feat(core): add framework-independent compile pipeline"
```

---

### Task 6: Commands auf Core delegieren

**Files:**
- Modify: `src/mdo/commands/compile.py`
- Modify: `tests/test_compile.py`

- [ ] **Step 1: `commands/compile.py` verschlanken**

```python
# src/mdo/commands/compile.py
import platform
import subprocess
from pathlib import Path

import typer

from mdo.core.compiler import compile_letter as core_compile
from mdo.exceptions import CompileError, FontError, FrontmatterError, ToolNotFoundError


def compile_letter(
    filename: str = typer.Argument(help="Letter .md file to compile"),
    typ: bool = typer.Option(False, "--typ", help="Keep the generated .typ file"),
) -> None:
    """Compile a letter .md to PDF/A-2b."""
    path = Path(filename)

    try:
        pdf_path = core_compile(path, keep_typ=typ)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except FontError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except ToolNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except FrontmatterError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except CompileError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    typer.echo(f"Created {pdf_path}")

    # Open/Reveal — these stay in the CLI layer
    # Read frontmatter again to check open/reveal flags
    from mdo.core.compiler import parse_letter
    from mdo.core.models import LetterData

    try:
        fm, _ = parse_letter(pdf_path.with_suffix(".md"))
        data = LetterData.model_validate(fm)
        if data.open:
            _open_file(pdf_path)
        if data.reveal:
            _reveal_file(pdf_path)
    except Exception:
        pass  # open/reveal is best-effort


def _open_file(path: Path) -> None:
    """Open file with the default application."""
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", str(path)], check=False)
    elif system == "Linux":
        subprocess.run(["xdg-open", str(path)], check=False)
    else:
        subprocess.run(["start", "", str(path)], check=False, shell=True)  # noqa: S603


def _reveal_file(path: Path) -> None:
    """Reveal file in the system file manager."""
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", "-R", str(path)], check=False)
    elif system == "Linux":
        subprocess.run(["xdg-open", str(path.parent)], check=False)
    else:
        subprocess.run(["explorer", "/select,", str(path)], check=False)
```

**Hinweis:** Die open/reveal-Logik hat ein Problem — nach dem auto-rename existiert die `.md`-Datei unter einem neuen Namen. Das `parse_letter` nach dem Compile muss den umbenannten Pfad finden. Alternative: `core_compile` gibt ein Result-Objekt zurück, das `open`/`reveal`-Flags enthält.

**Besserer Ansatz — LetterData zurückgeben:**

In `core/compiler.py` die Funktion `compile_letter` so erweitern, dass sie `(Path, LetterData)` zurückgibt:

```python
def compile_letter(...) -> tuple[Path, LetterData]:
    ...
    return pdf_path, data
```

Dann in `commands/compile.py`:

```python
pdf_path, data = core_compile(path, keep_typ=typ)
typer.echo(f"Created {pdf_path}")
if data.open:
    _open_file(pdf_path)
if data.reveal:
    _reveal_file(pdf_path)
```

- [ ] **Step 2: `core/compiler.py` Return-Type anpassen**

Signatur ändern zu:
```python
def compile_letter(...) -> tuple[Path, LetterData]:
```

Und am Ende:
```python
return pdf_path, data
```

- [ ] **Step 3: Tests anpassen**

In `tests/test_core_compiler.py`:
```python
def test_returns_pdf_path(...) -> None:
    ...
    result, data = compile_letter(p)
    assert isinstance(result, Path)
    assert result.suffix == ".pdf"
```

In `tests/test_compile.py` — Mock-Pfade aktualisieren:
- `mdo.commands.compile.check_fonts` → `mdo.core.compiler.check_fonts`
- `mdo.commands.compile.subprocess.run` → `mdo.core.compiler.subprocess.run`
- Die Test-Logik bleibt gleich, nur die Patch-Targets ändern sich.

```python
# tests/test_compile.py
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
    result = MagicMock()
    result.returncode = 0
    result.stderr = ""
    result.stdout = ""
    if cmd[0] == "pandoc" and "-f" in cmd:
        result.stdout = "Sehr geehrte Damen und Herren,\n\ndies ist ein #strong[Test]."
    elif cmd[0] == "typst" and "compile" in cmd:
        pdf_path = Path(cmd[-1])
        pdf_path.write_bytes(b"%PDF-1.4 fake")
    elif cmd[0] in ("typst", "pandoc") and "--version" in cmd:
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
    # After rename, the original .typ and .json should be cleaned up
    assert not (work_dir / "brief.typ").exists()
    assert not (work_dir / "brief.json").exists()
```

- [ ] **Step 4: Alle Tests ausführen**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest -v`
Expected: PASS

- [ ] **Step 5: Lint + Type-Check**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run ruff check src/ tests/ && uv run mypy src/`
Expected: Keine Fehler

- [ ] **Step 6: Commit**

```bash
git add src/mdo/commands/compile.py src/mdo/core/compiler.py tests/test_compile.py tests/test_core_compiler.py
git commit -m "refactor(compile): delegate compile command to core.compiler"
```

---

### Task 7: Finale Aufräumarbeiten

**Files:**
- Delete: `src/mdo/config.py` (falls noch nicht geschehen in Task 2)
- Modify: `src/mdo/commands/new.py` (Import-Update falls nötig)
- Verify: Alle Tests, Lint, Type-Check

- [ ] **Step 1: Prüfen, ob `config.py` noch existiert**

Run: `ls src/mdo/config.py 2>/dev/null && echo "EXISTS" || echo "ALREADY DELETED"`

Falls noch da: löschen und alle Imports auf `mdo.core.models` umbiegen.

- [ ] **Step 2: `grep` nach alten Imports**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && grep -r "from mdo.config" src/ tests/`
Run: `cd /Users/rolandkreus/GitHub/mdo-cli && grep -r "from mdo.commands.install_fonts import mdo_fonts_dir" src/`

Alle Treffer bereinigen.

- [ ] **Step 3: Alle Tests ausführen**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest -v`
Expected: PASS — alle Tests grün

- [ ] **Step 4: Lint + Type-Check + Format**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/ && uv run mypy src/`
Expected: Keine Fehler

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: remove config.py, clean up all imports"
```

---

## Zusammenfassung

| Task | Was | Neue Dateien |
|------|-----|-------------|
| 1 | `core/paths.py` erweitern | `tests/test_paths.py` |
| 2 | `ProfileConfig` → `core/models.py` | — |
| 3 | Multi-Profil-Modul | `core/profile.py`, `tests/test_core_profile.py` |
| 4 | Template-Modul (Git+HTTP) | `core/template.py`, `tests/test_core_template.py` |
| 5 | Core-Compiler | `core/compiler.py`, `tests/test_core_compiler.py` |
| 6 | Commands verschlanken | — |
| 7 | Aufräumen | — |

Nach Abschluss aller Tasks:
- `core/` ist Framework-unabhängig (kein Typer)
- `commands/` sind dünne Wrapper
- Multi-Profil funktioniert
- Template-Install via Git und HTTP
- CLI-Verhalten ist unverändert
- Alle Tests grün
