import platform
from pathlib import Path

PACKAGE_NAME = "din5008a"
FALLBACK_VERSION = "0.1.1"


def _find_installed_version() -> str:
    """Find the latest installed version of din5008a."""
    system = platform.system()
    if system == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "typst" / "packages" / "local"
    elif system == "Linux":
        base = Path.home() / ".local" / "share" / "typst" / "packages" / "local"
    else:
        base = Path.home() / "AppData" / "Roaming" / "typst" / "packages" / "local"

    pkg_dir = base / PACKAGE_NAME
    if not pkg_dir.exists():
        return FALLBACK_VERSION

    versions = sorted(
        (d.name for d in pkg_dir.iterdir() if d.is_dir()),
        reverse=True,
    )
    return versions[0] if versions else FALLBACK_VERSION


def build_typst(
    *,
    sender: dict[str, object],
    recipient: list[str],
    date: str,
    subject: str,
    body: str,
    closing: str,
    signature: str | None,
) -> str:
    """Generate a complete .typ file for din5008a."""
    version = _find_installed_version()
    qr = "true" if sender.get("qr_code") else "false"
    city_combined = f"{sender['zip']} {sender['city']}".strip()
    recipient_str = ", ".join(f'"{line}"' for line in recipient)

    typ = f'''#import "@local/din5008a:{version}": din5008a, bullet

#show: din5008a.with(
  sender: (
    name: "{sender["name"]}",
    street: "{sender["street"]}",
    city: "{city_combined}",
    phone: "{sender["phone"]}",
    email: "{sender["email"]}",
    iban: "{sender["iban"]}",
    bic: "{sender["bic"]}",
    bank: "{sender["bank"]}",
    qr: {qr},
  ),
  recipient: ({recipient_str}),
  date: "{date}",
  subject: "{subject}",
)

{body}

{closing}

'''

    if signature:
        typ += f'#image("{signature}", width: 40mm)\n\n'

    typ += f"{sender['name']}\n"

    return typ
