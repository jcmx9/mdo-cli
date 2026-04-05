import re


def md_to_typst(text: str) -> str:
    """Convert Markdown text to Typst markup."""
    if not text:
        return ""

    lines = text.split("\n")
    result: list[str] = []
    in_code_block = False

    for line in lines:
        if line.startswith("```"):
            in_code_block = not in_code_block
            result.append(line)
            continue

        if in_code_block:
            result.append(line)
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            result.append("=" * level + " " + heading_match.group(2))
            continue

        ordered_match = re.match(r"^\d+\.\s+(.+)$", line)
        if ordered_match:
            result.append("+ " + ordered_match.group(1))
            continue

        line = _convert_inline(line)
        result.append(line)

    return "\n".join(result)


def _convert_inline(line: str) -> str:
    """Convert bold and italic markers, preserving inline code."""
    parts = re.split(r"(`[^`]+`)", line)
    converted: list[str] = []
    for part in parts:
        if part.startswith("`") and part.endswith("`"):
            converted.append(part)
        else:
            # Bold first: **text** → placeholder to protect from italic regex
            bold_spans: list[str] = []

            def _bold_repl(m: re.Match[str]) -> str:
                bold_spans.append(m.group(1))
                return f"\x00BOLD{len(bold_spans) - 1}\x00"

            part = re.sub(r"\*\*(.+?)\*\*", _bold_repl, part)
            # Italic: *text* → _text_
            part = re.sub(r"\*(.+?)\*", r"_\1_", part)
            # Restore bold: placeholder → *text*
            for i, span in enumerate(bold_spans):
                part = part.replace(f"\x00BOLD{i}\x00", f"*{span}*")
            converted.append(part)
    return "".join(converted)
