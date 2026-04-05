import datetime
import platform
import subprocess
from pathlib import Path

import typer
import yaml

from mdo.core.fonts import FONT_HELP_URL, check_fonts
from mdo.core.markdown import md_to_typst
from mdo.core.typst_builder import build_typst

GERMAN_MONTHS = [
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
]

REQUIRED_FIELDS = {"name", "street", "zip", "city", "recipient", "closing"}


def _format_german_date(d: datetime.date) -> str:
    """Format date as '05. April 2026'."""
    return f"{d.day:02d}. {GERMAN_MONTHS[d.month - 1]} {d.year}"


def _parse_letter(path: Path) -> tuple[dict[str, object], str]:
    """Parse a letter .md into (frontmatter_dict, body_text)."""
    content = path.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) < 3:
        typer.echo("Error: Invalid frontmatter in file", err=True)
        raise typer.Exit(1)
    fm = yaml.safe_load(parts[1])
    if not isinstance(fm, dict):
        typer.echo("Error: Invalid frontmatter in file", err=True)
        raise typer.Exit(1)
    # Validate required fields
    missing = REQUIRED_FIELDS - set(fm.keys())
    if missing:
        typer.echo(f"Error: Missing required fields: {', '.join(sorted(missing))}", err=True)
        raise typer.Exit(1)
    body = parts[2].strip()
    return fm, body


def compile_letter(
    filename: str = typer.Argument(help="Letter .md file to compile"),
) -> None:
    """Compile a letter .md to PDF/A-2b."""
    path = Path(filename)

    # Must be a .md file
    if path.suffix != ".md":
        typer.echo(f"Error: Expected a .md file, got '{path.suffix}'", err=True)
        raise typer.Exit(1)

    if not path.exists():
        typer.echo(f"Error: File not found: {filename}", err=True)
        raise typer.Exit(1)

    # Font check
    missing = check_fonts()
    if missing:
        typer.echo(f"Error: Missing system fonts: {', '.join(missing)}", err=True)
        typer.echo(f"Install static font variants. See requirements: {FONT_HELP_URL}", err=True)
        raise typer.Exit(1)

    # Check typst is available
    try:
        subprocess.run(["typst", "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        typer.echo("Error: typst not found. Install: https://typst.app", err=True)
        raise typer.Exit(1)

    # Parse
    fm, body = _parse_letter(path)

    # Resolve date
    date_val = fm.get("date")
    if date_val is None:
        date_str = _format_german_date(datetime.date.today())
    else:
        date_str = str(date_val)

    # Resolve signature
    signature_val = fm.get("signature")
    signature_file: str | None = None
    if signature_val:
        sig_path = Path(str(signature_val))
        if not sig_path.exists():
            typer.echo(f"Error: Signature file not found: {signature_val}", err=True)
            raise typer.Exit(1)
        signature_file = str(signature_val)

    # Convert body
    typst_body = md_to_typst(body)

    # Build sender dict
    sender = {
        "name": fm.get("name", ""),
        "street": fm.get("street", ""),
        "zip": fm.get("zip", ""),
        "city": fm.get("city", ""),
        "phone": fm.get("phone", ""),
        "email": fm.get("email", ""),
        "iban": fm.get("iban", ""),
        "bic": fm.get("bic", ""),
        "bank": fm.get("bank", ""),
        "qr_code": fm.get("qr_code", False),
    }

    raw_recipient = fm.get("recipient", [])
    recipient: list[str] = (
        [str(r) for r in raw_recipient] if isinstance(raw_recipient, list) else []
    )
    if not recipient:
        typer.echo("Error: recipient is empty. Add at least one address line.", err=True)
        raise typer.Exit(1)
    subject = str(fm.get("subject", "") or "")
    closing = str(fm.get("closing", "Mit freundlichem Gruß"))

    # Generate .typ
    typ_content = build_typst(
        sender=sender,
        recipient=recipient,
        date=date_str,
        subject=subject or "",
        body=typst_body,
        closing=closing,
        signature=signature_file,
    )

    typ_path = path.with_suffix(".typ")
    pdf_path = path.with_suffix(".pdf")

    try:
        typ_path.write_text(typ_content, encoding="utf-8")

        result = subprocess.run(
            ["typst", "compile", "--pdf-standard", "a-2b", str(typ_path), str(pdf_path)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            typer.echo(f"Error: typst compile failed:\n{result.stderr}", err=True)
            raise typer.Exit(1)

        typer.echo(f"Created {pdf_path}")

        # Post-compile actions from frontmatter
        if fm.get("open"):
            _open_file(pdf_path)
        if fm.get("reveal"):
            _reveal_file(pdf_path)
    finally:
        if typ_path.exists():
            typ_path.unlink()


def _open_file(path: Path) -> None:
    """Open file with the default application."""
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", str(path)], check=False)
    elif system == "Linux":
        subprocess.run(["xdg-open", str(path)], check=False)
    else:
        subprocess.run(["start", "", str(path)], check=False, shell=True)  # noqa: S603


def _reveal_file(path: Path) -> None:
    """Reveal file in the system file manager."""
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", "-R", str(path)], check=False)
    elif system == "Linux":
        subprocess.run(["xdg-open", str(path.parent)], check=False)
    else:
        subprocess.run(["explorer", "/select,", str(path)], check=False)
