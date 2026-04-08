from typing import Optional

import typer

from mdo import __version__
from mdo.commands.compile import compile_letter
from mdo.commands.install_fonts import install_fonts
from mdo.commands.new import new
from mdo.commands.profile import profile
from mdo.commands.update import update

app = typer.Typer(
    name="mdo",
    help="Generate DIN 5008 Form A business letters as PDF/A from Markdown.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"mdo {__version__}")
        raise typer.Exit


def _markdown_callback(value: bool) -> None:
    if value:
        table = (
            "Markdown Cheatsheet\n"
            "\n"
            "  Fett            **text**\n"
            "  Kursiv          *text*\n"
            "  Aufzählung      - Punkt\n"
            "  Nummerierung    1. Punkt\n"
            "  Monospace (feste Zeichenbreite)\n"
            "    Inline         `text`\n"
            "    Block          ```text```\n"
            "  Zeilenumbruch   \\ am Zeilenende\n"
            "  Trennlinie      ---\n"
        )
        typer.echo(table)
        raise typer.Exit


@app.callback()
def main(
    version: Optional[bool] = typer.Option(  # noqa: UP007
        None,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
    markdown: Optional[bool] = typer.Option(  # noqa: UP007
        None,
        "--markdown",
        help="Show Markdown cheatsheet and exit.",
        callback=_markdown_callback,
        is_eager=True,
    ),
) -> None:
    """Generate DIN 5008 Form A business letters as PDF/A from Markdown."""


app.command("compile")(compile_letter)
app.command("install-fonts")(install_fonts)
app.command()(new)
app.command()(profile)
app.command()(update)
