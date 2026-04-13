import logging
import subprocess
import tempfile
import zipfile
from pathlib import Path

import typer

logger = logging.getLogger(__name__)

FONTS = [
    {
        "name": "Source Serif 4",
        "repo": "adobe-fonts/source-serif",
        "asset_prefix": "source-serif",
        "asset_suffix": "Desktop.zip",
        "glob": "*/OTF/*.otf",
    },
    {
        "name": "Source Sans 3",
        "repo": "adobe-fonts/source-sans",
        "asset_prefix": "OTF-source-sans",
        "asset_suffix": ".zip",
        "glob": "*.otf",
    },
    {
        "name": "Source Code Pro",
        "repo": "adobe-fonts/source-code-pro",
        "asset_prefix": "OTF-source-code-pro",
        "asset_suffix": ".zip",
        "glob": "*.otf",
    },
]


def mdo_fonts_dir() -> Path:
    """Return the mdo-specific fonts directory."""
    return Path.home() / ".local" / "share" / "mdo" / "fonts"


def _get_download_url(repo: str, prefix: str, suffix: str) -> str | None:
    """Get the download URL for the latest release asset matching prefix/suffix."""
    import json

    try:
        result = subprocess.run(
            ["curl", "-sL", f"https://api.github.com/repos/{repo}/releases/latest"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    data = json.loads(result.stdout)
    for asset in data.get("assets", []):
        name = asset["name"]
        if name.startswith(prefix) and name.endswith(suffix):
            return str(asset["browser_download_url"])
    return None


def install_fonts() -> None:
    """Download and install required fonts for the din5008a template."""
    fonts_dir = mdo_fonts_dir()
    fonts_dir.mkdir(parents=True, exist_ok=True)
    logger.debug("Font target directory: %s", fonts_dir)

    for font in FONTS:
        typer.echo(f"Downloading {font['name']} ...")

        logger.debug("Fetching release URL for %s from %s", font["name"], font["repo"])
        url = _get_download_url(font["repo"], font["asset_prefix"], font["asset_suffix"])
        if not url:
            typer.echo(f"  Error: could not find release for {font['name']}", err=True)
            continue

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            zip_path = tmp_path / "font.zip"

            try:
                subprocess.run(
                    ["curl", "-sL", "-o", str(zip_path), url],
                    check=True,
                )
            except (FileNotFoundError, subprocess.CalledProcessError):
                typer.echo(f"  Error: download failed for {font['name']}", err=True)
                continue

            with zipfile.ZipFile(zip_path) as zf:
                installed = 0
                for entry in zf.namelist():
                    entry_path = Path(entry)
                    if entry_path.suffix.lower() == ".otf" and entry_path.match(font["glob"]):
                        dest = fonts_dir / entry_path.name
                        dest.write_bytes(zf.read(entry))
                        installed += 1

            typer.echo(f"  Installed {installed} fonts to {fonts_dir}")

    typer.echo("Done.")
