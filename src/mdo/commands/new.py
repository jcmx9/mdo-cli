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

    # Build frontmatter: profile fields + letter-specific fields
    fm = dict(profile_data)
    fm["date"] = None
    fm["subject"] = None
    fm["recipient"] = [
        "Firma GmbH",
        "Frau / Herrn Vorname Nachname",
        "Strasse Nr.",
        "PLZ Ort",
    ]

    # Write with manual YAML to place the date comment
    fm_text = yaml.dump(
        fm, allow_unicode=True, default_flow_style=False, sort_keys=False
    )
    fm_text = fm_text.replace("date: null", "date: null  # JJJJ-MM-TT")

    content = f"---\n{fm_text}---\n\nSehr geehrte Damen und Herren,\n\n\n"

    Path(target).write_text(content)
    typer.echo(f"Created {target}")
