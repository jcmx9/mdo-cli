"""Entry point for Serious Python — starts the mdo HTTP server."""

import os
import sys

# Serious Python extrahiert den Code in ein Temp-Verzeichnis.
# Sicherstellen, dass mdo importierbar ist.
sys.path.insert(0, os.path.dirname(__file__))

# Gebündelte Binaries (typst, pandoc) zum PATH hinzufügen.
binaries_path = os.environ.get("MDO_BINARIES_PATH", "")
if binaries_path:
    os.environ["PATH"] = binaries_path + os.pathsep + os.environ.get("PATH", "")

from mdo.core.server import create_server

PORT_FILE = os.path.join(os.environ.get("TMPDIR", "/tmp"), "mdo_server_port.txt")


def main() -> None:
    server = create_server(port=0)
    port = server.server_address[1]

    with open(PORT_FILE, "w") as f:
        f.write(str(port))

    print(f"mdo server running on http://127.0.0.1:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
