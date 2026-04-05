from mdo.core.markdown import md_to_typst


def test_bold() -> None:
    assert md_to_typst("This is **bold** text") == "This is *bold* text"


def test_italic_asterisk() -> None:
    assert md_to_typst("This is *italic* text") == "This is _italic_ text"


def test_italic_underscore() -> None:
    assert md_to_typst("This is _italic_ text") == "This is _italic_ text"


def test_bold_and_italic() -> None:
    result = md_to_typst("**bold** and *italic*")
    assert result == "*bold* and _italic_"


def test_heading_levels() -> None:
    assert md_to_typst("# Heading 1") == "= Heading 1"
    assert md_to_typst("## Heading 2") == "== Heading 2"
    assert md_to_typst("### Heading 3") == "=== Heading 3"


def test_unordered_list_unchanged() -> None:
    text = "- Item 1\n- Item 2"
    assert md_to_typst(text) == "- Item 1\n- Item 2"


def test_ordered_list_maps_to_plus() -> None:
    text = "1. First\n2. Second"
    assert md_to_typst(text) == "+ First\n+ Second"


def test_code_block_preserved() -> None:
    text = "before\n```python\nx = **not bold**\n```\nafter"
    result = md_to_typst(text)
    assert "**not bold**" in result
    assert "```python" in result


def test_inline_code_preserved() -> None:
    text = "Use `**raw**` here"
    result = md_to_typst(text)
    assert "`**raw**`" in result


def test_empty_input() -> None:
    assert md_to_typst("") == ""


def test_plain_text_unchanged() -> None:
    text = "Just a normal paragraph.\n\nAnother one."
    assert md_to_typst(text) == text
