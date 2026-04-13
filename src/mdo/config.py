"""Central Pydantic configuration model for profile.yaml."""

import re

from pydantic import BaseModel, field_validator


class ProfileConfig(BaseModel):
    """Validated sender profile from profile.yaml."""

    name: str
    street: str
    zip: str
    city: str
    phone: str = ""
    email: str = ""
    iban: str = ""
    bic: str = ""
    bank: str = ""
    accent: str | None = None
    signature_width: int | None = None
    qr_code: bool = False
    signature: bool = True
    closing: str = "Mit freundlichem Gruß"
    open: bool = True
    reveal: bool = True

    @field_validator("zip", mode="before")
    @classmethod
    def coerce_zip(cls, v: object) -> str:
        """YAML parses bare numbers like 12345 as int."""
        return str(v)

    @field_validator("accent")
    @classmethod
    def valid_hex_color(cls, v: str | None) -> str | None:
        """Validate accent as hex color or None."""
        if v is None:
            return None
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            msg = f"accent must be a hex color like #B03060, got '{v}'"
            raise ValueError(msg)
        return v
