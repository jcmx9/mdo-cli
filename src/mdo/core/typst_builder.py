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
    qr = "true" if sender.get("qr_code") else "false"
    city_combined = f"{sender['zip']} {sender['city']}".strip()
    recipient_str = ", ".join(f'"{line}"' for line in recipient)

    typ = f'''#import "@local/din5008a:0.1.1": din5008a, bullet

#show: din5008a.with(
  sender: (
    name: "{sender['name']}",
    street: "{sender['street']}",
    city: "{city_combined}",
    phone: "{sender['phone']}",
    email: "{sender['email']}",
    iban: "{sender['iban']}",
    bic: "{sender['bic']}",
    bank: "{sender['bank']}",
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
