from pathlib import Path

import typer


PROFILE_FILE = "profile.yaml"

PROFILE_FIELDS = [
    ("name", "Name", "Max Mustermann"),
    ("street", "Strasse", "Musterstrasse 1"),
    ("zip", "PLZ", "12345"),
    ("city", "Ort", "Musterstadt"),
    ("phone", "Telefon", "0123 456789"),
    ("email", "E-Mail", "max@example.de"),
    ("iban", "IBAN", "DE89 3704 0044 0532 0130 00"),
    ("bic", "BIC", "COBADEFFXXX"),
    ("bank", "Bank", "Commerzbank"),
]


def _write_profile(data: dict[str, object], path: Path) -> None:
    """Write profile.yaml without quoting string values."""
    lines: list[str] = []
    for key, value in data.items():
        if value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f"{key}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def profile() -> None:
    """Create a new profile.yaml interactively."""
    path = Path(PROFILE_FILE)
    if path.exists():
        typer.echo(f"Error: {PROFILE_FILE} already exists", err=True)
        raise typer.Exit(1)

    typer.echo("Neues Absenderprofil anlegen. Enter fuer Standardwert.\n")

    data: dict[str, object] = {}

    for key, label, default in PROFILE_FIELDS:
        value = typer.prompt(f"  {label}", default=default)
        data[key] = value

    # Non-interactive fields with sensible defaults
    qr_input = typer.prompt("  vCard QR-Code anzeigen (ja/nein)", default="ja")
    data["qr_code"] = qr_input.lower() in ("ja", "j", "yes", "y", "true")
    data["signature"] = None
    closing = typer.prompt("  Schlussgruss", default="Mit freundlichem Gruß")
    data["closing"] = closing

    _write_profile(data, path)
    typer.echo(f"\nCreated {PROFILE_FILE}")
