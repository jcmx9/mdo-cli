import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from mdo.core.template import get_installed_version, install_template_git, install_template_http


@patch("mdo.core.template.typst_packages_dir")
@patch("mdo.core.template.subprocess.run")
def test_install_git(mock_run: MagicMock, mock_dir: MagicMock, tmp_path: Path) -> None:
    mock_dir.return_value = tmp_path / "packages"

    def fake_clone(cmd: list[str], **kwargs: object) -> MagicMock:
        repo_dir = Path(cmd[-1])
        repo_dir.mkdir(parents=True)
        src_dir = repo_dir / "src"
        src_dir.mkdir()
        (src_dir / "lib.typ").write_text("// template")
        (repo_dir / "typst.toml").write_text('[package]\nversion = "0.3.0"\n')
        (repo_dir / ".git").mkdir()
        result = MagicMock()
        result.returncode = 0
        return result

    mock_run.side_effect = fake_clone
    path = install_template_git()
    assert "0.3.0" in str(path)
    assert (path / "src" / "lib.typ").exists()
    assert not (path / ".git").exists()


@patch("mdo.core.template.typst_packages_dir")
@patch("mdo.core.template.subprocess.run")
def test_install_http(mock_run: MagicMock, mock_dir: MagicMock, tmp_path: Path) -> None:
    mock_dir.return_value = tmp_path / "packages"

    def fake_curl(cmd: list[str], **kwargs: object) -> MagicMock:
        result = MagicMock()
        result.returncode = 0
        if "api.github.com" in str(cmd):
            result.stdout = json.dumps(
                {
                    "tag_name": "v0.3.0",
                    "zipball_url": "https://github.com/fake/archive/v0.3.0.zip",
                }
            )
        elif "-o" in cmd:
            import io
            import zipfile

            zip_path = Path(cmd[cmd.index("-o") + 1])
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                zf.writestr("repo-abc123/typst.toml", '[package]\nversion = "0.3.0"\n')
                zf.writestr("repo-abc123/src/lib.typ", "// template")
            zip_path.write_bytes(buf.getvalue())
        return result

    mock_run.side_effect = fake_curl
    path = install_template_http()
    assert "0.3.0" in str(path)
    assert (path / "src" / "lib.typ").exists()


@patch("mdo.core.template.find_installed_version", return_value="0.2.0")
def test_get_installed_version(mock_ver: MagicMock) -> None:
    assert get_installed_version() == "0.2.0"
