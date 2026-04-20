"""Local HTTP JSON server for Flutter communication."""

import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from mdo.core.compiler import compile_letter as core_compile
from mdo.core.fonts import check_fonts as core_check_fonts
from mdo.core.letter import delete_letter as core_delete_letter
from mdo.core.letter import list_letters as core_list_letters
from mdo.core.letter import load_letter as core_load_letter
from mdo.core.letter import save_letter as core_save_letter
from mdo.core.models import ProfileConfig
from mdo.core.paths import fonts_dir as core_fonts_dir
from mdo.core.paths import mdo_base_dir
from mdo.core.profile import delete_profile as core_delete_profile
from mdo.core.profile import list_profiles as core_list_profiles
from mdo.core.profile import load_profile as core_load_profile
from mdo.core.profile import save_profile as core_save_profile
from mdo.core.template import get_installed_version as core_get_version
from mdo.core.template import install_template as core_install_template

logger = logging.getLogger(__name__)


def _handle_list_profiles(params: dict[str, object]) -> list[str]:
    return core_list_profiles()


def _handle_load_profile(params: dict[str, object]) -> dict[str, object]:
    name = str(params.get("name", "default"))
    config = core_load_profile(name)
    return config.model_dump()


def _handle_save_profile(params: dict[str, object]) -> str:
    name = str(params.get("name", "default"))
    data = params.get("data", {})
    config = ProfileConfig.model_validate(data)
    path = core_save_profile(config, name=name)
    return str(path)


def _handle_delete_profile(params: dict[str, object]) -> str:
    name = str(params["name"])
    core_delete_profile(name)
    return "ok"


def _handle_get_template_version(params: dict[str, object]) -> str | None:
    return core_get_version()


def _handle_save_letter(params: dict[str, object]) -> str:
    fm_raw = params.get("frontmatter", {})
    fm: dict[str, object] = fm_raw if isinstance(fm_raw, dict) else {}
    body = str(params.get("body", ""))
    filename = params.get("filename")
    path = core_save_letter(fm, body, filename=str(filename) if filename else None)
    return str(path)


def _handle_load_letter(params: dict[str, object]) -> dict[str, object]:
    filename = str(params["filename"])
    fm, body = core_load_letter(filename)
    return {"frontmatter": fm, "body": body}


def _handle_list_letters(params: dict[str, object]) -> list[str]:
    return core_list_letters()


def _handle_delete_letter(params: dict[str, object]) -> str:
    filename = str(params["filename"])
    core_delete_letter(filename)
    return "ok"


def _handle_check_fonts(params: dict[str, object]) -> dict[str, object]:
    missing = core_check_fonts(core_fonts_dir())
    return {"missing": missing, "installed": len(missing) == 0}


def _handle_install_fonts(params: dict[str, object]) -> str:
    from mdo.commands.install_fonts import install_fonts as cli_install_fonts

    cli_install_fonts()
    return "ok"


def _handle_install_template(params: dict[str, object]) -> str:
    method = str(params.get("method", "auto"))
    path = core_install_template(method=method)
    return str(path)


def _handle_compile(params: dict[str, object]) -> dict[str, object]:
    path = Path(str(params["path"]))
    keep_typ = bool(params.get("keep_typ", False))
    output_dir = params.get("output_dir")
    pdf_path, data = core_compile(path, keep_typ=keep_typ)
    # PDF ins Ausgabeverzeichnis verschieben
    if output_dir and pdf_path.exists():
        target_dir = Path(str(output_dir))
        target_dir.mkdir(parents=True, exist_ok=True)
        final_path = target_dir / pdf_path.name
        import shutil

        shutil.move(str(pdf_path), str(final_path))
        pdf_path = final_path
    return {"pdf_path": str(pdf_path), "subject": data.subject, "date": data.date}


def _handle_copy_signature(params: dict[str, object]) -> str:
    """Kopiere eine Signatur-Datei nach ~/.mdo/unterschrift_PROFILNAME.ext."""
    source = Path(str(params["source"]))
    profile_name = str(params.get("profile_name", "default"))
    if not source.exists():
        msg = f"File not found: {source}"
        raise FileNotFoundError(msg)
    ext = source.suffix
    target = mdo_base_dir() / f"unterschrift_{profile_name}{ext}"
    import shutil

    shutil.copy2(str(source), str(target))
    return str(target)


METHODS: dict[str, object] = {
    "list_profiles": _handle_list_profiles,
    "load_profile": _handle_load_profile,
    "save_profile": _handle_save_profile,
    "delete_profile": _handle_delete_profile,
    "get_template_version": _handle_get_template_version,
    "check_fonts": _handle_check_fonts,
    "install_fonts": _handle_install_fonts,
    "install_template": _handle_install_template,
    "compile": _handle_compile,
    "save_letter": _handle_save_letter,
    "load_letter": _handle_load_letter,
    "list_letters": _handle_list_letters,
    "delete_letter": _handle_delete_letter,
    "copy_signature": _handle_copy_signature,
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
