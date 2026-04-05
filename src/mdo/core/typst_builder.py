from mdo.core.paths import find_installed_version


def _esc(value: object) -> str:
    """Escape a value for use inside a Typst string literal."""
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


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
    version = find_installed_version()
    qr = "true" if sender.get("qr_code") else "false"
    city_combined = f"{sender['zip']} {sender['city']}".strip()
    recipient_str = ", ".join(f'"{_esc(line)}"' for line in recipient)

    typ = f'''#import "@local/din5008a:{version}": din5008a, bullet

#show: din5008a.with(
  sender: (
    name: "{_esc(sender["name"])}",
    street: "{_esc(sender["street"])}",
    city: "{_esc(city_combined)}",
    phone: "{_esc(sender["phone"])}",
    email: "{_esc(sender["email"])}",
    iban: "{_esc(sender["iban"])}",
    bic: "{_esc(sender["bic"])}",
    bank: "{_esc(sender["bank"])}",
    qr: {qr},
  ),
  recipient: ({recipient_str}),
  date: "{_esc(date)}",
  subject: "{_esc(subject)}",
)

{body}

{closing}

'''

    if signature:
        typ += f'#image("{_esc(signature)}", width: 40mm)\n\n'

    typ += f"{sender['name']}\n"

    return typ
