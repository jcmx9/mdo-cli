import logging

import typer

from mdo.core.models import ProfileConfig
from mdo.core.profile import delete_profile as core_delete
from mdo.core.profile import list_profiles as core_list
from mdo.core.profile import save_profile as core_save

logger = logging.getLogger(__name__)

profile_app = typer.Typer(
    name="profile",
    help="Absenderprofile verwalten.",
    invoke_without_command=True,
)


@profile_app.callback()
def profile_callback(ctx: typer.Context) -> None:
    """Absenderprofile verwalten. Ohne Subcommand: neues Profil anlegen."""
    if ctx.invoked_subcommand is None:
        create(name="default")


PROFILE_FIELDS = [
    ("name", "Name", "Max Mustermann"),
    ("street", "Strasse", "Musterstrasse 1"),
    ("zip", "PLZ", "12345"),
    ("city", "Ort", "Musterstadt"),
    ("phone", "Telefon", "0123 456789"),
    ("email", "E-Mail", "max@example.de"),
    ("iban", "IBAN (null = ohne)", "null"),
    ("bic", "BIC (null = ohne)", "null"),
    ("bank", "Bank (null = ohne)", "null"),
    ("accent", "Akzentfarbe (Hex oder null)", "null"),
    ("signature_width", "Unterschrift-Breite in mm (null = Standard)", "null"),
]


@profile_app.command("create")
def create(
    name: str = typer.Option("default", "--name", "-n", help="Profile name"),
) -> None:
    """Neues Absenderprofil interaktiv anlegen."""
    typer.echo(f"Neues Absenderprofil '{name}' anlegen. Enter fuer Standardwert.\n")

    data: dict[str, object] = {}

    for key, label, default in PROFILE_FIELDS:
        value = typer.prompt(f"  {label}", default=default)
        if key in ("accent", "signature_width", "iban", "bic", "bank") and value.lower() == "null":
            data[key] = None
        elif key == "signature_width" and value.lower() != "null":
            data[key] = int(value)
        else:
            data[key] = value

    qr_input = typer.prompt("  vCard QR-Code anzeigen (ja/nein)", default="ja")
    data["qr_code"] = qr_input.lower() in ("ja", "j", "yes", "y", "true")
    sig_input = typer.prompt("  Unterschrift verwenden (ja/nein)", default="ja")
    data["signature"] = sig_input.lower() in ("ja", "j", "yes", "y", "true")
    closing = typer.prompt("  Schlussgruss", default="Mit freundlichem Gruß")
    data["closing"] = closing
    data["open"] = True
    data["reveal"] = True

    config = ProfileConfig.model_validate(data)
    path = core_save(config, name=name)
    typer.echo(f"\nCreated profile '{name}' at {path}")


@profile_app.command("list")
def list_cmd() -> None:
    """Alle verfuegbaren Profile anzeigen."""
    names = core_list()
    if not names:
        typer.echo("Keine Profile gefunden. Erstelle eines mit: mdo profile create")
        return
    for n in names:
        typer.echo(f"  {n}")


@profile_app.command("delete")
def delete(
    name: str = typer.Argument(help="Name des zu loeschenden Profils"),
) -> None:
    """Ein Profil loeschen."""
    try:
        core_delete(name)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    typer.echo(f"Deleted profile '{name}'")
