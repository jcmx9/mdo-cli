from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from mdo.cli import app

runner = CliRunner()


@patch("mdo.commands.update.typst_packages_dir")
@patch("mdo.commands.update.subprocess.run")
def test_update_installs_template(mock_run: MagicMock, mock_dir: MagicMock, tmp_path: Path) -> None:
    # Set up fake packages dir
    mock_dir.return_value = tmp_path / "packages"

    # Set up fake repo clone
    def fake_clone(cmd: list[str], **kwargs: object) -> MagicMock:
        repo_dir = Path(cmd[-1])
        repo_dir.mkdir(parents=True)
        src_dir = repo_dir / "src"
        src_dir.mkdir()
        (src_dir / "lib.typ").write_text("// template")
        (repo_dir / "typst.toml").write_text('[package]\nversion = "0.2.0"\n')
        (repo_dir / "version.typ").write_text('#let version = "0.2.0"')
        (repo_dir / ".git").mkdir()  # excluded from copy
        result = MagicMock()
        result.returncode = 0
        return result

    mock_run.side_effect = fake_clone

    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0
    assert "0.2.0" in result.output

    installed = tmp_path / "packages" / "din5008a" / "0.2.0"
    assert (installed / "src" / "lib.typ").exists()
    assert (installed / "typst.toml").exists()
    assert (installed / "version.typ").exists()
    assert not (installed / ".git").exists()


@patch("mdo.commands.update.subprocess.run", side_effect=FileNotFoundError)
def test_update_git_not_found(mock_run: MagicMock) -> None:
    result = runner.invoke(app, ["update"])
    assert result.exit_code != 0
    assert "git" in result.output.lower()
