import subprocess
from unittest.mock import patch

import pytest

from mdo.core.markdown import md_to_typst


def test_bold() -> None:
    assert "#strong[bold]" in md_to_typst("This is **bold** text")


def test_italic_asterisk() -> None:
    assert "#emph[italic]" in md_to_typst("This is *italic* text")


def test_heading() -> None:
    result = md_to_typst("# Heading 1")
    assert "= Heading 1" in result


def test_ordered_list() -> None:
    result = md_to_typst("1. First\n2. Second")
    assert "+ First" in result
    assert "+ Second" in result


def test_unordered_list() -> None:
    result = md_to_typst("- Item 1\n- Item 2")
    assert "- Item 1" in result
    assert "- Item 2" in result


def test_empty_input() -> None:
    assert md_to_typst("") == ""


def test_plain_text() -> None:
    result = md_to_typst("Just a normal paragraph.")
    assert "Just a normal paragraph." in result


def test_pandoc_not_found() -> None:
    with (
        patch("mdo.core.markdown.subprocess.run", side_effect=FileNotFoundError),
        pytest.raises(RuntimeError, match="pandoc not found"),
    ):
        md_to_typst("text")


def test_pandoc_error() -> None:
    error = subprocess.CalledProcessError(1, "pandoc", stderr="bad input")
    with (
        patch("mdo.core.markdown.subprocess.run", side_effect=error),
        pytest.raises(RuntimeError, match="pandoc conversion failed"),
    ):
        md_to_typst("text")
