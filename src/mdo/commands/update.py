import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import typer

from mdo.core.paths import PACKAGE_NAME, typst_packages_dir

REPO_URL = "https://github.com/jcmx9/typst-DIN5008a.git"


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
        target = typst_packages_dir() / PACKAGE_NAME / version
        target.mkdir(parents=True, exist_ok=True)

        # Copy src/ directory (preserving structure for entrypoint "src/lib.typ")
        src_dir = tmp_path / "src"
        if not src_dir.exists():
            typer.echo("Error: src/ directory not found in template repo", err=True)
            raise typer.Exit(1)

        shutil.copytree(src_dir, target / "src", dirs_exist_ok=True)

        toml_src = tmp_path / "typst.toml"
        shutil.copy2(toml_src, target / "typst.toml")

        typer.echo(f"Installed {PACKAGE_NAME} v{version} to {target}")
