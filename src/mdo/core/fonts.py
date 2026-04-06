import subprocess
from pathlib import Path

REQUIRED_FONTS = ["Source Serif 4", "Source Sans 3", "Source Code Pro"]

FONT_HELP_URL = "https://github.com/jcmx9/typst-DIN5008a#requirements"


def check_fonts(mdo_fonts_path: Path | None = None) -> list[str]:
    """Return list of missing required font families.

    If mdo_fonts_path exists and contains .otf files, assume fonts are installed there.
    """
    if mdo_fonts_path and mdo_fonts_path.exists():
        otf_files = list(mdo_fonts_path.glob("*.otf"))
        if otf_files:
            return []

    try:
        result = subprocess.run(
            ["fc-list", "--format", "%{family}\n"],
            capture_output=True,
            text=True,
            check=False,
        )
        installed: set[str] = set()
        for line in result.stdout.splitlines():
            for family in line.split(","):
                installed.add(family.strip())
    except FileNotFoundError:
        return list(REQUIRED_FONTS)

    return [font for font in REQUIRED_FONTS if font not in installed]
