from pathlib import Path
from unittest.mock import patch

import yaml
from typer.testing import CliRunner

from mdo.cli import app

runner = CliRunner()


@patch("mdo.core.profile.profiles_dir")
def test_profile_create_with_defaults(mock_dir: object, tmp_path: Path) -> None:
    profiles_path = tmp_path / "profiles"
    profiles_path.mkdir()
    mock_dir.return_value = profiles_path  # type: ignore[union-attr]
    result = runner.invoke(app, ["profile", "create"], input="\n" * 14)
    assert result.exit_code == 0
    p = profiles_path / "default" / "profile.yaml"
    assert p.exists()
    data = yaml.safe_load(p.read_text())
    assert data["name"] == "Max Mustermann"
    assert data["qr_code"] is True
    assert data["signature"] is True
    assert data["closing"] == "Mit freundlichem Gruß"
    assert data["accent"] is None
    assert "street" in data
    assert "zip" in data
    assert "city" in data
    assert "phone" in data
    assert "email" in data
    assert "iban" in data
    assert "bic" in data
    assert "bank" in data


@patch("mdo.core.profile.profiles_dir")
def test_profile_create_with_custom_values(mock_dir: object, tmp_path: Path) -> None:
    profiles_path = tmp_path / "profiles"
    profiles_path.mkdir()
    mock_dir.return_value = profiles_path  # type: ignore[union-attr]
    inputs = (
        "Anna Weber\nLindenallee 12\n80331\nMuenchen\n089 123\n"
        "anna@example.de\nDE91 1234\nBFSWDE33\nTestbank\n#265282\n"
        "null\nja\nja\nMit herzlichen Gruessen\n"
    )
    result = runner.invoke(app, ["profile", "create"], input=inputs)
    assert result.exit_code == 0
    data = yaml.safe_load((profiles_path / "default" / "profile.yaml").read_text())
    assert data["name"] == "Anna Weber"
    assert data["city"] == "Muenchen"


@patch("mdo.core.profile.profiles_dir")
def test_profile_create_named(mock_dir: object, tmp_path: Path) -> None:
    profiles_path = tmp_path / "profiles"
    profiles_path.mkdir()
    mock_dir.return_value = profiles_path  # type: ignore[union-attr]
    result = runner.invoke(app, ["profile", "create", "--name", "work"], input="\n" * 14)
    assert result.exit_code == 0
    assert (profiles_path / "work" / "profile.yaml").exists()


@patch("mdo.core.profile.profiles_dir")
def test_profile_no_quotes_on_zip(mock_dir: object, tmp_path: Path) -> None:
    profiles_path = tmp_path / "profiles"
    profiles_path.mkdir()
    mock_dir.return_value = profiles_path  # type: ignore[union-attr]
    result = runner.invoke(app, ["profile", "create"], input="\n" * 14)
    assert result.exit_code == 0
    raw = (profiles_path / "default" / "profile.yaml").read_text()
    assert "zip: 12345" in raw
    assert "'12345'" not in raw
    assert '"12345"' not in raw


@patch("mdo.core.profile.profiles_dir")
def test_profile_list_empty(mock_dir: object, tmp_path: Path) -> None:
    profiles_path = tmp_path / "profiles"
    profiles_path.mkdir()
    mock_dir.return_value = profiles_path  # type: ignore[union-attr]
    result = runner.invoke(app, ["profile", "list"])
    assert result.exit_code == 0
    assert "Keine Profile" in result.output


@patch("mdo.core.profile.profiles_dir")
def test_profile_list_shows_profiles(mock_dir: object, tmp_path: Path) -> None:
    profiles_path = tmp_path / "profiles"
    profiles_path.mkdir()
    mock_dir.return_value = profiles_path  # type: ignore[union-attr]
    (profiles_path / "default").mkdir()
    (profiles_path / "default" / "profile.yaml").write_text("name: Test\n")
    (profiles_path / "work").mkdir()
    (profiles_path / "work" / "profile.yaml").write_text("name: Work\n")
    result = runner.invoke(app, ["profile", "list"])
    assert result.exit_code == 0
    assert "default" in result.output
    assert "work" in result.output


@patch("mdo.core.profile.profiles_dir")
def test_profile_delete(mock_dir: object, tmp_path: Path) -> None:
    profiles_path = tmp_path / "profiles"
    profiles_path.mkdir()
    mock_dir.return_value = profiles_path  # type: ignore[union-attr]
    (profiles_path / "temp").mkdir()
    (profiles_path / "temp" / "profile.yaml").write_text("name: Temp\n")
    result = runner.invoke(app, ["profile", "delete", "temp"])
    assert result.exit_code == 0
    assert not (profiles_path / "temp").exists()
    assert not (profiles_path / "temp" / "profile.yaml").exists()


@patch("mdo.core.profile.profiles_dir")
def test_profile_delete_default_fails(mock_dir: object, tmp_path: Path) -> None:
    profiles_path = tmp_path / "profiles"
    profiles_path.mkdir()
    mock_dir.return_value = profiles_path  # type: ignore[union-attr]
    (profiles_path / "default").mkdir()
    (profiles_path / "default" / "profile.yaml").write_text("name: Default\n")
    result = runner.invoke(app, ["profile", "delete", "default"])
    assert result.exit_code != 0
