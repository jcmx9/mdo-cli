# Design: Multi-Plattform Korrespondenz-Engine (Flutter-Integration)

**Datum:** 2026-04-19
**Branch:** `feature/flutter`
**Status:** Genehmigt

---

## 1. Ziel

mdo-cli wird um eine Flutter-basierte Desktop-App erweitert. CLI und App koexistieren — CLI für Power-User, Flutter-App für grafische Nutzung. Die Python-Kernlogik wird geteilt.

## 2. Architektur: Monorepo mit Shared Core

```
mdo-cli/
├── src/mdo/
│   ├── core/                 # Framework-unabhängige Kernlogik
│   │   ├── __init__.py
│   │   ├── models.py         # LetterData, ProfileConfig
│   │   ├── markdown.py       # md_to_typst (Pandoc)
│   │   ├── typst_builder.py  # .typ + .json Generierung
│   │   ├── fonts.py          # Font-Prüfung
│   │   ├── paths.py          # Plattformabhängige Pfade (erweitert)
│   │   ├── compiler.py       # compile()-Pipeline (extrahiert aus commands/)
│   │   ├── profile.py        # Multi-Profil: laden/speichern/wechseln
│   │   └── template.py       # Template install/update (Git + HTTP)
│   ├── commands/             # CLI-Commands (dünne Wrapper um core)
│   │   ├── compile.py
│   │   ├── new.py
│   │   ├── profile.py
│   │   ├── install_fonts.py
│   │   └── update.py
│   ├── cli.py                # Typer-App
│   ├── exceptions.py
│   ├── __init__.py
│   └── __main__.py
├── flutter/                  # Flutter-App
│   ├── lib/
│   ├── python/
│   │   └── main.py           # JSON-RPC Entrypoint für Serious Python
│   ├── android/
│   ├── ios/
│   ├── macos/
│   ├── windows/
│   ├── linux/
│   └── pubspec.yaml
├── tests/
├── scripts/
├── pyproject.toml
└── README.md
```

## 3. Core-API

Der Core exponiert reine Funktionen ohne CLI-Abhängigkeiten (kein Typer, keine `typer.Exit()`). Exceptions statt Exit-Codes.

### compiler.py

```python
def compile_letter(
    letter_path: Path,
    profile: ProfileConfig,
    output_dir: Path | None = None,
) -> Path:
    """Parse → Validate → Convert → Compile → Rename.
    Gibt Pfad zur fertigen PDF zurück."""
```

### profile.py

```python
def load_profile(name: str = "default") -> ProfileConfig:
    """Profil aus ~/.mdo/profiles/{name}.yaml laden."""

def save_profile(config: ProfileConfig, name: str = "default") -> Path:
    """Profil speichern."""

def list_profiles() -> list[str]:
    """Alle verfügbaren Profilnamen."""

def delete_profile(name: str) -> None:
    """Profil löschen (nicht 'default')."""
```

### template.py

```python
def install_template(method: str = "auto") -> Path:
    """Template installieren. method: 'git', 'http', 'auto'.
    'auto' = git auf Desktop, http auf Mobile/Fallback."""

def get_installed_version() -> str | None:
    """Installierte Template-Version oder None."""
```

### paths.py

```python
def mdo_base_dir() -> Path:
    """~/.mdo/ (Desktop) oder App-Sandbox (Mobile)."""

def profiles_dir() -> Path:
    """~/.mdo/profiles/"""

def fonts_dir() -> Path:
    """~/.mdo/fonts/"""
```

### Rückwärtskompatibilität

Wenn ein `profile.yaml` im aktuellen Arbeitsverzeichnis existiert, wird es bevorzugt. Das CLI-Verhalten bleibt unverändert.

## 4. Flutter↔Python Kommunikation

Python wird via Serious Python in die Flutter-App eingebettet. Kommunikation über **stdin/stdout JSON-RPC**.

### Python-Entrypoint

```python
# flutter/python/main.py
import json
import sys
from mdo.core.compiler import compile_letter
from mdo.core.profile import load_profile, save_profile, list_profiles

def handle(request: dict) -> dict:
    match request["method"]:
        case "compile":
            pdf = compile_letter(
                Path(request["path"]),
                load_profile(request["profile"]),
            )
            return {"result": str(pdf)}
        case "list_profiles":
            return {"result": list_profiles()}
        case "save_profile":
            save_profile(ProfileConfig(**request["data"]), request["name"])
            return {"result": "ok"}
        # ...

for line in sys.stdin:
    request = json.loads(line)
    try:
        response = handle(request)
    except Exception as e:
        response = {"error": str(e)}
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()
```

### Dart-Seite

```dart
class MdoEngine {
  Future<Map<String, dynamic>> call(String method, Map<String, dynamic> params);

  Future<String> compile(String path, String profile) async {
    final result = await call("compile", {"path": path, "profile": profile});
    return result["result"];
  }

  Future<List<String>> listProfiles() async { ... }
}
```

### Warum JSON-RPC über Pipes

- Plattformunabhängig (gleicher Code auf macOS/Windows/Linux)
- Einfach zu debuggen (JSON ist lesbar)
- Kein nativer Glue-Code pro Plattform nötig
- Serious Python unterstützt diesen Ansatz direkt

## 5. Flutter-App Aufbau

### Screens

```
App
├── Home (Briefe-Liste)
│   ├── Sortierung: Datum, Empfänger
│   ├── Suche
│   └── Swipe → Löschen / Duplizieren
├── Brief erstellen/bearbeiten
│   ├── Tab 1: Metadaten (Formular)
│   │   ├── Empfänger (mehrzeilig)
│   │   ├── Betreff
│   │   ├── Datum (Picker, Default: heute)
│   │   ├── Anlagen (dynamische Liste)
│   │   └── Profil-Auswahl (Dropdown)
│   ├── Tab 2: Brieftext (Markdown-Editor)
│   └── Actions: Speichern, Vorschau (PDF), Kompilieren
├── PDF-Vorschau (eingebettet)
├── Profile
│   ├── Liste aller Profile
│   ├── Profil erstellen/bearbeiten (Formular)
│   └── Profil löschen
├── Einstellungen
│   ├── Template-Version + Update-Button
│   ├── Font-Status + Install-Button
│   └── Standard-Profil wählen
```

### Tech-Stack

| Bereich | Lösung |
|---------|--------|
| State Management | Riverpod |
| Navigation | GoRouter |
| PDF-Anzeige | `pdfx` oder `syncfusion_flutter_pdfviewer` |
| Markdown-Editor | `flutter_markdown` + `code_text_field` |
| Dateisystem | `path_provider` |
| Design | Material 3 mit Custom-Theme |
| Python-Embedding | Serious Python |

### Eingabe-Konzept

- **Hybrid:** Formular für Metadaten (Empfänger, Betreff, Datum etc.), Markdown-Editor für den Brieftext
- **PDF-Vorschau auf Knopfdruck** (kein Live-Preview)

## 6. Datenhaltung

### Pfad-Strategie (Kompromiss)

- **Desktop:** User arbeitet in beliebigen Verzeichnissen (wie bisher). `~/.mdo/` für Profile und Konfiguration.
- **Mobile (Zukunft):** App-Sandbox-Verzeichnis mit gleicher interner Struktur.
- Ein Pfad-Resolver (`mdo_base_dir()`) entscheidet je nach Plattform.

### Verzeichnisstruktur

```
~/.mdo/
├── profiles/
│   ├── default.yaml
│   └── geschaeftlich.yaml
└── fonts/
    └── *.otf
```

### Briefe

- Werden als `.md`-Dateien gespeichert (gleiche Struktur wie CLI)
- Desktop: im Arbeitsverzeichnis des Users
- Mobile: im App-Dokumentenverzeichnis

## 7. Template-Bereitstellung

- **Bundled:** Template wird in die App eingebaut (offline-fähig ab Start)
- **HTTP-Download:** Update über GitHub Releases ZIP-Download
- **Git-Clone:** Bleibt als Alternative auf Desktop (bestehender `mdo update`)
- `install_template(method="auto")` wählt automatisch: Git auf Desktop, HTTP auf Mobile/Fallback

## 8. Phasenplan

### Phase 1: Core-Refactoring (Python)

- Logik aus `commands/` in `core/` extrahieren
- Multi-Profil-Support (`~/.mdo/profiles/`)
- Template-Install via HTTP als Alternative zu Git
- Plattform-Pfad-Resolver (`mdo_base_dir()`)
- CLI bleibt voll funktionsfähig, Tests grün
- Kein Flutter-Code in Phase 1

### Phase 2: Flutter Desktop-App

- Flutter-Projekt unter `flutter/`
- Serious Python Integration
- JSON-RPC Bridge (`flutter/python/main.py`)
- Alle Screens (Home, Brief, Profile, Einstellungen)
- PDF-Vorschau auf Knopfdruck
- Packaging: `.dmg`, `.msi`, `.AppImage`
- Plattformen: macOS, Windows, Linux

### Phase 3: Mobile (Zukunft)

- Pandoc durch Python-native Lösung ersetzen
- Typst als Rust-Lib via FFI einbinden
- iOS + Android Builds
- App-Store-Distribution (optional)

## 9. Nicht im Scope

- Cloud-Sync / Accounts
- Kollaboration / Sharing
- Eigener Markdown-zu-PDF-Renderer (Typst bleibt der Renderer)
- Template-Editor (Template kommt aus `typst-DIN5008a`)
- Verschlüsselung / Passwortschutz
- Live-PDF-Preview (nur auf Knopfdruck)

## 10. Distribution

- GitHub Releases: `.dmg` (macOS), `.msi` (Windows), `.AppImage` (Linux)
- App-Stores erst später, wenn die App reif ist
