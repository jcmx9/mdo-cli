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
    ("accent", "Akzentfarbe (Hex oder null)", "null"),
]

FIELD_COMMENTS: dict[str, str] = {
    "name": "Absendername",
    "street": "Strasse und Hausnummer",
    "zip": "Postleitzahl",
    "city": "Ort",
    "phone": "Telefonnummer",
    "email": "E-Mail-Adresse",
    "iban": "Bank-IBAN",
    "bic": "Bank-BIC",
    "bank": "Bankname",
    "accent": "Akzentfarbe als Hex (null = Template-Standard)",
    "qr_code": "vCard-QR-Code im Infoblock anzeigen",
    "signature": "Unterschrift-Datei automatisch suchen (unterschrift.svg/png/jpg/gif)",
    "closing": "Schlussgruss",
    "open": "PDF nach Kompilierung oeffnen",
    "reveal": "PDF im Dateimanager anzeigen",
}


def _write_profile(data: dict[str, object], path: Path) -> None:
    """Write profile.yaml with inline comments."""
    lines: list[str] = []
    for key, value in data.items():
        if value is None:
            formatted = "null"
        elif isinstance(value, bool):
            formatted = "true" if value else "false"
        elif isinstance(value, str) and value.startswith("#"):
            formatted = f'"{value}"'
        else:
            formatted = str(value)

        comment = FIELD_COMMENTS.get(key, "")
        if comment:
            lines.append(f"{key}: {formatted}  # {comment}")
        else:
            lines.append(f"{key}: {formatted}")
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
        if key == "accent" and value.lower() == "null":
            data[key] = None
        else:
            data[key] = value

    # Non-interactive fields with sensible defaults
    qr_input = typer.prompt("  vCard QR-Code anzeigen (ja/nein)", default="ja")
    data["qr_code"] = qr_input.lower() in ("ja", "j", "yes", "y", "true")
    sig_input = typer.prompt("  Unterschrift verwenden (ja/nein)", default="ja")
    data["signature"] = sig_input.lower() in ("ja", "j", "yes", "y", "true")
    closing = typer.prompt("  Schlussgruss", default="Mit freundlichem Gruß")
    data["closing"] = closing
    data["open"] = True
    data["reveal"] = True

    _write_profile(data, path)
    typer.echo(f"\nCreated {PROFILE_FILE}")
