import subprocess

REQUIRED_FONTS = ["Source Serif 4", "Source Sans 3", "Source Code Pro"]

FONT_HELP_URL = "https://github.com/jcmx9/typst-DIN5008a#requirements"


def check_fonts() -> list[str]:
    """Return list of missing required font families."""
    try:
        result = subprocess.run(
            ["fc-list", "--format", "%{family}\n"],
            capture_output=True,
            text=True,
            check=False,
        )
        installed = result.stdout
    except FileNotFoundError:
        return list(REQUIRED_FONTS)

    missing: list[str] = []
    for font in REQUIRED_FONTS:
        if font not in installed:
            missing.append(font)
    return missing
