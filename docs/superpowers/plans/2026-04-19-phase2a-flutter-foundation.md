# Phase 2a: Flutter Foundation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Flutter Desktop-App-Gerüst mit eingebettetem Python-Backend aufsetzen, sodass `mdo profile list` über Flutter→Python funktioniert.

**Architecture:** Serious Python bettet den Python-Interpreter in die Flutter-App ein. Python startet einen lokalen HTTP-Server (stdlib `http.server`), Dart kommuniziert per HTTP-POST mit JSON. Riverpod verwaltet den State, GoRouter die Navigation. Phase 2a endet mit einer funktionierenden End-to-End-Verbindung: Flutter-Button → HTTP → Python `list_profiles()` → Anzeige in Flutter.

**Tech Stack:** Flutter 3.x, Dart, Serious Python 0.9.x, Riverpod 3.x, GoRouter 17.x, Python 3.12 stdlib `http.server`

**Design-Änderung gegenüber Spec:** Der Spec beschreibt JSON-RPC über stdin/stdout-Pipes. Serious Python unterstützt das nicht — stattdessen nutzen wir einen lokalen HTTP-JSON-Server. Die API-Semantik bleibt gleich (method + params → result/error), nur der Transport ändert sich.

---

## File Structure

### New Files (Flutter)

| File | Responsibility |
|------|---------------|
| `flutter/pubspec.yaml` | Flutter-Projekt-Konfiguration, Dependencies |
| `flutter/lib/main.dart` | App-Einstiegspunkt, ProviderScope, MaterialApp |
| `flutter/lib/app.dart` | GoRouter-Konfiguration, Theme |
| `flutter/lib/engine/mdo_engine.dart` | HTTP-Client zum Python-Backend |
| `flutter/lib/providers/engine_provider.dart` | Riverpod-Provider für MdoEngine |
| `flutter/lib/providers/profile_provider.dart` | Riverpod-Provider für Profile-Liste |
| `flutter/lib/screens/home_screen.dart` | Startseite mit Profil-Liste (Proof of Concept) |
| `flutter/test/engine/mdo_engine_test.dart` | Unit-Tests für MdoEngine |

### New Files (Python)

| File | Responsibility |
|------|---------------|
| `src/mdo/core/server.py` | Lokaler HTTP-JSON-Server für Flutter-Kommunikation |
| `tests/test_server.py` | Tests für den Server |
| `flutter/python/main.py` | Entrypoint für Serious Python (startet Server) |

---

### Task 1: Python HTTP-JSON-Server (`core/server.py`)

**Files:**
- Create: `src/mdo/core/server.py`
- Create: `tests/test_server.py`

- [ ] **Step 1: Failing Tests schreiben**

```python
# tests/test_server.py
import json
import threading
import urllib.request
from unittest.mock import patch

import pytest

from mdo.core.server import MdoRequestHandler, create_server


@pytest.fixture
def server():
    """Start server on random port, yield base URL, stop after test."""
    srv = create_server(port=0)  # port=0 = OS wählt freien Port
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
```

- [ ] **Step 2: Tests ausführen — FAIL erwartet**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest tests/test_server.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implementierung**

```python
# src/mdo/core/server.py
"""Local HTTP JSON server for Flutter communication."""

import json
import logging
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer

from mdo.core.profile import list_profiles as core_list_profiles

logger = logging.getLogger(__name__)

# Dispatch-Tabelle: method-Name → Funktion
METHODS: dict[str, object] = {
    "list_profiles": lambda params: core_list_profiles(),
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
            result = handler(params)
            self._send_json({"result": result})
        except Exception as e:
            logger.exception("Error in method %s", method)
            self._send_json({"error": str(e)})

    def _send_json(self, data: dict, code: int = 200) -> None:
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        """Suppress default stderr logging."""
        logger.debug(format, *args)


def create_server(port: int = 0) -> HTTPServer:
    """Create an HTTP server on localhost. port=0 for random free port."""
    server = HTTPServer(("127.0.0.1", port), MdoRequestHandler)
    actual_port = server.server_address[1]
    logger.info("Server listening on http://127.0.0.1:%d", actual_port)
    return server
```

- [ ] **Step 4: Tests ausführen — PASS erwartet**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest tests/test_server.py -v`
Expected: PASS

- [ ] **Step 5: Lint + Type-Check**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run ruff check src/mdo/core/server.py tests/test_server.py && uv run mypy src/`
Expected: Keine Fehler

- [ ] **Step 6: Commit**

```bash
git add src/mdo/core/server.py tests/test_server.py
git commit -m "feat(core): add local HTTP JSON server for Flutter communication"
```

---

### Task 2: Server um weitere Methoden erweitern

**Files:**
- Modify: `src/mdo/core/server.py`
- Modify: `tests/test_server.py`

- [ ] **Step 1: Failing Tests schreiben**

```python
# tests/test_server.py — zusätzliche Tests

@patch("mdo.core.server.core_get_version", return_value="0.2.0")
def test_get_template_version(mock_ver, server):
    result = _post(server, "get_template_version")
    assert result == {"result": "0.2.0"}


@patch("mdo.core.server.core_load_profile")
def test_load_profile(mock_load, server):
    from mdo.core.models import ProfileConfig
    mock_load.return_value = ProfileConfig(
        name="Test", street="Str 1", zip="12345", city="Stadt"
    )
    result = _post(server, "load_profile", {"name": "default"})
    assert result["result"]["name"] == "Test"


@patch("mdo.core.server.core_compile")
def test_compile(mock_compile, server):
    from pathlib import Path
    from mdo.core.models import LetterData
    data = LetterData(
        name="Test", street="S", zip="1", city="C",
        recipient=["R"], date="01. April 2026", subject="S",
    )
    mock_compile.return_value = (Path("/tmp/test.pdf"), data)
    result = _post(server, "compile", {"path": "/tmp/brief.md"})
    assert result["result"]["pdf_path"] == "/tmp/test.pdf"
```

- [ ] **Step 2: Tests ausführen — FAIL erwartet**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest tests/test_server.py -v`
Expected: FAIL — neue Methoden noch nicht registriert

- [ ] **Step 3: Server erweitern**

In `src/mdo/core/server.py` — Imports und METHODS erweitern:

```python
from mdo.core.compiler import compile_letter as core_compile
from mdo.core.profile import (
    delete_profile as core_delete_profile,
    list_profiles as core_list_profiles,
    load_profile as core_load_profile,
    save_profile as core_save_profile,
)
from mdo.core.models import ProfileConfig
from mdo.core.template import get_installed_version as core_get_version

from pathlib import Path


def _handle_list_profiles(params: dict) -> list[str]:
    return core_list_profiles()


def _handle_load_profile(params: dict) -> dict:
    name = params.get("name", "default")
    config = core_load_profile(name)
    return config.model_dump()


def _handle_save_profile(params: dict) -> str:
    name = params.get("name", "default")
    data = params.get("data", {})
    config = ProfileConfig.model_validate(data)
    path = core_save_profile(config, name=name)
    return str(path)


def _handle_delete_profile(params: dict) -> str:
    name = params["name"]
    core_delete_profile(name)
    return "ok"


def _handle_get_template_version(params: dict) -> str | None:
    return core_get_version()


def _handle_compile(params: dict) -> dict:
    path = Path(params["path"])
    keep_typ = params.get("keep_typ", False)
    pdf_path, data = core_compile(path, keep_typ=keep_typ)
    return {"pdf_path": str(pdf_path), "subject": data.subject, "date": data.date}


METHODS: dict[str, object] = {
    "list_profiles": _handle_list_profiles,
    "load_profile": _handle_load_profile,
    "save_profile": _handle_save_profile,
    "delete_profile": _handle_delete_profile,
    "get_template_version": _handle_get_template_version,
    "compile": _handle_compile,
}
```

- [ ] **Step 4: Tests ausführen — PASS erwartet**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest tests/test_server.py -v`
Expected: PASS

- [ ] **Step 5: Alle Tests ausführen**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest -v`
Expected: PASS (bestehende Tests dürfen nicht brechen)

- [ ] **Step 6: Lint + Type-Check**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run ruff check src/ tests/ && uv run mypy src/`
Expected: Keine Fehler

- [ ] **Step 7: Commit**

```bash
git add src/mdo/core/server.py tests/test_server.py
git commit -m "feat(core): add compile/profile/template methods to server"
```

---

### Task 3: Python-Entrypoint für Serious Python

**Files:**
- Create: `flutter/python/main.py`

Dieser Task benötigt kein TDD — es ist ein einfaches Startskript.

- [ ] **Step 1: Verzeichnis erstellen**

```bash
mkdir -p flutter/python
```

- [ ] **Step 2: Entrypoint erstellen**

```python
# flutter/python/main.py
"""Entry point for Serious Python — starts the mdo HTTP server."""

import os
import sys

# Serious Python setzt das Arbeitsverzeichnis
# Wir müssen sicherstellen, dass mdo importierbar ist
sys.path.insert(0, os.path.dirname(__file__))

from mdo.core.server import create_server

PORT_FILE = os.path.join(os.environ.get("TMPDIR", "/tmp"), "mdo_server_port.txt")


def main() -> None:
    server = create_server(port=0)
    port = server.server_address[1]

    # Port in Datei schreiben, damit Flutter ihn lesen kann
    with open(PORT_FILE, "w") as f:
        f.write(str(port))

    print(f"mdo server running on http://127.0.0.1:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Commit**

```bash
git add flutter/python/main.py
git commit -m "feat(flutter): add Python entrypoint for Serious Python"
```

---

### Task 4: Flutter-Projekt erstellen

**Files:**
- Create: `flutter/` (gesamtes Flutter-Scaffold)
- Modify: `flutter/pubspec.yaml`

- [ ] **Step 1: Flutter-Projekt erstellen**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli
flutter create --platforms=macos,linux,windows --project-name mdo_app flutter
```

- [ ] **Step 2: `pubspec.yaml` anpassen**

Ersetze den Inhalt von `flutter/pubspec.yaml`:

```yaml
name: mdo_app
description: "DIN 5008 Form A Briefgenerator – Desktop-App"
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  flutter_riverpod: ^3.3.1
  go_router: ^17.2.1
  serious_python: ^0.9.11
  http: ^1.1.0
  pdfrx: ^2.2.24
  path_provider: ^2.1.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0

flutter:
  uses-material-design: true
  assets:
    - python/
```

- [ ] **Step 3: Dependencies installieren**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli/flutter
flutter pub get
```

- [ ] **Step 4: Commit**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli
git add flutter/
git commit -m "feat(flutter): create Flutter desktop project scaffold"
```

---

### Task 5: MdoEngine — Dart HTTP-Client

**Files:**
- Create: `flutter/lib/engine/mdo_engine.dart`
- Create: `flutter/test/engine/mdo_engine_test.dart`

- [ ] **Step 1: Test schreiben**

```dart
// flutter/test/engine/mdo_engine_test.dart
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:mdo_app/engine/mdo_engine.dart';

void main() {
  late HttpServer mockServer;
  late MdoEngine engine;

  setUp(() async {
    // Starte einen Mock-Server
    mockServer = await HttpServer.bind('127.0.0.1', 0);
    mockServer.listen((request) async {
      if (request.uri.path == '/health') {
        request.response
          ..headers.contentType = ContentType.json
          ..write(jsonEncode({'status': 'ok'}))
          ..close();
        return;
      }
      if (request.uri.path == '/rpc' && request.method == 'POST') {
        final body = await utf8.decoder.bind(request).join();
        final data = jsonDecode(body) as Map<String, dynamic>;
        final method = data['method'] as String;

        Map<String, dynamic> response;
        if (method == 'list_profiles') {
          response = {'result': ['default', 'work']};
        } else {
          response = {'error': 'Unknown method: $method'};
        }

        request.response
          ..headers.contentType = ContentType.json
          ..write(jsonEncode(response))
          ..close();
        return;
      }
      request.response
        ..statusCode = 404
        ..close();
    });

    engine = MdoEngine(port: mockServer.port);
  });

  tearDown(() async {
    await mockServer.close();
  });

  test('health check returns ok', () async {
    final healthy = await engine.isHealthy();
    expect(healthy, isTrue);
  });

  test('listProfiles returns profile names', () async {
    final profiles = await engine.listProfiles();
    expect(profiles, equals(['default', 'work']));
  });

  test('call with unknown method returns error', () async {
    expect(
      () => engine.call('nonexistent', {}),
      throwsException,
    );
  });
}
```

- [ ] **Step 2: Tests ausführen — FAIL erwartet**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli/flutter
flutter test test/engine/mdo_engine_test.dart
```

Expected: FAIL — Datei `mdo_engine.dart` existiert noch nicht

- [ ] **Step 3: MdoEngine implementieren**

```dart
// flutter/lib/engine/mdo_engine.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

/// HTTP-Client zum lokalen Python-Backend.
class MdoEngine {
  final int port;
  final http.Client _client;

  MdoEngine({required this.port, http.Client? client})
      : _client = client ?? http.Client();

  String get _baseUrl => 'http://127.0.0.1:$port';

  /// Prüft ob der Server erreichbar ist.
  Future<bool> isHealthy() async {
    try {
      final response = await _client.get(Uri.parse('$_baseUrl/health'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return data['status'] == 'ok';
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  /// Sendet einen JSON-RPC-Aufruf an den Server.
  Future<dynamic> call(String method, Map<String, dynamic> params) async {
    final response = await _client.post(
      Uri.parse('$_baseUrl/rpc'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'method': method, 'params': params}),
    );

    final data = jsonDecode(response.body) as Map<String, dynamic>;

    if (data.containsKey('error')) {
      throw Exception(data['error']);
    }

    return data['result'];
  }

  /// Gibt alle Profilnamen zurück.
  Future<List<String>> listProfiles() async {
    final result = await call('list_profiles', {});
    return (result as List).cast<String>();
  }

  /// Lädt ein Profil als Map.
  Future<Map<String, dynamic>> loadProfile(String name) async {
    final result = await call('load_profile', {'name': name});
    return result as Map<String, dynamic>;
  }

  /// Gibt die installierte Template-Version zurück.
  Future<String?> getTemplateVersion() async {
    final result = await call('get_template_version', {});
    return result as String?;
  }

  /// Kompiliert eine .md-Datei zu PDF.
  Future<String> compile(String path) async {
    final result = await call('compile', {'path': path});
    return (result as Map<String, dynamic>)['pdf_path'] as String;
  }

  void dispose() {
    _client.close();
  }
}
```

- [ ] **Step 4: Tests ausführen — PASS erwartet**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli/flutter
flutter test test/engine/mdo_engine_test.dart
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli
git add flutter/lib/engine/ flutter/test/engine/
git commit -m "feat(flutter): add MdoEngine HTTP client for Python backend"
```

---

### Task 6: Riverpod-Provider

**Files:**
- Create: `flutter/lib/providers/engine_provider.dart`
- Create: `flutter/lib/providers/profile_provider.dart`

- [ ] **Step 1: Engine-Provider erstellen**

```dart
// flutter/lib/providers/engine_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mdo_app/engine/mdo_engine.dart';

/// Provider für die MdoEngine-Instanz.
/// Wird gesetzt, sobald der Python-Server gestartet ist.
final engineProvider = StateProvider<MdoEngine?>((ref) => null);
```

- [ ] **Step 2: Profile-Provider erstellen**

```dart
// flutter/lib/providers/profile_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mdo_app/providers/engine_provider.dart';

/// Provider für die Liste der Profilnamen.
final profileListProvider = FutureProvider<List<String>>((ref) async {
  final engine = ref.watch(engineProvider);
  if (engine == null) return [];
  return engine.listProfiles();
});
```

- [ ] **Step 3: Commit**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli
git add flutter/lib/providers/
git commit -m "feat(flutter): add Riverpod providers for engine and profiles"
```

---

### Task 7: App-Shell mit GoRouter

**Files:**
- Create: `flutter/lib/app.dart`
- Modify: `flutter/lib/main.dart`
- Create: `flutter/lib/screens/home_screen.dart`

- [ ] **Step 1: HomeScreen erstellen**

```dart
// flutter/lib/screens/home_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mdo_app/providers/engine_provider.dart';
import 'package:mdo_app/providers/profile_provider.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final engine = ref.watch(engineProvider);
    final profilesAsync = ref.watch(profileListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('mdo'),
        actions: [
          // Verbindungsstatus
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Icon(
              engine != null ? Icons.check_circle : Icons.error,
              color: engine != null ? Colors.green : Colors.red,
            ),
          ),
        ],
      ),
      body: Center(
        child: profilesAsync.when(
          data: (profiles) {
            if (profiles.isEmpty) {
              return const Text('Keine Profile gefunden.');
            }
            return ListView.builder(
              itemCount: profiles.length,
              itemBuilder: (context, index) => ListTile(
                leading: const Icon(Icons.person),
                title: Text(profiles[index]),
              ),
            );
          },
          loading: () => const CircularProgressIndicator(),
          error: (error, _) => Text('Fehler: $error'),
        ),
      ),
    );
  }
}
```

- [ ] **Step 2: App-Router erstellen**

```dart
// flutter/lib/app.dart
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:mdo_app/screens/home_screen.dart';

final router = GoRouter(
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
    ),
  ],
);

class MdoApp extends StatelessWidget {
  const MdoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'mdo',
      theme: ThemeData(
        colorSchemeSeed: Colors.blueGrey,
        useMaterial3: true,
      ),
      routerConfig: router,
    );
  }
}
```

- [ ] **Step 3: main.dart — Serious Python starten + Engine verbinden**

```dart
// flutter/lib/main.dart
import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:serious_python/serious_python.dart';

import 'package:mdo_app/app.dart';
import 'package:mdo_app/engine/mdo_engine.dart';
import 'package:mdo_app/providers/engine_provider.dart';

void main() {
  runApp(
    const ProviderScope(
      child: _AppLoader(),
    ),
  );
}

class _AppLoader extends ConsumerStatefulWidget {
  const _AppLoader();

  @override
  ConsumerState<_AppLoader> createState() => _AppLoaderState();
}

class _AppLoaderState extends ConsumerState<_AppLoader> {
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _startPythonServer();
  }

  Future<void> _startPythonServer() async {
    try {
      // Python-Server starten via Serious Python
      await SeriousPython.run('python/main.py');

      // Warten bis die Port-Datei geschrieben wurde
      final portFile = File('${Directory.systemTemp.path}/mdo_server_port.txt');
      int? port;
      for (var i = 0; i < 50; i++) {
        await Future.delayed(const Duration(milliseconds: 100));
        if (await portFile.exists()) {
          final content = await portFile.readAsString();
          port = int.tryParse(content.trim());
          if (port != null) break;
        }
      }

      if (port == null) {
        setState(() {
          _error = 'Python-Server konnte nicht gestartet werden.';
          _loading = false;
        });
        return;
      }

      // Engine erstellen und Health-Check
      final engine = MdoEngine(port: port);
      for (var i = 0; i < 20; i++) {
        if (await engine.isHealthy()) break;
        await Future.delayed(const Duration(milliseconds: 100));
      }

      ref.read(engineProvider.notifier).state = engine;
      setState(() => _loading = false);
    } catch (e) {
      setState(() {
        _error = 'Fehler: $e';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const MaterialApp(
        home: Scaffold(
          body: Center(child: CircularProgressIndicator()),
        ),
      );
    }

    if (_error != null) {
      return MaterialApp(
        home: Scaffold(
          body: Center(child: Text(_error!)),
        ),
      );
    }

    return const MdoApp();
  }
}
```

- [ ] **Step 4: Commit**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli
git add flutter/lib/
git commit -m "feat(flutter): add app shell with GoRouter, Riverpod, and Python launcher"
```

---

### Task 8: End-to-End-Verifikation

**Files:** keine neuen Dateien — nur Verifikation

- [ ] **Step 1: Python-Tests**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli
uv run pytest -v
```

Expected: alle bestehenden + neue Server-Tests bestehen

- [ ] **Step 2: Python Lint + Type-Check**

```bash
uv run ruff check src/ tests/ && uv run mypy src/
```

Expected: Keine Fehler

- [ ] **Step 3: Flutter-Tests**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli/flutter
flutter test
```

Expected: MdoEngine-Tests bestehen

- [ ] **Step 4: Flutter-App starten (manuell)**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli/flutter
flutter run -d macos
```

Expected: App startet, zeigt Lade-Indikator, dann Profil-Liste (oder "Keine Profile gefunden" falls noch kein Profil unter `~/.mdo/profiles/` existiert).

Manueller Test:
1. In Terminal: `mdo profile create` → Profil erstellen
2. Flutter-App neustarten
3. Profil sollte in der Liste erscheinen

- [ ] **Step 5: Commit + Tag**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli
git add -A
git commit -m "chore: verify end-to-end Flutter-Python integration"
```

---

## Zusammenfassung

| Task | Was | Dateien |
|------|-----|---------|
| 1 | Python HTTP-JSON-Server (Basis) | `core/server.py`, `tests/test_server.py` |
| 2 | Server-Methoden erweitern | `core/server.py`, `tests/test_server.py` |
| 3 | Python-Entrypoint für Serious Python | `flutter/python/main.py` |
| 4 | Flutter-Projekt erstellen | `flutter/*` |
| 5 | MdoEngine Dart HTTP-Client | `flutter/lib/engine/`, `flutter/test/engine/` |
| 6 | Riverpod-Provider | `flutter/lib/providers/` |
| 7 | App-Shell (GoRouter, Screens) | `flutter/lib/app.dart`, `flutter/lib/screens/`, `flutter/lib/main.dart` |
| 8 | End-to-End-Verifikation | — |

Nach Abschluss:
- Python-Server läuft als eingebetteter Prozess in der Flutter-App
- Flutter kommuniziert per HTTP-JSON mit Python
- `list_profiles()` funktioniert end-to-end
- Grundlage für Phase 2b (Screens) steht
