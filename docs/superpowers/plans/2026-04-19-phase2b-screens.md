# Phase 2b: Screens — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Alle Kern-Screens der Flutter-App implementieren: Profil-Verwaltung, Brief-Editor, Kompilierung und PDF-Vorschau.

**Architecture:** Zuerst wird das Python-Backend um Letter-CRUD erweitert (Briefe speichern/laden/auflisten unter `~/.mdo/letters/`). Dann werden die Flutter-Screens gebaut: Profile (Liste + Formular), Brief-Editor (Metadaten-Formular + Markdown-Textfeld), Kompilierung, PDF-Vorschau. Jeder Screen ist ein eigenes Dart-File und kommuniziert über Riverpod-Provider mit dem Python-Backend.

**Tech Stack:** Python 3.12 (core/letter.py), Flutter/Dart, Riverpod 3.x, GoRouter 17.x, pdfrx (PDF-Viewer)

---

## File Structure

### New Python Files

| File | Responsibility |
|------|---------------|
| `src/mdo/core/letter.py` | Letter-CRUD: save/load/list/delete `.md`-Dateien |
| `tests/test_letter.py` | Tests für Letter-CRUD |

### Modified Python Files

| File | Responsibility |
|------|---------------|
| `src/mdo/core/server.py` | Neue Methoden: `save_letter`, `load_letter`, `list_letters`, `delete_letter` |
| `src/mdo/core/paths.py` | Neue Funktion: `letters_dir()` |

### New Flutter Files

| File | Responsibility |
|------|---------------|
| `flutter/lib/screens/profile_list_screen.dart` | Profil-Liste mit Erstellen/Löschen |
| `flutter/lib/screens/profile_form_screen.dart` | Profil-Formular (Erstellen + Bearbeiten) |
| `flutter/lib/screens/letter_list_screen.dart` | Brief-Liste (Home-Ersatz) |
| `flutter/lib/screens/letter_editor_screen.dart` | Brief-Editor (Metadaten + Markdown) |
| `flutter/lib/screens/pdf_preview_screen.dart` | PDF-Vorschau |
| `flutter/lib/providers/letter_provider.dart` | Riverpod-Provider für Briefe |
| `flutter/lib/engine/mdo_engine.dart` | Erweitert: Letter-Methoden |

### Modified Flutter Files

| File | Responsibility |
|------|---------------|
| `flutter/lib/app.dart` | Neue Routen |
| `flutter/lib/screens/home_screen.dart` | Wird durch `letter_list_screen.dart` ersetzt |

---

### Task 1: Python Letter-CRUD (`core/letter.py`)

**Files:**
- Modify: `src/mdo/core/paths.py` — `letters_dir()` hinzufügen
- Create: `src/mdo/core/letter.py`
- Create: `tests/test_letter.py`

- [ ] **Step 1: `letters_dir()` zu paths.py hinzufügen**

In `src/mdo/core/paths.py`:

```python
def letters_dir() -> Path:
    """Return the letters directory (~/.mdo/letters/)."""
    return mdo_base_dir() / "letters"
```

- [ ] **Step 2: Failing Tests schreiben**

```python
# tests/test_letter.py
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from mdo.core.letter import delete_letter, list_letters, load_letter, save_letter


@pytest.fixture
def letters_path(tmp_path: Path) -> Path:
    d = tmp_path / ".mdo" / "letters"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def _mock_letters_dir(letters_path: Path):  # type: ignore[no-untyped-def]
    with patch("mdo.core.letter.letters_dir", return_value=letters_path):
        yield


SAMPLE_FRONTMATTER: dict[str, object] = {
    "name": "Max Mustermann",
    "street": "Musterstrasse 1",
    "zip": "12345",
    "city": "Musterstadt",
    "phone": "",
    "email": "",
    "iban": "",
    "bic": "",
    "bank": "",
    "qr_code": True,
    "signature": True,
    "closing": "Mit freundlichem Gruß",
    "date": None,
    "subject": "Testbetreff",
    "recipient": ["Firma GmbH", "Strasse 1", "12345 Stadt"],
    "attachments": [],
}

SAMPLE_BODY = "Sehr geehrte Damen und Herren,\n\ndies ist ein Test."


@pytest.mark.usefixtures("_mock_letters_dir")
class TestSaveLetter:
    def test_save_creates_file(self, letters_path: Path) -> None:
        path = save_letter(SAMPLE_FRONTMATTER, SAMPLE_BODY)
        assert path.exists()
        assert path.suffix == ".md"
        content = path.read_text()
        assert "---" in content
        assert "Testbetreff" in content
        assert "dies ist ein Test" in content

    def test_save_with_custom_filename(self, letters_path: Path) -> None:
        path = save_letter(SAMPLE_FRONTMATTER, SAMPLE_BODY, filename="mein_brief.md")
        assert path.name == "mein_brief.md"

    def test_save_overwrites_existing(self, letters_path: Path) -> None:
        save_letter(SAMPLE_FRONTMATTER, SAMPLE_BODY, filename="brief.md")
        path = save_letter(
            {**SAMPLE_FRONTMATTER, "subject": "Neuer Betreff"},
            "Neuer Text.",
            filename="brief.md",
        )
        content = path.read_text()
        assert "Neuer Betreff" in content


@pytest.mark.usefixtures("_mock_letters_dir")
class TestLoadLetter:
    def test_load_existing(self, letters_path: Path) -> None:
        save_letter(SAMPLE_FRONTMATTER, SAMPLE_BODY, filename="test.md")
        fm, body = load_letter("test.md")
        assert fm["subject"] == "Testbetreff"
        assert "dies ist ein Test" in body

    def test_load_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_letter("nonexistent.md")


@pytest.mark.usefixtures("_mock_letters_dir")
class TestListLetters:
    def test_list_empty(self) -> None:
        assert list_letters() == []

    def test_list_returns_md_files(self, letters_path: Path) -> None:
        save_letter(SAMPLE_FRONTMATTER, SAMPLE_BODY, filename="brief1.md")
        save_letter(SAMPLE_FRONTMATTER, SAMPLE_BODY, filename="brief2.md")
        names = list_letters()
        assert sorted(names) == ["brief1.md", "brief2.md"]

    def test_list_ignores_non_md(self, letters_path: Path) -> None:
        (letters_path / "notes.txt").write_text("not a letter")
        assert list_letters() == []


@pytest.mark.usefixtures("_mock_letters_dir")
class TestDeleteLetter:
    def test_delete_existing(self, letters_path: Path) -> None:
        save_letter(SAMPLE_FRONTMATTER, SAMPLE_BODY, filename="temp.md")
        delete_letter("temp.md")
        assert not (letters_path / "temp.md").exists()

    def test_delete_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            delete_letter("nonexistent.md")
```

- [ ] **Step 3: Implementierung**

```python
# src/mdo/core/letter.py
"""Letter CRUD operations for the Flutter app."""

import logging
from pathlib import Path

import yaml

from mdo.core.paths import letters_dir

logger = logging.getLogger(__name__)


def _build_frontmatter(data: dict[str, object]) -> str:
    """Serialize frontmatter dict to YAML string between --- markers."""
    lines: list[str] = ["---"]
    for key, value in data.items():
        if value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif isinstance(value, str) and value.startswith("#"):
            lines.append(f'{key}: "{value}"')
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def save_letter(
    frontmatter: dict[str, object],
    body: str,
    filename: str | None = None,
) -> Path:
    """Save a letter as .md file to ~/.mdo/letters/."""
    target_dir = letters_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        import datetime
        today = datetime.date.today().isoformat()
        counter = 1
        while True:
            filename = f"{today}_Brief{counter:02d}.md"
            if not (target_dir / filename).exists():
                break
            counter += 1

    path = target_dir / filename
    fm_text = _build_frontmatter(frontmatter)
    content = f"{fm_text}\n\n{body}\n"
    path.write_text(content, encoding="utf-8")
    logger.debug("Letter saved to %s", path)
    return path


def load_letter(filename: str) -> tuple[dict[str, object], str]:
    """Load a letter from ~/.mdo/letters/. Returns (frontmatter, body)."""
    path = letters_dir() / filename
    if not path.exists():
        msg = f"Letter not found: {path}"
        raise FileNotFoundError(msg)

    content = path.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) < 3:
        msg = f"Invalid frontmatter in {filename}"
        raise ValueError(msg)

    fm: dict[str, object] = yaml.safe_load(parts[1])
    body = parts[2].strip()
    return fm, body


def list_letters() -> list[str]:
    """Return all letter filenames in ~/.mdo/letters/."""
    target_dir = letters_dir()
    if not target_dir.exists():
        return []
    return sorted(p.name for p in target_dir.glob("*.md"))


def delete_letter(filename: str) -> None:
    """Delete a letter from ~/.mdo/letters/."""
    path = letters_dir() / filename
    if not path.exists():
        msg = f"Letter not found: {path}"
        raise FileNotFoundError(msg)
    path.unlink()
    logger.debug("Letter deleted: %s", path)
```

- [ ] **Step 4: Tests ausführen**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest tests/test_letter.py -v`
Expected: PASS

- [ ] **Step 5: Lint + Type-Check + Alle Tests**

Run: `cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest -v && uv run ruff check src/ tests/ && uv run mypy src/`

- [ ] **Step 6: Commit**

```bash
git add src/mdo/core/letter.py src/mdo/core/paths.py tests/test_letter.py
git commit -m "feat(core): add letter CRUD module for Flutter app"
```

---

### Task 2: Server um Letter-Methoden erweitern

**Files:**
- Modify: `src/mdo/core/server.py`
- Modify: `tests/test_server.py`

- [ ] **Step 1: Failing Tests**

```python
# Append to tests/test_server.py

@patch("mdo.core.server.core_save_letter")
def test_save_letter(mock_save, server):
    from pathlib import Path
    mock_save.return_value = Path("/tmp/.mdo/letters/brief.md")
    result = _post(server, "save_letter", {
        "frontmatter": {"subject": "Test", "recipient": ["Firma"]},
        "body": "Hallo Welt",
    })
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
```

- [ ] **Step 2: Server erweitern**

In `src/mdo/core/server.py` — neue Imports und Handler:

```python
from mdo.core.letter import (
    delete_letter as core_delete_letter,
    list_letters as core_list_letters,
    load_letter as core_load_letter,
    save_letter as core_save_letter,
)


def _handle_save_letter(params: dict[str, object]) -> str:
    fm = params.get("frontmatter", {})
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
```

Und in `METHODS` hinzufügen:

```python
    "save_letter": _handle_save_letter,
    "load_letter": _handle_load_letter,
    "list_letters": _handle_list_letters,
    "delete_letter": _handle_delete_letter,
```

- [ ] **Step 3: Tests + Lint + Commit**

```bash
uv run pytest -v && uv run ruff check src/ tests/ && uv run mypy src/
git add src/mdo/core/server.py tests/test_server.py
git commit -m "feat(core): add letter CRUD methods to server"
```

---

### Task 3: MdoEngine um Letter-Methoden erweitern

**Files:**
- Modify: `flutter/lib/engine/mdo_engine.dart`
- Modify: `flutter/test/engine/mdo_engine_test.dart`

- [ ] **Step 1: Methoden zu MdoEngine hinzufügen**

```dart
// In mdo_engine.dart — neue Methoden am Ende der Klasse

  /// Speichert einen Brief.
  Future<String> saveLetter({
    required Map<String, dynamic> frontmatter,
    required String body,
    String? filename,
  }) async {
    final result = await call('save_letter', {
      'frontmatter': frontmatter,
      'body': body,
      if (filename != null) 'filename': filename,
    });
    return result as String;
  }

  /// Lädt einen Brief.
  Future<Map<String, dynamic>> loadLetter(String filename) async {
    final result = await call('load_letter', {'filename': filename});
    return result as Map<String, dynamic>;
  }

  /// Listet alle Briefe auf.
  Future<List<String>> listLetters() async {
    final result = await call('list_letters', {});
    return (result as List).cast<String>();
  }

  /// Löscht einen Brief.
  Future<void> deleteLetter(String filename) async {
    await call('delete_letter', {'filename': filename});
  }
```

- [ ] **Step 2: Tests erweitern**

Im Mock-Server in `mdo_engine_test.dart` — neue Methoden-Handler:

```dart
} else if (method == 'list_letters') {
  response = {
    'result': ['brief1.md', 'brief2.md']
  };
} else if (method == 'save_letter') {
  response = {'result': '/tmp/brief.md'};
} else if (method == 'load_letter') {
  response = {
    'result': {
      'frontmatter': {'subject': 'Test'},
      'body': 'Hallo Welt',
    }
  };
} else if (method == 'delete_letter') {
  response = {'result': 'ok'};
}
```

Neue Tests:

```dart
  test('listLetters returns filenames', () async {
    final letters = await engine.listLetters();
    expect(letters, equals(['brief1.md', 'brief2.md']));
  });

  test('saveLetter returns path', () async {
    final path = await engine.saveLetter(
      frontmatter: {'subject': 'Test'},
      body: 'Hallo Welt',
    );
    expect(path, contains('brief.md'));
  });

  test('loadLetter returns frontmatter and body', () async {
    final result = await engine.loadLetter('brief.md');
    expect(result['frontmatter']['subject'], equals('Test'));
    expect(result['body'], equals('Hallo Welt'));
  });
```

- [ ] **Step 3: Tests + Commit**

```bash
cd flutter && flutter test
git add flutter/lib/engine/ flutter/test/engine/
git commit -m "feat(flutter): add letter CRUD methods to MdoEngine"
```

---

### Task 4: Letter-Provider + Profile-Provider erweitern

**Files:**
- Create: `flutter/lib/providers/letter_provider.dart`
- Modify: `flutter/lib/providers/profile_provider.dart`

- [ ] **Step 1: Letter-Provider**

```dart
// flutter/lib/providers/letter_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mdo_app/providers/engine_provider.dart';

/// Provider für die Liste der Brief-Dateinamen.
final letterListProvider = FutureProvider<List<String>>((ref) async {
  final engine = ref.watch(engineProvider);
  if (engine == null) return [];
  return engine.listLetters();
});
```

- [ ] **Step 2: Profile-Provider um Load erweitern**

```dart
// flutter/lib/providers/profile_provider.dart — erweitern
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mdo_app/providers/engine_provider.dart';

/// Provider für die Liste der Profilnamen.
final profileListProvider = FutureProvider<List<String>>((ref) async {
  final engine = ref.watch(engineProvider);
  if (engine == null) return [];
  return engine.listProfiles();
});

/// Provider für ein einzelnes Profil (parametrisiert).
final profileProvider =
    FutureProvider.family<Map<String, dynamic>, String>((ref, name) async {
  final engine = ref.watch(engineProvider);
  if (engine == null) return {};
  return engine.loadProfile(name);
});
```

- [ ] **Step 3: Commit**

```bash
git add flutter/lib/providers/
git commit -m "feat(flutter): add letter and profile providers"
```

---

### Task 5: Profil-Liste Screen

**Files:**
- Create: `flutter/lib/screens/profile_list_screen.dart`

- [ ] **Step 1: Screen implementieren**

```dart
// flutter/lib/screens/profile_list_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mdo_app/providers/engine_provider.dart';
import 'package:mdo_app/providers/profile_provider.dart';

class ProfileListScreen extends ConsumerWidget {
  const ProfileListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profilesAsync = ref.watch(profileListProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/profile/create'),
        child: const Icon(Icons.add),
      ),
      body: profilesAsync.when(
        data: (profiles) {
          if (profiles.isEmpty) {
            return const Center(
              child: Text('Keine Profile vorhanden.\nErstelle ein neues Profil.'),
            );
          }
          return ListView.builder(
            itemCount: profiles.length,
            itemBuilder: (context, index) {
              final name = profiles[index];
              return ListTile(
                leading: const Icon(Icons.person),
                title: Text(name),
                trailing: name != 'default'
                    ? IconButton(
                        icon: const Icon(Icons.delete),
                        onPressed: () async {
                          final engine = ref.read(engineProvider);
                          if (engine == null) return;
                          try {
                            await engine.call('delete_profile', {'name': name});
                            ref.invalidate(profileListProvider);
                          } catch (e) {
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text('Fehler: $e')),
                              );
                            }
                          }
                        },
                      )
                    : null,
                onTap: () => context.push('/profile/edit/$name'),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Fehler: $e')),
      ),
    );
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add flutter/lib/screens/profile_list_screen.dart
git commit -m "feat(flutter): add profile list screen"
```

---

### Task 6: Profil-Formular Screen

**Files:**
- Create: `flutter/lib/screens/profile_form_screen.dart`

- [ ] **Step 1: Screen implementieren**

```dart
// flutter/lib/screens/profile_form_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mdo_app/providers/engine_provider.dart';
import 'package:mdo_app/providers/profile_provider.dart';

class ProfileFormScreen extends ConsumerStatefulWidget {
  final String? profileName; // null = create, non-null = edit

  const ProfileFormScreen({super.key, this.profileName});

  @override
  ConsumerState<ProfileFormScreen> createState() => _ProfileFormScreenState();
}

class _ProfileFormScreenState extends ConsumerState<ProfileFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _controllers = <String, TextEditingController>{};
  bool _qrCode = false;
  bool _signature = true;
  bool _loading = true;
  bool _saving = false;

  static const _fields = [
    ('name', 'Name'),
    ('street', 'Strasse'),
    ('zip', 'PLZ'),
    ('city', 'Ort'),
    ('phone', 'Telefon'),
    ('email', 'E-Mail'),
    ('iban', 'IBAN'),
    ('bic', 'BIC'),
    ('bank', 'Bank'),
    ('accent', 'Akzentfarbe (Hex)'),
    ('closing', 'Schlussgruss'),
  ];

  @override
  void initState() {
    super.initState();
    for (final (key, _) in _fields) {
      _controllers[key] = TextEditingController();
    }
    _controllers['closing']!.text = 'Mit freundlichem Gruß';
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    if (widget.profileName == null) {
      setState(() => _loading = false);
      return;
    }
    final engine = ref.read(engineProvider);
    if (engine == null) return;
    try {
      final data = await engine.loadProfile(widget.profileName!);
      for (final (key, _) in _fields) {
        final value = data[key];
        if (value != null) _controllers[key]!.text = value.toString();
      }
      setState(() {
        _qrCode = data['qr_code'] == true;
        _signature = data['signature'] != false;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);

    final engine = ref.read(engineProvider);
    if (engine == null) return;

    final data = <String, dynamic>{};
    for (final (key, _) in _fields) {
      final text = _controllers[key]!.text;
      if (key == 'accent' && text.isEmpty) {
        data[key] = null;
      } else {
        data[key] = text;
      }
    }
    data['qr_code'] = _qrCode;
    data['signature'] = _signature;
    data['open'] = true;
    data['reveal'] = true;

    try {
      final name = widget.profileName ?? 'default';
      await engine.call('save_profile', {'name': name, 'data': data});
      ref.invalidate(profileListProvider);
      if (mounted) context.pop();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fehler: $e')),
        );
      }
    } finally {
      setState(() => _saving = false);
    }
  }

  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isEdit = widget.profileName != null;

    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: Text(isEdit ? 'Profil bearbeiten' : 'Neues Profil')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(isEdit ? 'Profil bearbeiten' : 'Neues Profil'),
        actions: [
          if (_saving)
            const Padding(
              padding: EdgeInsets.all(16),
              child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)),
            )
          else
            IconButton(onPressed: _save, icon: const Icon(Icons.save)),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            for (final (key, label) in _fields)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: TextFormField(
                  controller: _controllers[key],
                  decoration: InputDecoration(
                    labelText: label,
                    border: const OutlineInputBorder(),
                  ),
                  validator: (key == 'name' || key == 'street' || key == 'zip' || key == 'city')
                      ? (v) => (v == null || v.isEmpty) ? 'Pflichtfeld' : null
                      : null,
                ),
              ),
            SwitchListTile(
              title: const Text('vCard QR-Code'),
              value: _qrCode,
              onChanged: (v) => setState(() => _qrCode = v),
            ),
            SwitchListTile(
              title: const Text('Unterschrift'),
              value: _signature,
              onChanged: (v) => setState(() => _signature = v),
            ),
          ],
        ),
      ),
    );
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add flutter/lib/screens/profile_form_screen.dart
git commit -m "feat(flutter): add profile form screen (create + edit)"
```

---

### Task 7: Brief-Liste Screen

**Files:**
- Create: `flutter/lib/screens/letter_list_screen.dart`
- Delete: `flutter/lib/screens/home_screen.dart` (wird ersetzt)

- [ ] **Step 1: Screen implementieren**

```dart
// flutter/lib/screens/letter_list_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mdo_app/providers/engine_provider.dart';
import 'package:mdo_app/providers/letter_provider.dart';

class LetterListScreen extends ConsumerWidget {
  const LetterListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final engine = ref.watch(engineProvider);
    final lettersAsync = ref.watch(letterListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('mdo'),
        actions: [
          IconButton(
            icon: const Icon(Icons.person),
            tooltip: 'Profile',
            onPressed: () => context.push('/profiles'),
          ),
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: Icon(
              engine != null ? Icons.check_circle : Icons.error,
              color: engine != null ? Colors.green : Colors.red,
              size: 16,
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/letter/new'),
        child: const Icon(Icons.add),
      ),
      body: lettersAsync.when(
        data: (letters) {
          if (letters.isEmpty) {
            return const Center(
              child: Text('Keine Briefe vorhanden.\nErstelle einen neuen Brief.'),
            );
          }
          return ListView.builder(
            itemCount: letters.length,
            itemBuilder: (context, index) {
              final filename = letters[index];
              return ListTile(
                leading: const Icon(Icons.mail),
                title: Text(filename),
                trailing: IconButton(
                  icon: const Icon(Icons.delete),
                  onPressed: () async {
                    if (engine == null) return;
                    try {
                      await engine.deleteLetter(filename);
                      ref.invalidate(letterListProvider);
                    } catch (e) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text('Fehler: $e')),
                        );
                      }
                    }
                  },
                ),
                onTap: () => context.push('/letter/edit/$filename'),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Fehler: $e')),
      ),
    );
  }
}
```

- [ ] **Step 2: home_screen.dart löschen**

```bash
rm flutter/lib/screens/home_screen.dart
```

- [ ] **Step 3: Commit**

```bash
git add flutter/lib/screens/
git commit -m "feat(flutter): add letter list screen, replace home screen"
```

---

### Task 8: Brief-Editor Screen

**Files:**
- Create: `flutter/lib/screens/letter_editor_screen.dart`

- [ ] **Step 1: Screen implementieren**

```dart
// flutter/lib/screens/letter_editor_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mdo_app/providers/engine_provider.dart';
import 'package:mdo_app/providers/letter_provider.dart';
import 'package:mdo_app/providers/profile_provider.dart';

class LetterEditorScreen extends ConsumerStatefulWidget {
  final String? filename; // null = new letter, non-null = edit

  const LetterEditorScreen({super.key, this.filename});

  @override
  ConsumerState<LetterEditorScreen> createState() => _LetterEditorScreenState();
}

class _LetterEditorScreenState extends ConsumerState<LetterEditorScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final _subjectController = TextEditingController();
  final _recipientController = TextEditingController();
  final _bodyController = TextEditingController();
  final _attachmentsController = TextEditingController();
  DateTime? _date;
  String _selectedProfile = 'default';
  bool _loading = true;
  Map<String, dynamic> _profileData = {};

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _date = DateTime.now();
    _loadData();
  }

  Future<void> _loadData() async {
    final engine = ref.read(engineProvider);
    if (engine == null) return;

    try {
      // Profil laden
      final profiles = await engine.listProfiles();
      if (profiles.isNotEmpty) {
        _selectedProfile = profiles.first;
        _profileData = await engine.loadProfile(_selectedProfile);
      }

      // Brief laden falls Edit-Modus
      if (widget.filename != null) {
        final data = await engine.loadLetter(widget.filename!);
        final fm = data['frontmatter'] as Map<String, dynamic>;
        _subjectController.text = fm['subject']?.toString() ?? '';
        final recipients = fm['recipient'] as List? ?? [];
        _recipientController.text = recipients.join('\n');
        _bodyController.text = data['body']?.toString() ?? '';
        final attachments = fm['attachments'] as List? ?? [];
        _attachmentsController.text = attachments.join('\n');
        if (fm['date'] != null) {
          // Deutsches Datum parsen ist komplex — belassen als String
        }
      } else {
        _recipientController.text = 'Firma/Amt\nVorname Nachname\nStrasse 1\n12345 Stadt';
      }
    } catch (e) {
      // Fehler ignorieren, leere Felder anzeigen
    }
    setState(() => _loading = false);
  }

  Future<void> _save() async {
    final engine = ref.read(engineProvider);
    if (engine == null) return;

    final frontmatter = <String, dynamic>{
      ..._profileData,
      'subject': _subjectController.text.isEmpty ? null : _subjectController.text,
      'date': null, // null = heute
      'recipient': _recipientController.text
          .split('\n')
          .where((l) => l.trim().isNotEmpty)
          .toList(),
      'attachments': _attachmentsController.text
          .split('\n')
          .where((l) => l.trim().isNotEmpty)
          .toList(),
    };

    try {
      await engine.saveLetter(
        frontmatter: frontmatter,
        body: _bodyController.text,
        filename: widget.filename,
      );
      ref.invalidate(letterListProvider);
      if (mounted) context.pop();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fehler: $e')),
        );
      }
    }
  }

  Future<void> _compile() async {
    final engine = ref.read(engineProvider);
    if (engine == null) return;

    // Erst speichern
    await _save();

    // Dann kompilieren
    // TODO: filename aus save_letter Rückgabe verwenden
  }

  @override
  void dispose() {
    _tabController.dispose();
    _subjectController.dispose();
    _recipientController.dispose();
    _bodyController.dispose();
    _attachmentsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isEdit = widget.filename != null;

    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: Text(isEdit ? 'Brief bearbeiten' : 'Neuer Brief')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(isEdit ? 'Brief bearbeiten' : 'Neuer Brief'),
        actions: [
          IconButton(
            icon: const Icon(Icons.save),
            tooltip: 'Speichern',
            onPressed: _save,
          ),
          IconButton(
            icon: const Icon(Icons.picture_as_pdf),
            tooltip: 'Kompilieren',
            onPressed: _compile,
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Metadaten'),
            Tab(text: 'Brieftext'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // Tab 1: Metadaten
          ListView(
            padding: const EdgeInsets.all(16),
            children: [
              TextFormField(
                controller: _subjectController,
                decoration: const InputDecoration(
                  labelText: 'Betreff',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _recipientController,
                maxLines: 5,
                decoration: const InputDecoration(
                  labelText: 'Empfänger (eine Zeile pro Adresszeile)',
                  border: OutlineInputBorder(),
                  alignLabelWithHint: true,
                ),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _attachmentsController,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Anlagen (eine pro Zeile, optional)',
                  border: OutlineInputBorder(),
                  alignLabelWithHint: true,
                ),
              ),
            ],
          ),
          // Tab 2: Brieftext (Markdown)
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextFormField(
              controller: _bodyController,
              maxLines: null,
              expands: true,
              textAlignVertical: TextAlignVertical.top,
              style: const TextStyle(fontFamily: 'monospace'),
              decoration: const InputDecoration(
                hintText: 'Sehr geehrte Damen und Herren,\n\n...',
                border: OutlineInputBorder(),
                alignLabelWithHint: true,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add flutter/lib/screens/letter_editor_screen.dart
git commit -m "feat(flutter): add letter editor screen with metadata + markdown tabs"
```

---

### Task 9: PDF-Vorschau Screen

**Files:**
- Create: `flutter/lib/screens/pdf_preview_screen.dart`

- [ ] **Step 1: Screen implementieren**

```dart
// flutter/lib/screens/pdf_preview_screen.dart
import 'package:flutter/material.dart';
import 'package:pdfrx/pdfrx.dart';

class PdfPreviewScreen extends StatelessWidget {
  final String pdfPath;

  const PdfPreviewScreen({super.key, required this.pdfPath});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('PDF-Vorschau'),
      ),
      body: PdfViewer.file(
        pdfPath,
        params: const PdfViewerParams(
          enableTextSelection: true,
        ),
      ),
    );
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add flutter/lib/screens/pdf_preview_screen.dart
git commit -m "feat(flutter): add PDF preview screen"
```

---

### Task 10: GoRouter — alle Routen verdrahten

**Files:**
- Modify: `flutter/lib/app.dart`

- [ ] **Step 1: Routen aktualisieren**

```dart
// flutter/lib/app.dart
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:mdo_app/screens/letter_editor_screen.dart';
import 'package:mdo_app/screens/letter_list_screen.dart';
import 'package:mdo_app/screens/pdf_preview_screen.dart';
import 'package:mdo_app/screens/profile_form_screen.dart';
import 'package:mdo_app/screens/profile_list_screen.dart';

final router = GoRouter(
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const LetterListScreen(),
    ),
    GoRoute(
      path: '/profiles',
      builder: (context, state) => const ProfileListScreen(),
    ),
    GoRoute(
      path: '/profile/create',
      builder: (context, state) => const ProfileFormScreen(),
    ),
    GoRoute(
      path: '/profile/edit/:name',
      builder: (context, state) => ProfileFormScreen(
        profileName: state.pathParameters['name'],
      ),
    ),
    GoRoute(
      path: '/letter/new',
      builder: (context, state) => const LetterEditorScreen(),
    ),
    GoRoute(
      path: '/letter/edit/:filename',
      builder: (context, state) => LetterEditorScreen(
        filename: state.pathParameters['filename'],
      ),
    ),
    GoRoute(
      path: '/pdf/:path',
      builder: (context, state) => PdfPreviewScreen(
        pdfPath: Uri.decodeComponent(state.pathParameters['path'] ?? ''),
      ),
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

- [ ] **Step 2: main.dart — import updaten**

In `flutter/lib/main.dart` — der Import von `home_screen.dart` wird nicht mehr gebraucht (wurde bereits über `app.dart` → `LetterListScreen` ersetzt).

- [ ] **Step 3: Tests + Commit**

```bash
cd flutter && flutter test
cd .. && git add flutter/
git commit -m "feat(flutter): wire up all routes with GoRouter"
```

---

### Task 11: End-to-End-Verifikation

- [ ] **Step 1: Python-Tests**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli && uv run pytest tests/ -v
```

Expected: alle Tests bestehen

- [ ] **Step 2: Flutter-Tests**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli/flutter && flutter test
```

Expected: alle Tests bestehen

- [ ] **Step 3: Lint**

```bash
uv run ruff check src/ tests/ && uv run mypy src/
cd flutter && flutter analyze
```

- [ ] **Step 4: Manueller Test**

```bash
cd /Users/rolandkreus/GitHub/mdo-cli/flutter && flutter run -d macos
```

Manuell prüfen:
1. App startet, Briefe-Liste erscheint
2. Profil-Icon → Profil-Liste → Profil erstellen
3. Zurück → Neuer Brief (+) → Metadaten ausfüllen → Brieftext schreiben → Speichern
4. Brief erscheint in Liste → Antippen → Brief bearbeiten

---

## Zusammenfassung

| Task | Was | Dateien |
|------|-----|---------|
| 1 | Python Letter-CRUD | `core/letter.py`, `tests/test_letter.py` |
| 2 | Server Letter-Methoden | `core/server.py` |
| 3 | MdoEngine Letter-Methoden | `mdo_engine.dart` |
| 4 | Letter + Profile Provider | `letter_provider.dart`, `profile_provider.dart` |
| 5 | Profil-Liste Screen | `profile_list_screen.dart` |
| 6 | Profil-Formular Screen | `profile_form_screen.dart` |
| 7 | Brief-Liste Screen | `letter_list_screen.dart` |
| 8 | Brief-Editor Screen | `letter_editor_screen.dart` |
| 9 | PDF-Vorschau Screen | `pdf_preview_screen.dart` |
| 10 | GoRouter verdrahten | `app.dart` |
| 11 | End-to-End-Verifikation | — |
