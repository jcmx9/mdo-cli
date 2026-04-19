"""Local HTTP JSON server for Flutter communication."""

import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

from mdo.core.profile import list_profiles as core_list_profiles

logger = logging.getLogger(__name__)


def _handle_list_profiles(params: dict[str, object]) -> list[str]:
    return core_list_profiles()


METHODS: dict[str, object] = {
    "list_profiles": _handle_list_profiles,
}


class MdoRequestHandler(BaseHTTPRequestHandler):
    """Handle JSON-RPC-style requests."""

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"status": "ok"})
        else:
            self._send_json({"error": "Not found"}, code=404)

    def do_POST(self) -> None:
        if self.path != "/rpc":
            self._send_json({"error": "Not found"}, code=404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            request = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, code=400)
            return

        method = request.get("method", "")
        params = request.get("params", {})

        handler = METHODS.get(method)
        if handler is None:
            self._send_json({"error": f"Unknown method: {method}"})
            return

        try:
            result = handler(params)  # type: ignore[operator]
            self._send_json({"result": result})
        except Exception as e:
            logger.exception("Error in method %s", method)
            self._send_json({"error": str(e)})

    def _send_json(self, data: dict[str, object], code: int = 200) -> None:
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Suppress default stderr logging."""
        logger.debug(format, *args)


def create_server(port: int = 0) -> HTTPServer:
    """Create an HTTP server on localhost. port=0 for random free port."""
    server = HTTPServer(("127.0.0.1", port), MdoRequestHandler)
    actual_port = server.server_address[1]
    logger.info("Server listening on http://127.0.0.1:%d", actual_port)
    return server
