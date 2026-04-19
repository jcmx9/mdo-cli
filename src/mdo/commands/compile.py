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
        pdf_path, data = core_compile(path, keep_typ=typ)
    except (FileNotFoundError, ValueError, FontError, ToolNotFoundError, FrontmatterError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except CompileError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    typer.echo(f"Created {pdf_path}")

    if data.open:
        _open_file(pdf_path)
    if data.reveal:
        _reveal_file(pdf_path)


def _open_file(path: Path) -> None:
    """Open file with the default application."""
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", str(path)], check=False)
    elif system == "Linux":
        subprocess.run(["xdg-open", str(path)], check=False)
    else:
        subprocess.run(["start", "", str(path)], check=False, shell=True)


def _reveal_file(path: Path) -> None:
    """Reveal file in the system file manager."""
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", "-R", str(path)], check=False)
    elif system == "Linux":
        subprocess.run(["xdg-open", str(path.parent)], check=False)
    else:
        subprocess.run(["explorer", "/select,", str(path)], check=False)
