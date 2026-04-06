import datetime
import re
from pathlib import Path
from typing import Optional

import typer
import yaml

from mdo.commands.profile import PROFILE_FILE


def _next_filename() -> str:
    """Generate YYYY-MM-DD_BriefCC.md with collision avoidance."""
    today = datetime.date.today().isoformat()
    pattern = re.compile(rf"^{re.escape(today)}_Brief(\d{{2}})\.md$")
    existing: list[int] = []
    for p in Path(".").iterdir():
        m = pattern.match(p.name)
        if m:
            existing.append(int(m.group(1)))
    counter = max(existing, default=0) + 1
    return f"{today}_Brief{counter:02d}.md"


def _format_value(value: object) -> str:
    """Format a value for YAML frontmatter without quoting strings."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        lines = [f"\n  - {item}" for item in value]
        return "".join(lines)
    s = str(value)
    if s.startswith("#"):
        return f'"{s}"'
    return s


def new(
    filename: Optional[str] = typer.Argument(  # noqa: UP007
        None, help="Output filename (auto-generated if omitted)"
    ),
) -> None:
    """Create a new letter .md from profile.yaml."""
    profile_path = Path(PROFILE_FILE)
    if not profile_path.exists():
        typer.echo(f"Error: {PROFILE_FILE} not found in current directory", err=True)
        raise typer.Exit(1)

    profile_data = yaml.safe_load(profile_path.read_text())

    target = filename if filename else _next_filename()

    # Build frontmatter lines manually to avoid yaml.dump quoting
    lines: list[str] = ["---"]
    for key, value in profile_data.items():
        lines.append(f"{key}: {_format_value(value)}")

    lines.append("date: null  # JJJJ-MM-TT")
    lines.append("subject: null")
    lines.append(
        "recipient:"
        "\n  - Firma GmbH"
        "\n  - Frau / Herrn Vorname Nachname"
        "\n  - Strasse Nr."
        "\n  - PLZ Ort"
    )
    lines.append("attachments: []")
    lines.append("---")

    fm_text = "\n".join(lines)
    content = f"{fm_text}\n\nSehr geehrte Damen und Herren,\n\n\n"

    Path(target).write_text(content, encoding="utf-8")
    typer.echo(f"Created {target}")
