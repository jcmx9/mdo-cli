from typing import Optional

import typer

from mdo import __version__
from mdo.commands.compile import compile_letter
from mdo.commands.new import new
from mdo.commands.profile import profile

app = typer.Typer(
    name="mdo",
    help="Generate DIN 5008 Form A business letters as PDF/A from Markdown.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"mdo {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: Optional[bool] = typer.Option(  # noqa: UP007
        None, "--version", "-V", help="Show version and exit.", callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Generate DIN 5008 Form A business letters as PDF/A from Markdown."""


app.command("compile")(compile_letter)
app.command()(new)
app.command()(profile)
