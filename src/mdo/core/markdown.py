import subprocess


def md_to_typst(text: str) -> str:
    """Convert Markdown text to Typst markup via Pandoc."""
    if not text:
        return ""

    try:
        result = subprocess.run(
            ["pandoc", "-f", "markdown", "-t", "typst"],
            input=text,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        msg = "pandoc not found. Install: https://pandoc.org"
        raise RuntimeError(msg) from None
    except subprocess.CalledProcessError as e:
        msg = f"pandoc conversion failed:\n{e.stderr}"
        raise RuntimeError(msg) from None

    return result.stdout.rstrip("\n")
