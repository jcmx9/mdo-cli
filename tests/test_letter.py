from pathlib import Path
from unittest.mock import patch

import pytest

from mdo.core.letter import delete_letter, list_letters, load_letter, save_letter


@pytest.fixture
def letters_path(tmp_path: Path) -> Path:
    d = tmp_path / ".mdo" / "letters"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def _mock_letters_dir(letters_path: Path):  # type: ignore[no-untyped-def]
    with patch("mdo.core.letter.letters_dir", return_value=letters_path):
        yield


SAMPLE_FM: dict[str, object] = {
    "name": "Max Mustermann",
    "street": "Musterstrasse 1",
    "zip": "12345",
    "city": "Musterstadt",
    "phone": "",
    "email": "",
    "iban": "",
    "bic": "",
    "bank": "",
    "qr_code": True,
    "signature": True,
    "closing": "Mit freundlichem Gruß",
    "date": None,
    "subject": "Testbetreff",
    "recipient": ["Firma GmbH", "Strasse 1", "12345 Stadt"],
    "attachments": [],
}

SAMPLE_BODY = "Sehr geehrte Damen und Herren,\n\ndies ist ein Test."


@pytest.mark.usefixtures("_mock_letters_dir")
class TestSaveLetter:
    def test_save_creates_file(self, letters_path: Path) -> None:
        path = save_letter(SAMPLE_FM, SAMPLE_BODY)
        assert path.exists()
        assert path.suffix == ".md"
        content = path.read_text()
        assert "---" in content
        assert "Testbetreff" in content
        assert "dies ist ein Test" in content

    def test_save_with_filename(self, letters_path: Path) -> None:
        path = save_letter(SAMPLE_FM, SAMPLE_BODY, filename="mein_brief.md")
        assert path.name == "mein_brief.md"

    def test_save_overwrites(self, letters_path: Path) -> None:
        save_letter(SAMPLE_FM, SAMPLE_BODY, filename="brief.md")
        path = save_letter({**SAMPLE_FM, "subject": "Neu"}, "Neuer Text.", filename="brief.md")
        assert "Neu" in path.read_text()


@pytest.mark.usefixtures("_mock_letters_dir")
class TestLoadLetter:
    def test_load_existing(self, letters_path: Path) -> None:
        save_letter(SAMPLE_FM, SAMPLE_BODY, filename="test.md")
        fm, body = load_letter("test.md")
        assert fm["subject"] == "Testbetreff"
        assert "dies ist ein Test" in body

    def test_load_nonexistent(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_letter("nope.md")


@pytest.mark.usefixtures("_mock_letters_dir")
class TestListLetters:
    def test_empty(self) -> None:
        assert list_letters() == []

    def test_returns_md(self, letters_path: Path) -> None:
        save_letter(SAMPLE_FM, SAMPLE_BODY, filename="a.md")
        save_letter(SAMPLE_FM, SAMPLE_BODY, filename="b.md")
        assert sorted(list_letters()) == ["a.md", "b.md"]

    def test_ignores_non_md(self, letters_path: Path) -> None:
        (letters_path / "notes.txt").write_text("not a letter")
        assert list_letters() == []


@pytest.mark.usefixtures("_mock_letters_dir")
class TestDeleteLetter:
    def test_delete_existing(self, letters_path: Path) -> None:
        save_letter(SAMPLE_FM, SAMPLE_BODY, filename="temp.md")
        delete_letter("temp.md")
        assert not (letters_path / "temp.md").exists()

    def test_delete_nonexistent(self) -> None:
        with pytest.raises(FileNotFoundError):
            delete_letter("nope.md")
