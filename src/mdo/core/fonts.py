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
        # Split into individual family names for exact matching
        # fc-list can return comma-separated families per line
        installed: set[str] = set()
        for line in result.stdout.splitlines():
            for family in line.split(","):
                installed.add(family.strip())
    except FileNotFoundError:
        return list(REQUIRED_FONTS)

    return [font for font in REQUIRED_FONTS if font not in installed]
