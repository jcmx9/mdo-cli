import datetime
import re
from pathlib import Path
from typing import Optional

import typer
import yaml

from mdo.commands.profile import FIELD_COMMENTS, PROFILE_FILE


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


LETTER_COMMENTS: dict[str, str] = {
    "date": "Briefdatum, JJJJ-MM-TT (null = heute)",
    "subject": "Betreffzeile",
    "recipient": "Empfaenger-Adresszeilen",
    "attachments": "Anlagen (am Briefende dargestellt)",
}


DEFAULT_RECIPIENT = [
    "Firma/Amt",
    "Vorname Nachname",
    "Strassenname 1a",
    "12345 Musterstadt",
]


def _prompt_recipient() -> list[str]:
    """Prompt for recipient address lines. Enter on empty line = default/done."""
    typer.echo("  Empfaenger (Zeile fuer Zeile, leere Zeile = fertig):")
    recipient_lines: list[str] = []
    for i, default in enumerate(DEFAULT_RECIPIENT):
        raw = typer.prompt(f"    Zeile {i + 1}", default=default)
        recipient_lines.append(raw)

    # Additional lines beyond the 4 defaults
    while True:
        raw = typer.prompt(f"    Zeile {len(recipient_lines) + 1}", default="")
        if not raw:
            break
        recipient_lines.append(raw)

    return recipient_lines


def _build_frontmatter(
    profile_data: dict[str, object],
    subject: str | None,
    date_value: str | None,
    recipient: list[str],
) -> str:
    """Build YAML frontmatter string from profile and letter fields."""
    comments = {**FIELD_COMMENTS, **LETTER_COMMENTS}

    lines: list[str] = ["---"]
    for key, value in profile_data.items():
        comment = comments.get(key, "")
        suffix = f"  # {comment}" if comment else ""
        lines.append(f"{key}: {_format_value(value)}{suffix}")

    lines.append(f"date: {_format_value(date_value)}  # {comments['date']}")
    lines.append(f"subject: {_format_value(subject)}  # {comments['subject']}")
    lines.append(
        f"recipient:  # {comments['recipient']}" + "".join(f"\n  - {line}" for line in recipient)
    )
    lines.append(
        f"# attachments:  # {comments['attachments']}"
        "\n#   - Lebenslauf"
        "\n#   - Zeugnis"
        "\nattachments: []"
    )
    lines.append("---")
    return "\n".join(lines)


def new(
    filename: Optional[str] = typer.Argument(  # noqa: UP007
        None, help="Output filename (auto-generated if omitted)"
    ),
    silent: bool = typer.Option(
        False, "--silent", "-s", help="Skip interactive prompts, use defaults"
    ),
) -> None:
    """Create a new letter .md from profile.yaml."""
    profile_path = Path(PROFILE_FILE)
    if not profile_path.exists():
        typer.echo(f"Error: {PROFILE_FILE} not found in current directory", err=True)
        raise typer.Exit(1)

    profile_data = yaml.safe_load(profile_path.read_text())

    if silent:
        subject = None
        date_value = None
        recipient = list(DEFAULT_RECIPIENT)
    else:
        typer.echo("Neuen Brief anlegen. Enter fuer Standardwert.\n")

        subject_input = typer.prompt("  Betreff", default="")
        subject = subject_input if subject_input else None

        date_input = typer.prompt("  Datum (JJJJ-MM-TT)", default="heute")
        date_value = None if date_input.lower() == "heute" else date_input

        recipient = _prompt_recipient()

    target = filename if filename else _next_filename()

    fm_text = _build_frontmatter(profile_data, subject, date_value, recipient)
    content = f"{fm_text}\n\nSehr geehrte Damen und Herren,\n\n\n"

    Path(target).write_text(content, encoding="utf-8")
    typer.echo(f"Created {target}")
