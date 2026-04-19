"""Multi-profile management for mdo."""

import logging
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
    "signature": "Unterschrift-Datei automatisch suchen (unterschrift.svg/png/jpg/gif)",
    "signature_width": "Unterschrift-Breite in mm (null = Template-Standard 30pt)",
    "closing": "Schlussgruss",
    "open": "PDF nach Kompilierung oeffnen",
    "reveal": "PDF im Dateimanager anzeigen",
}


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


def save_profile(config: ProfileConfig, name: str = "default") -> Path:
    """Save a profile to ~/.mdo/profiles/{name}.yaml."""
    target_dir = profiles_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{name}.yaml"
    data = config.model_dump()
    path.write_text(_serialize_profile(data), encoding="utf-8")
    logger.debug("Profile saved to %s", path)
    return path


def load_profile(name: str = "default") -> ProfileConfig:
    """Load a profile from ~/.mdo/profiles/{name}.yaml."""
    path = profiles_dir() / f"{name}.yaml"
    if not path.exists():
        msg = f"Profile not found: {path}"
        raise FileNotFoundError(msg)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ProfileConfig.model_validate(data)


def list_profiles() -> list[str]:
    """Return all available profile names."""
    target_dir = profiles_dir()
    if not target_dir.exists():
        return []
    return sorted(p.stem for p in target_dir.glob("*.yaml"))


def delete_profile(name: str) -> None:
    """Delete a profile. Cannot delete 'default'."""
    if name == "default":
        msg = "Cannot delete the default profile"
        raise ValueError(msg)
    path = profiles_dir() / f"{name}.yaml"
    if not path.exists():
        msg = f"Profile not found: {path}"
        raise FileNotFoundError(msg)
    path.unlink()
    logger.debug("Profile deleted: %s", path)
