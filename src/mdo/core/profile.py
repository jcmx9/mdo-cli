"""Multi-profile management for mdo."""

import logging
import shutil
from pathlib import Path

import yaml

from mdo.core.models import ProfileConfig
from mdo.core.paths import profiles_dir

logger = logging.getLogger(__name__)

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
    "signature": "Unterschrift-Datei automatisch suchen",
    "signature_width": "Unterschrift-Breite in mm (null = Template-Standard 30pt)",
    "closing": "Schlussgruss",
    "open": "PDF nach Kompilierung oeffnen",
    "reveal": "PDF im Dateimanager anzeigen",
}

SIGNATURE_EXTENSIONS = ("svg", "png", "jpg", "gif")


def _format_value(value: object) -> str:
    """Format a value for YAML without yaml.dump quoting."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        if not value:
            return '""'
        if value.startswith("#"):
            return f'"{value}"'
    return str(value)


def _serialize_profile(data: dict[str, object]) -> str:
    """Serialize profile data as YAML with inline comments."""
    lines: list[str] = []
    for key, value in data.items():
        formatted = _format_value(value)
        comment = FIELD_COMMENTS.get(key, "")
        if comment:
            lines.append(f"{key}: {formatted}  # {comment}")
        else:
            lines.append(f"{key}: {formatted}")
    return "\n".join(lines) + "\n"


def profile_dir(name: str = "default") -> Path:
    """Return the directory for a specific profile."""
    return profiles_dir() / name


def save_profile(config: ProfileConfig, name: str = "default") -> Path:
    """Save a profile to ~/.mdo/profiles/{name}/profile.yaml."""
    target = profile_dir(name)
    target.mkdir(parents=True, exist_ok=True)
    path = target / "profile.yaml"
    data = config.model_dump()
    path.write_text(_serialize_profile(data), encoding="utf-8")
    logger.debug("Profile saved to %s", path)
    return path


def load_profile(name: str = "default") -> ProfileConfig:
    """Load a profile from ~/.mdo/profiles/{name}/profile.yaml."""
    path = profile_dir(name) / "profile.yaml"
    if not path.exists():
        # Fallback: altes Format (profiles/{name}.yaml direkt)
        legacy = profiles_dir() / f"{name}.yaml"
        if legacy.exists():
            path = legacy
        else:
            msg = f"Profile not found: {path}"
            raise FileNotFoundError(msg)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ProfileConfig.model_validate(data)


def list_profiles() -> list[str]:
    """Return all available profile names."""
    target_dir = profiles_dir()
    if not target_dir.exists():
        return []
    names: list[str] = []
    for p in sorted(target_dir.iterdir()):
        if p.is_dir() and (p / "profile.yaml").exists():
            names.append(p.name)
        elif p.is_file() and p.suffix == ".yaml":
            # Legacy: flache YAML-Datei
            names.append(p.stem)
    return names


def delete_profile(name: str) -> None:
    """Delete a profile directory."""
    target = profile_dir(name)
    if not target.is_dir():
        legacy = profiles_dir() / f"{name}.yaml"
        if not legacy.exists():
            msg = f"Profile not found: {name}"
            raise FileNotFoundError(msg)
        legacy.unlink()
        logger.debug("Profile deleted: %s", name)
        return
    remaining = list_profiles()
    if len(remaining) <= 1:
        msg = "Cannot delete the last profile"
        raise ValueError(msg)
    shutil.rmtree(target)
    logger.debug("Profile deleted: %s", name)


def save_signature(source: Path, name: str = "default") -> Path:
    """Copy a signature file into the profile directory.

    Renames to unterschrift_{name}.ext.
    """
    if not source.exists():
        msg = f"File not found: {source}"
        raise FileNotFoundError(msg)
    target = profile_dir(name)
    target.mkdir(parents=True, exist_ok=True)
    ext = source.suffix.lower()
    dest = target / f"unterschrift_{name}{ext}"
    shutil.copy2(str(source), str(dest))
    logger.debug("Signature saved to %s", dest)
    return dest


def find_signature(name: str = "default") -> Path | None:
    """Find the signature file for a profile."""
    target = profile_dir(name)
    for ext in SIGNATURE_EXTENSIONS:
        for candidate in target.glob(f"unterschrift*.{ext}"):
            return candidate
    return None
