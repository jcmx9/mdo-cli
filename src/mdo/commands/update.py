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
