import datetime
import re

from pydantic import BaseModel, field_validator

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


def format_german_date(d: datetime.date) -> str:
    """Format date as '05. April 2026'."""
    return f"{d.day:02d}. {GERMAN_MONTHS[d.month - 1]} {d.year}"


class LetterData(BaseModel):
    """Validated letter data from YAML frontmatter."""

    # Sender
    name: str
    street: str
    zip: str
    city: str
    phone: str = ""
    email: str = ""
    iban: str = ""
    bic: str = ""
    bank: str = ""
    qr_code: bool = False
    signature: str | bool | None = None
    signature_width: int | None = None
    closing: str = "Mit freundlichem Gruß"

    # Letter
    date: str | None = None
    subject: str = ""
    recipient: list[str]
    accent: str | None = None
    attachments: list[str] = []

    # Compile options
    open: bool = False
    reveal: bool = False

    @field_validator("zip", mode="before")
    @classmethod
    def coerce_zip(cls, v: object) -> str:
        """YAML parses bare numbers like 12345 as int."""
        return str(v)

    @field_validator("date", mode="before")
    @classmethod
    def coerce_date(cls, v: object) -> str | None:
        """Convert None to today, datetime.date to German format."""
        if v is None:
            return format_german_date(datetime.date.today())
        if isinstance(v, datetime.date):
            return format_german_date(v)
        return str(v)

    @field_validator("recipient")
    @classmethod
    def recipient_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            msg = "recipient must have at least one address line"
            raise ValueError(msg)
        return v

    @field_validator("accent")
    @classmethod
    def valid_hex_color(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            msg = f"accent must be a hex color like #B03060, got '{v}'"
            raise ValueError(msg)
        return v

    def sender_dict(self) -> dict[str, object]:
        """Return sender fields as dict for JSON export."""
        return {
            "name": self.name,
            "street": self.street,
            "city": f"{self.zip} {self.city}".strip(),
            "phone": self.phone,
            "email": self.email,
            "iban": self.iban,
            "bic": self.bic,
            "bank": self.bank,
            "qr": self.qr_code,
        }
