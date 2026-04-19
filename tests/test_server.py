# tests/test_server.py
import json
import threading
import urllib.request
from unittest.mock import patch

import pytest

from mdo.core.server import create_server


@pytest.fixture
def server():
    """Start server on random port, yield base URL, stop after test."""
    srv = create_server(port=0)
    port = srv.server_address[1]
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    srv.shutdown()


def _post(base_url: str, method: str, params: dict | None = None) -> dict:
    """Send a JSON-RPC-style POST request."""
    body = json.dumps({"method": method, "params": params or {}}).encode()
    req = urllib.request.Request(
        f"{base_url}/rpc",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


@patch("mdo.core.server.core_list_profiles", return_value=["default", "work"])
def test_list_profiles(mock_list, server):
    result = _post(server, "list_profiles")
    assert result == {"result": ["default", "work"]}


def test_unknown_method(server):
    result = _post(server, "nonexistent_method")
    assert "error" in result


def test_health(server):
    req = urllib.request.Request(f"{server}/health")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    assert data["status"] == "ok"


@patch("mdo.core.server.core_get_version", return_value="0.2.0")
def test_get_template_version(mock_ver, server):
    result = _post(server, "get_template_version")
    assert result == {"result": "0.2.0"}


@patch("mdo.core.server.core_load_profile")
def test_load_profile(mock_load, server):
    from mdo.core.models import ProfileConfig

    mock_load.return_value = ProfileConfig(name="Test", street="Str 1", zip="12345", city="Stadt")
    result = _post(server, "load_profile", {"name": "default"})
    assert result["result"]["name"] == "Test"


@patch("mdo.core.server.core_delete_profile")
def test_delete_profile(mock_del, server):
    result = _post(server, "delete_profile", {"name": "temp"})
    assert result == {"result": "ok"}
    mock_del.assert_called_once_with("temp")


@patch("mdo.core.server.core_save_letter")
def test_save_letter(mock_save, server):
    from pathlib import Path

    mock_save.return_value = Path("/tmp/.mdo/letters/brief.md")
    result = _post(
        server,
        "save_letter",
        {
            "frontmatter": {"subject": "Test", "recipient": ["Firma"]},
            "body": "Hallo Welt",
        },
    )
    assert "brief.md" in result["result"]


@patch("mdo.core.server.core_load_letter")
def test_load_letter(mock_load, server):
    mock_load.return_value = ({"subject": "Test"}, "Hallo Welt")
    result = _post(server, "load_letter", {"filename": "brief.md"})
    assert result["result"]["frontmatter"]["subject"] == "Test"
    assert result["result"]["body"] == "Hallo Welt"


@patch("mdo.core.server.core_list_letters", return_value=["brief1.md", "brief2.md"])
def test_list_letters(mock_list, server):
    result = _post(server, "list_letters")
    assert result == {"result": ["brief1.md", "brief2.md"]}


@patch("mdo.core.server.core_delete_letter")
def test_delete_letter(mock_del, server):
    result = _post(server, "delete_letter", {"filename": "brief.md"})
    assert result == {"result": "ok"}


@patch("mdo.core.server.core_compile")
def test_compile(mock_compile, server):
    from pathlib import Path

    from mdo.core.models import LetterData

    data = LetterData(
        name="Test",
        street="S",
        zip="1",
        city="C",
        recipient=["R"],
        date="01. April 2026",
        subject="Betreff",
    )
    mock_compile.return_value = (Path("/tmp/test.pdf"), data)
    result = _post(server, "compile", {"path": "/tmp/brief.md"})
    assert result["result"]["pdf_path"] == "/tmp/test.pdf"
    assert result["result"]["subject"] == "Betreff"
