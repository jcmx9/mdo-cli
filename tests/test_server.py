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
