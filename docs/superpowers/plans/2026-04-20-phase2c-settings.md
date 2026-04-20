# Phase 2c: Settings & Polish — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Settings-Screen mit Template-Update, Font-Status und Standard-Profil-Auswahl. Dazu Server-Methoden für Font-Check, Font-Install und Template-Update.

**Architecture:** Drei neue Server-Methoden (`check_fonts`, `install_fonts`, `install_template`) exponieren die bestehende Core-Logik. Der Settings-Screen zeigt den Status an und bietet Update/Install-Buttons. Kein neuer Python-Core-Code nötig — alles existiert bereits in `core/fonts.py`, `commands/install_fonts.py` und `core/template.py`.

**Tech Stack:** Python 3.12, Flutter/Dart, Riverpod 3.x

---

## File Structure

### Modified Python Files

| File | Responsibility |
|------|---------------|
| `src/mdo/core/server.py` | Neue Methoden: `check_fonts`, `install_fonts`, `install_template` |
| `tests/test_server.py` | Tests für neue Methoden |

### New Flutter Files

| File | Responsibility |
|------|---------------|
| `flutter/lib/screens/settings_screen.dart` | Settings-Screen |
| `flutter/lib/providers/settings_provider.dart` | Provider für Template-Version und Font-Status |

### Modified Flutter Files

| File | Responsibility |
|------|---------------|
| `flutter/lib/app.dart` | Neue Route `/settings` |
| `flutter/lib/screens/letter_list_screen.dart` | Settings-Icon in AppBar |
| `flutter/lib/engine/mdo_engine.dart` | Neue Methoden |

---

### Task 1: Server-Methoden für Fonts und Template

**Files:**
- Modify: `src/mdo/core/server.py`
- Modify: `tests/test_server.py`

- [ ] **Step 1: Failing Tests schreiben**

```python
# tests/test_server.py — neue Tests

@patch("mdo.core.server.core_check_fonts", return_value=[])
def test_check_fonts_ok(mock_check, server):
    result = _post(server, "check_fonts")
    assert result == {"result": {"missing": [], "installed": True}}


@patch("mdo.core.server.core_check_fonts", return_value=["Source Serif 4"])
def test_check_fonts_missing(mock_check, server):
    result = _post(server, "check_fonts")
    assert result["result"]["installed"] is False
    assert "Source Serif 4" in result["result"]["missing"]


@patch("mdo.core.server.core_install_fonts")
def test_install_fonts(mock_install, server):
    result = _post(server, "install_fonts")
    assert result == {"result": "ok"}


@patch("mdo.core.server.core_install_template")
def test_install_template(mock_install, server):
    from pathlib import Path
    mock_install.return_value = Path("/tmp/packages/din5008a/0.3.0")
    result = _post(server, "install_template")
    assert "0.3.0" in result["result"]
```

- [ ] **Step 2: Server erweitern**

In `src/mdo/core/server.py` — neue Imports:

```python
from mdo.core.fonts import check_fonts as core_check_fonts
from mdo.core.paths import fonts_dir as core_fonts_dir
from mdo.core.template import install_template as core_install_template
```

Neue Handler:

```python
def _handle_check_fonts(params: dict[str, object]) -> dict[str, object]:
    missing = core_check_fonts(core_fonts_dir())
    return {"missing": missing, "installed": len(missing) == 0}


def _handle_install_fonts(params: dict[str, object]) -> str:
    # Ruft die install_fonts-Logik auf — diese ist in commands/install_fonts.py
    # und hat typer-Abhängigkeiten. Wir importieren die Font-Download-Logik direkt.
    from mdo.commands.install_fonts import install_fonts as cli_install_fonts
    cli_install_fonts()
    return "ok"


def _handle_install_template(params: dict[str, object]) -> str:
    method = str(params.get("method", "auto"))
    path = core_install_template(method=method)
    return str(path)
```

In METHODS hinzufügen:

```python
    "check_fonts": _handle_check_fonts,
    "install_fonts": _handle_install_fonts,
    "install_template": _handle_install_template,
```

**Hinweis:** `install_fonts` ruft den CLI-Command auf, der `typer.echo` verwendet. Das ist ein Kompromiss — die Font-Download-Logik wurde in Phase 1 nicht in Core extrahiert. Für Phase 2c akzeptabel, da die Funktion trotzdem funktioniert (typer.echo schreibt nach stdout, was im Server-Kontext ignoriert wird).

- [ ] **Step 3: Tests + Lint + Commit**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli
uv run pytest tests/test_server.py -v
uv run pytest tests/ -v
uv run ruff check src/ tests/ && uv run mypy src/
git add src/mdo/core/server.py tests/test_server.py
git commit -m "feat(core): add fonts/template management methods to server"
```

---

### Task 2: MdoEngine erweitern

**Files:**
- Modify: `flutter/lib/engine/mdo_engine.dart`
- Modify: `flutter/test/engine/mdo_engine_test.dart`

- [ ] **Step 1: Methoden hinzufügen**

```dart
// In mdo_engine.dart — neue Methoden

  /// Prüft den Font-Status.
  Future<Map<String, dynamic>> checkFonts() async {
    final result = await call('check_fonts', {});
    return result as Map<String, dynamic>;
  }

  /// Installiert fehlende Fonts.
  Future<void> installFonts() async {
    await call('install_fonts', {});
  }

  /// Aktualisiert das Typst-Template.
  Future<String> installTemplate() async {
    final result = await call('install_template', {});
    return result as String;
  }
```

- [ ] **Step 2: Mock-Server erweitern + Tests**

Im Mock-Server:

```dart
} else if (method == 'check_fonts') {
  response = {
    'result': {'missing': [], 'installed': true}
  };
} else if (method == 'install_fonts') {
  response = {'result': 'ok'};
} else if (method == 'install_template') {
  response = {'result': '/tmp/din5008a/0.3.0'};
} else if (method == 'get_template_version') {
```

Neue Tests:

```dart
  test('checkFonts returns status', () async {
    final result = await engine.checkFonts();
    expect(result['installed'], isTrue);
    expect(result['missing'], isEmpty);
  });

  test('getTemplateVersion returns version string', () async {
    final version = await engine.getTemplateVersion();
    expect(version, equals('0.2.0'));
  });
```

- [ ] **Step 3: Tests + Commit**

```bash
cd flutter && flutter test
cd .. && git add flutter/
git commit -m "feat(flutter): add font/template management to MdoEngine"
```

---

### Task 3: Settings-Provider

**Files:**
- Create: `flutter/lib/providers/settings_provider.dart`

- [ ] **Step 1: Provider erstellen**

```dart
// flutter/lib/providers/settings_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mdo_app/providers/engine_provider.dart';

/// Provider für die installierte Template-Version.
final templateVersionProvider = FutureProvider<String?>((ref) async {
  final engine = ref.watch(engineProvider);
  if (engine == null) return null;
  return engine.getTemplateVersion();
});

/// Provider für den Font-Status.
final fontStatusProvider =
    FutureProvider<Map<String, dynamic>>((ref) async {
  final engine = ref.watch(engineProvider);
  if (engine == null) return {'installed': false, 'missing': []};
  return engine.checkFonts();
});
```

- [ ] **Step 2: Commit**

```bash
git add flutter/lib/providers/settings_provider.dart
git commit -m "feat(flutter): add settings providers for template and fonts"
```

---

### Task 4: Settings-Screen

**Files:**
- Create: `flutter/lib/screens/settings_screen.dart`

- [ ] **Step 1: Screen implementieren**

```dart
// flutter/lib/screens/settings_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mdo_app/providers/engine_provider.dart';
import 'package:mdo_app/providers/profile_provider.dart';
import 'package:mdo_app/providers/settings_provider.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final templateAsync = ref.watch(templateVersionProvider);
    final fontsAsync = ref.watch(fontStatusProvider);
    final profilesAsync = ref.watch(profileListProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Einstellungen')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Template-Sektion
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Typst-Template',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  templateAsync.when(
                    data: (version) => Text('Version: ${version ?? "nicht installiert"}'),
                    loading: () => const Text('Lade...'),
                    error: (e, _) => Text('Fehler: $e'),
                  ),
                  const SizedBox(height: 8),
                  ElevatedButton.icon(
                    onPressed: () => _updateTemplate(context, ref),
                    icon: const Icon(Icons.download),
                    label: const Text('Template aktualisieren'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),

          // Font-Sektion
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Schriftarten',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  fontsAsync.when(
                    data: (status) {
                      final installed = status['installed'] == true;
                      final missing = (status['missing'] as List?)?.cast<String>() ?? [];
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(
                                installed ? Icons.check_circle : Icons.warning,
                                color: installed ? Colors.green : Colors.orange,
                              ),
                              const SizedBox(width: 8),
                              Text(installed
                                  ? 'Alle Schriftarten installiert'
                                  : 'Fehlend: ${missing.join(", ")}'),
                            ],
                          ),
                          if (!installed) ...[
                            const SizedBox(height: 8),
                            ElevatedButton.icon(
                              onPressed: () => _installFonts(context, ref),
                              icon: const Icon(Icons.download),
                              label: const Text('Schriftarten installieren'),
                            ),
                          ],
                        ],
                      );
                    },
                    loading: () => const Text('Lade...'),
                    error: (e, _) => Text('Fehler: $e'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),

          // Profil-Sektion
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Profile',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  profilesAsync.when(
                    data: (profiles) => Text(
                        '${profiles.length} Profil${profiles.length == 1 ? "" : "e"} vorhanden'),
                    loading: () => const Text('Lade...'),
                    error: (e, _) => Text('Fehler: $e'),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _updateTemplate(BuildContext context, WidgetRef ref) async {
    final engine = ref.read(engineProvider);
    if (engine == null) return;

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Template wird aktualisiert...')),
    );

    try {
      final path = await engine.installTemplate();
      ref.invalidate(templateVersionProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Template installiert: $path')),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fehler: $e')),
        );
      }
    }
  }

  Future<void> _installFonts(BuildContext context, WidgetRef ref) async {
    final engine = ref.read(engineProvider);
    if (engine == null) return;

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Schriftarten werden installiert...')),
    );

    try {
      await engine.installFonts();
      ref.invalidate(fontStatusProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Schriftarten installiert')),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fehler: $e')),
        );
      }
    }
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add flutter/lib/screens/settings_screen.dart
git commit -m "feat(flutter): add settings screen with template/font management"
```

---

### Task 5: Route + Navigation verdrahten

**Files:**
- Modify: `flutter/lib/app.dart` — Route `/settings` hinzufügen
- Modify: `flutter/lib/screens/letter_list_screen.dart` — Settings-Icon in AppBar

- [ ] **Step 1: Route hinzufügen**

In `flutter/lib/app.dart` — neuer Import und Route:

```dart
import 'package:mdo_app/screens/settings_screen.dart';

// In routes-Liste:
    GoRoute(
      path: '/settings',
      builder: (context, state) => const SettingsScreen(),
    ),
```

- [ ] **Step 2: Settings-Icon in Brief-Liste**

In `flutter/lib/screens/letter_list_screen.dart` — neues Icon in AppBar actions:

```dart
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: 'Einstellungen',
            onPressed: () => context.push('/settings'),
          ),
```

- [ ] **Step 3: Tests + Commit**

```bash
cd flutter && flutter test && flutter analyze
cd .. && git add flutter/
git commit -m "feat(flutter): wire up settings screen in navigation"
```

---

### Task 6: End-to-End-Verifikation

- [ ] **Step 1: Python-Tests**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest tests/ -v
```

- [ ] **Step 2: Flutter-Tests**

```bash
cd flutter && flutter test && flutter analyze
```

- [ ] **Step 3: Lint**

```bash
uv run ruff check src/ tests/ && uv run mypy src/
```

---

## Zusammenfassung

| Task | Was |
|------|-----|
| 1 | Server: check_fonts, install_fonts, install_template |
| 2 | MdoEngine: checkFonts, installFonts, installTemplate |
| 3 | Settings-Provider (template version, font status) |
| 4 | Settings-Screen |
| 5 | Route + Navigation |
| 6 | End-to-End-Verifikation |
