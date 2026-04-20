"""Entry point for Serious Python — starts the mdo HTTP server."""

import os
import sys
import traceback

# Log-Datei für Debugging
LOG_FILE = os.path.join(os.environ.get("TMPDIR", "/tmp"), "mdo_python.log")

try:
    with open(LOG_FILE, "w") as log:
        log.write(f"Python started. Version: {sys.version}\n")
        log.write(f"CWD: {os.getcwd()}\n")
        log.write(f"__file__: {__file__}\n")
        log.write(f"sys.path: {sys.path}\n")
        log.write(f"TMPDIR: {os.environ.get('TMPDIR', 'not set')}\n")
        log.write(f"MDO_BINARIES_PATH: {os.environ.get('MDO_BINARIES_PATH', 'not set')}\n")

    # Sicherstellen, dass mdo importierbar ist.
    sys.path.insert(0, os.path.dirname(__file__))

    # Gebündelte Binaries (typst, pandoc) zum PATH hinzufügen.
    binaries_path = os.environ.get("MDO_BINARIES_PATH", "")
    if binaries_path:
        os.environ["PATH"] = binaries_path + os.pathsep + os.environ.get("PATH", "")

    from mdo.core.server import create_server

    PORT_FILE = os.path.join(os.environ.get("TMPDIR", "/tmp"), "mdo_server_port.txt")

    server = create_server(port=0)
    port = server.server_address[1]

    with open(PORT_FILE, "w") as f:
        f.write(str(port))

    with open(LOG_FILE, "a") as log:
        log.write(f"Server running on http://127.0.0.1:{port}\n")

    print(f"mdo server running on http://127.0.0.1:{port}", flush=True)
    server.serve_forever()

except Exception:
    with open(LOG_FILE, "a") as log:
        log.write(f"\nERROR:\n{traceback.format_exc()}\n")
    raise
