from pathlib import Path

import typer
import yaml


PROFILE_FILE = "profile.yaml"

PROFILE_TEMPLATE: dict[str, object] = {
    "name": "",
    "street": "Musterstrasse 1",
    "zip": "12345",
    "city": "Musterstadt",
    "phone": "0123 456789",
    "email": "max@example.de",
    "iban": "DE89 3704 0044 0532 0130 00",
    "bic": "COBADEFFXXX",
    "bank": "Commerzbank",
    "qr_code": True,
    "signature": None,
    "closing": "Mit freundlichem Gruß",
}


def profile(name: str = typer.Argument(help="Sender name for the profile")) -> None:
    """Create a new profile.yaml in the current directory."""
    path = Path(PROFILE_FILE)
    if path.exists():
        typer.echo(f"Error: {PROFILE_FILE} already exists", err=True)
        raise typer.Exit(1)

    data = dict(PROFILE_TEMPLATE)
    data["name"] = name

    path.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
    )
    typer.echo(f"Created {PROFILE_FILE}")
