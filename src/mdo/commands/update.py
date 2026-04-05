import platform
import re
import subprocess
import tempfile
from pathlib import Path

import typer

REPO_URL = "https://github.com/jcmx9/typst-DIN5008a.git"
PACKAGE_NAME = "din5008a"


def _packages_dir() -> Path:
    """Return the local Typst packages directory for the current OS."""
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "typst" / "packages" / "local"
    if system == "Linux":
        return Path.home() / ".local" / "share" / "typst" / "packages" / "local"
    # Windows
    app_data = Path.home() / "AppData" / "Roaming" / "typst" / "packages" / "local"
    return app_data


def _read_version(repo_dir: Path) -> str:
    """Read package version from typst.toml."""
    toml_path = repo_dir / "typst.toml"
    if not toml_path.exists():
        typer.echo("Error: typst.toml not found in template repo", err=True)
        raise typer.Exit(1)
    content = toml_path.read_text()
    match = re.search(r'^version\s*=\s*"(.+?)"', content, re.MULTILINE)
    if not match:
        typer.echo("Error: version not found in typst.toml", err=True)
        raise typer.Exit(1)
    return match.group(1)


def update() -> None:
    """Download/update the din5008a Typst template."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / "repo"

        typer.echo(f"Cloning {REPO_URL} ...")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", REPO_URL, str(tmp_path)],
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError:
            typer.echo("Error: git not found", err=True)
            raise typer.Exit(1)
        except subprocess.CalledProcessError as e:
            typer.echo(f"Error: git clone failed:\n{e.stderr}", err=True)
            raise typer.Exit(1)

        version = _read_version(tmp_path)
        target = _packages_dir() / PACKAGE_NAME / version
        target.mkdir(parents=True, exist_ok=True)

        # Copy src/* and typst.toml
        src_dir = tmp_path / "src"
        if not src_dir.exists():
            typer.echo("Error: src/ directory not found in template repo", err=True)
            raise typer.Exit(1)

        for f in src_dir.iterdir():
            dest = target / f.name
            dest.write_bytes(f.read_bytes())

        toml_src = tmp_path / "typst.toml"
        (target / "typst.toml").write_bytes(toml_src.read_bytes())

        typer.echo(f"Installed {PACKAGE_NAME} v{version} to {target}")
