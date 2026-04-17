import json

from mdo.core.models import LetterData
from mdo.core.paths import find_installed_version


def build_typst_files(*, data: LetterData, body: str) -> tuple[str, str]:
    """Generate .typ content and .json content for a letter.

    Returns:
        (typ_content, json_content) tuple.
    """
    version = find_installed_version()

    json_data: dict[str, object] = {
        "sender": data.sender_dict(),
        "recipient": data.recipient,
        "date": data.date,
        "subject": data.subject,
        "closing": data.closing,
        "signature": data.signature,
        "signature_width": data.signature_width,
        "accent": data.accent,
        "attachments": data.attachments,
    }
    json_content = json.dumps(json_data, ensure_ascii=False, indent=2)

    accent_line = "\n  accent: rgb(data.accent)," if data.accent else ""

    typ_content = f"""\
#import "@local/din5008a:{version}": din5008a, bullet
#let data = json("brief.json")
#let sig = if data.signature != none {{ read(data.signature) }} else {{ none }}
#let sig-width = if data.at("signature_width", default: none) != none {{
  data.signature_width * 1mm
}} else {{ none }}

#show: din5008a.with(
  sender: data.sender,
  recipient: data.recipient,
  date: data.date,
  subject: data.subject,
  closing: data.closing,
  signature: sig,
  signature-width: sig-width,{accent_line}
  attachments: data.at("attachments", default: ()),
)

{body}
"""

    return typ_content, json_content
