import platform
import subprocess
from pathlib import Path

import typer
import yaml
from pydantic import ValidationError

from mdo.core.fonts import FONT_HELP_URL, check_fonts
from mdo.core.markdown import md_to_typst
from mdo.core.models import LetterData
from mdo.core.typst_builder import build_typst_files


def _parse_letter(path: Path) -> tuple[dict[str, object], str]:
    """Parse a letter .md into (frontmatter_dict, body_text)."""
    content = path.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) < 3:
        typer.echo("Error: Invalid frontmatter in file", err=True)
        raise typer.Exit(1)
    fm = yaml.safe_load(parts[1])
    if not isinstance(fm, dict):
        typer.echo("Error: Invalid frontmatter in file", err=True)
        raise typer.Exit(1)
    body = parts[2].strip()
    return fm, body


def compile_letter(
    filename: str = typer.Argument(help="Letter .md file to compile"),
) -> None:
    """Compile a letter .md to PDF/A-2b."""
    path = Path(filename)

    if path.suffix != ".md":
        typer.echo(f"Error: Expected a .md file, got '{path.suffix}'", err=True)
        raise typer.Exit(1)

    if not path.exists():
        typer.echo(f"Error: File not found: {filename}", err=True)
        raise typer.Exit(1)

    # Font check
    missing = check_fonts()
    if missing:
        typer.echo(f"Error: Missing system fonts: {', '.join(missing)}", err=True)
        typer.echo(f"Install static font variants. See requirements: {FONT_HELP_URL}", err=True)
        raise typer.Exit(1)

    # Check external tools
    for tool, url in [("typst", "https://typst.app"), ("pandoc", "https://pandoc.org")]:
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
        except FileNotFoundError:
            typer.echo(f"Error: {tool} not found. Install: {url}", err=True)
            raise typer.Exit(1)

    # Parse frontmatter + body
    fm, body = _parse_letter(path)

    # Validate with Pydantic
    try:
        data = LetterData.model_validate(fm)
    except ValidationError as e:
        for err in e.errors():
            field = ".".join(str(x) for x in err["loc"])
            typer.echo(f"Error: {field}: {err['msg']}", err=True)
        raise typer.Exit(1)

    # Signature: resolve boolean/string to actual file
    if data.signature is True:
        found = None
        for ext in ("svg", "png", "jpg", "gif"):
            candidate = path.parent / f"unterschrift.{ext}"
            if candidate.exists():
                found = str(candidate.name)
                break
        data.signature = found
    elif data.signature and not Path(data.signature).exists():
        typer.echo(f"Error: Signature file not found: {data.signature}", err=True)
        raise typer.Exit(1)

    # Convert body via Pandoc
    try:
        typst_body = md_to_typst(body)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    # Build .typ + .json
    typ_content, json_content = build_typst_files(data=data, body=typst_body)

    typ_path = path.with_suffix(".typ")
    json_path = path.with_name("brief.json")
    pdf_path = path.with_suffix(".pdf")

    try:
        typ_path.write_text(typ_content, encoding="utf-8")
        json_path.write_text(json_content, encoding="utf-8")

        result = subprocess.run(
            ["typst", "compile", "--pdf-standard", "a-2b", str(typ_path), str(pdf_path)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            typer.echo(f"Error: typst compile failed:\n{result.stderr}", err=True)
            raise typer.Exit(1)

        typer.echo(f"Created {pdf_path}")

        if data.open:
            _open_file(pdf_path)
        if data.reveal:
            _reveal_file(pdf_path)
    finally:
        if typ_path.exists():
            typ_path.unlink()
        if json_path.exists():
            json_path.unlink()


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
