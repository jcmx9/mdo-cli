"""Core compile pipeline — no CLI dependencies."""

import logging
import re
import shutil
import subprocess
from pathlib import Path

import yaml
from pydantic import ValidationError

from mdo.core.fonts import check_fonts
from mdo.core.markdown import md_to_typst
from mdo.core.models import LetterData
from mdo.core.paths import fonts_dir
from mdo.core.typst_builder import build_typst_files
from mdo.exceptions import CompileError, FontError, FrontmatterError, ToolNotFoundError

logger = logging.getLogger(__name__)

GERMAN_MONTHS = {
    "Januar": "01",
    "Februar": "02",
    "März": "03",
    "April": "04",
    "Mai": "05",
    "Juni": "06",
    "Juli": "07",
    "August": "08",
    "September": "09",
    "Oktober": "10",
    "November": "11",
    "Dezember": "12",
}


def _sanitize(text: str) -> str:
    """Remove characters that are problematic in filenames."""
    return re.sub(r'[/\\:*?"<>|]', "", text).strip()


def _build_filename(data: LetterData) -> str | None:
    """Build filename as YYYY-MM-DD_recipient - subject."""
    if not data.date or not data.recipient or not data.subject:
        return None

    m = re.match(r"(\d{2})\.\s+(\S+)\s+(\d{4})", data.date)
    if m:
        day, month_name, year = m.group(1), m.group(2), m.group(3)
        month = GERMAN_MONTHS.get(month_name, "01")
        date_str = f"{year}-{month}-{day}"
    else:
        date_str = data.date

    recipient = _sanitize(data.recipient[0])
    subject = _sanitize(data.subject)

    if not recipient or not subject:
        return None

    return f"{date_str}_{recipient} - {subject}"


def parse_letter(path: Path) -> tuple[dict[str, object], str]:
    """Parse a letter .md into (frontmatter_dict, body_text).

    Raises:
        FileNotFoundError: If the file does not exist.
        FrontmatterError: If the frontmatter is invalid.
    """
    if not path.exists():
        msg = f"File not found: {path}"
        raise FileNotFoundError(msg)

    content = path.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) < 3:
        msg = "Invalid frontmatter in file"
        raise FrontmatterError(msg)
    fm = yaml.safe_load(parts[1])
    if not isinstance(fm, dict):
        msg = "Invalid frontmatter in file"
        raise FrontmatterError(msg)
    body = parts[2].strip()
    return fm, body


def _check_tool(name: str) -> None:
    """Check that an external tool is available."""
    try:
        subprocess.run([name, "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        msg = f"{name} not found"
        raise ToolNotFoundError(msg) from None


def _resolve_signature(data: LetterData, letter_dir: Path) -> None:
    """Resolve signature field: True -> auto-detect, string -> verify exists.

    Searches in letter_dir first, then in profile directories.
    """
    if data.signature is True:
        found = None
        # Suche im Brief-Verzeichnis
        for ext in ("svg", "png", "jpg", "gif"):
            candidate = letter_dir / f"unterschrift.{ext}"
            if candidate.exists():
                found = str(candidate)
                break
        # Suche in den Profil-Verzeichnissen
        if found is None:
            from mdo.core.paths import profiles_dir

            pdir = profiles_dir()
            if pdir.exists():
                for profile in sorted(pdir.iterdir()):
                    if not profile.is_dir():
                        continue
                    for ext in ("svg", "png", "jpg", "gif"):
                        for candidate in profile.glob(f"unterschrift*.{ext}"):
                            found = str(candidate)
                            break
                        if found:
                            break
                    if found:
                        break
        data.signature = found
    elif isinstance(data.signature, str):
        sig_path = Path(data.signature)
        # Absoluter Pfad → direkt prüfen
        if sig_path.is_absolute():
            if not sig_path.exists():
                msg = f"Signature file not found: {data.signature}"
                raise FileNotFoundError(msg)
        # Relativer Pfad → im Brief-Verzeichnis suchen
        elif not (letter_dir / data.signature).exists():
            msg = f"Signature file not found: {data.signature}"
            raise FileNotFoundError(msg)
        else:
            data.signature = str(letter_dir / data.signature)


def compile_letter(
    letter_path: Path,
    *,
    keep_typ: bool = False,
    auto_rename: bool = True,
) -> tuple[Path, LetterData]:
    """Full compile pipeline: Parse -> Validate -> Convert -> Compile -> Rename.

    Returns (path_to_pdf, letter_data).

    Raises:
        FileNotFoundError: File not found.
        FontError: Required fonts missing.
        ToolNotFoundError: External tool not found.
        FrontmatterError: Invalid frontmatter.
        CompileError: Typst compilation failed.
        ValueError: Wrong file extension.
    """
    if not letter_path.exists():
        msg = f"File not found: {letter_path}"
        raise FileNotFoundError(msg)

    if letter_path.suffix != ".md":
        msg = f"Expected a .md file, got '{letter_path.suffix}'"
        raise ValueError(msg)

    # Font check
    missing = check_fonts(fonts_dir())
    if missing:
        msg = f"Missing fonts: {', '.join(missing)}"
        raise FontError(msg)

    # Tool check
    _check_tool("typst")
    _check_tool("pandoc")

    # Parse
    fm, body = parse_letter(letter_path)

    # Validate
    try:
        data = LetterData.model_validate(fm)
    except ValidationError as e:
        errors = "; ".join(
            f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in e.errors()
        )
        msg = f"Validation failed: {errors}"
        raise FrontmatterError(msg) from None

    # Signature
    _resolve_signature(data, letter_path.parent)

    # Copy signature into letter dir so Typst can read() it
    sig_copy: Path | None = None
    if isinstance(data.signature, str):
        sig_src = Path(data.signature)
        if sig_src.is_absolute() and sig_src.parent != letter_path.parent:
            sig_copy = letter_path.parent / sig_src.name
            shutil.copy2(str(sig_src), str(sig_copy))
            data.signature = sig_src.name

    # Convert body
    typst_body = md_to_typst(body)

    # Build files
    typ_content, json_content = build_typst_files(data=data, body=typst_body)

    typ_path = letter_path.with_suffix(".typ")
    json_path = letter_path.with_name("brief.json")
    pdf_path = letter_path.with_suffix(".pdf")

    try:
        typ_path.write_text(typ_content, encoding="utf-8")
        json_path.write_text(json_content, encoding="utf-8")

        # Compile
        typst_cmd = ["typst", "compile", "--pdf-standard", "a-2b"]
        fdir = fonts_dir()
        if fdir.exists():
            typst_cmd.extend(["--font-path", str(fdir)])
        typst_cmd.extend([str(typ_path), str(pdf_path)])

        result = subprocess.run(
            typst_cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            msg = f"typst compile failed:\n{result.stderr}"
            raise CompileError(msg)

        # Auto-rename
        if auto_rename:
            final_name = _build_filename(data)
            if final_name and pdf_path.exists():
                try:
                    final_md = letter_path.parent / f"{final_name}.md"
                    final_pdf = letter_path.parent / f"{final_name}.pdf"
                    if final_md != letter_path:
                        letter_path.rename(final_md)
                    pdf_path.rename(final_pdf)
                    pdf_path = final_pdf
                    if keep_typ and typ_path.exists():
                        final_typ = letter_path.parent / f"{final_name}.typ"
                        typ_path.rename(final_typ)
                        typ_path = final_typ
                except OSError:
                    pass

        return pdf_path, data

    finally:
        if not keep_typ and typ_path.exists():
            typ_path.unlink()
        if json_path.exists():
            json_path.unlink()
        if sig_copy and sig_copy.exists():
            sig_copy.unlink()
