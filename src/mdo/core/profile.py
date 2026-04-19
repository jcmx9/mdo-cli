"""Multi-profile management for mdo."""

import logging
from pathlib import Path

import yaml

from mdo.core.models import ProfileConfig
from mdo.core.paths import profiles_dir

logger = logging.getLogger(__name__)


def save_profile(config: ProfileConfig, name: str = "default") -> Path:
    """Save a profile to ~/.mdo/profiles/{name}.yaml."""
    target_dir = profiles_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{name}.yaml"
    data = config.model_dump()
    path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
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
