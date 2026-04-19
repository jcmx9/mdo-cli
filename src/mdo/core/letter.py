"""Letter CRUD operations for the Flutter app."""

import datetime
import logging
from pathlib import Path

import yaml

from mdo.core.paths import letters_dir

logger = logging.getLogger(__name__)


def _build_frontmatter(data: dict[str, object]) -> str:
    """Serialize frontmatter dict to YAML string between --- markers."""
    lines: list[str] = ["---"]
    for key, value in data.items():
        if value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif isinstance(value, str) and value.startswith("#"):
            lines.append(f'{key}: "{value}"')
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def save_letter(
    frontmatter: dict[str, object],
    body: str,
    filename: str | None = None,
) -> Path:
    """Save a letter as .md file to ~/.mdo/letters/."""
    target_dir = letters_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        today = datetime.date.today().isoformat()
        counter = 1
        while True:
            filename = f"{today}_Brief{counter:02d}.md"
            if not (target_dir / filename).exists():
                break
            counter += 1

    path = target_dir / filename
    fm_text = _build_frontmatter(frontmatter)
    content = f"{fm_text}\n\n{body}\n"
    path.write_text(content, encoding="utf-8")
    logger.debug("Letter saved to %s", path)
    return path


def load_letter(filename: str) -> tuple[dict[str, object], str]:
    """Load a letter from ~/.mdo/letters/. Returns (frontmatter, body)."""
    path = letters_dir() / filename
    if not path.exists():
        msg = f"Letter not found: {path}"
        raise FileNotFoundError(msg)

    content = path.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) < 3:
        msg = f"Invalid frontmatter in {filename}"
        raise ValueError(msg)

    fm: dict[str, object] = yaml.safe_load(parts[1])
    body = parts[2].strip()
    return fm, body


def list_letters() -> list[str]:
    """Return all letter filenames in ~/.mdo/letters/."""
    target_dir = letters_dir()
    if not target_dir.exists():
        return []
    return sorted(p.name for p in target_dir.glob("*.md"))


def delete_letter(filename: str) -> None:
    """Delete a letter from ~/.mdo/letters/."""
    path = letters_dir() / filename
    if not path.exists():
        msg = f"Letter not found: {path}"
        raise FileNotFoundError(msg)
    path.unlink()
    logger.debug("Letter deleted: %s", path)
