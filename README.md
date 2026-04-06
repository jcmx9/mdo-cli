# mdo

A minimal CLI to generate DIN 5008 Form A business letters as PDF/A from Markdown.

Uses [Typst](https://typst.app) and the [din5008a](https://github.com/jcmx9/typst-DIN5008a) template.

## Prerequisites

Install via [Homebrew](https://brew.sh):

```bash
# Python
brew install python

# uv (Python package manager)
brew install uv

# Typst (document compiler)
brew install typst

# Pandoc (document converter)
brew install pandoc
```

### din5008a Template

Install or update the Typst template with:

```bash
mdo update
```

Or manually:

```bash
git clone https://github.com/jcmx9/typst-DIN5008a.git
mkdir -p ~/.local/share/typst/packages/local/din5008a/0.1.1
cp -r typst-DIN5008a/src ~/.local/share/typst/packages/local/din5008a/0.1.1/
cp typst-DIN5008a/typst.toml ~/.local/share/typst/packages/local/din5008a/0.1.1/
```

## Installation

```bash
uv tool install git+https://github.com/jcmx9/mdo-cli.git
```

## Quick Start

```bash
# 1. Install the Typst template
mdo update

# 2. Create a sender profile (interactive wizard)
mdo profile
```

The wizard prompts for name, address, contact, bank details, accent color, and more.
Result: `profile.yaml` in the current directory.

```yaml
# profile.yaml (example)
name: Max Mustermann
street: Musterstrasse 1
zip: 12345
city: Musterstadt
phone: 0123 456789
email: max@example.de
iban: DE89 3704 0044 0532 0130 00
bic: COBADEFFXXX
bank: Commerzbank
accent: "#B03060"
qr_code: true
signature: unterschrift.svg
closing: Mit freundlichem Gruss
open: true
reveal: true
```

```bash
# 3. Create a new letter
mdo new
```

Generates a `.md` file (e.g. `2026-04-06_Brief01.md`) with frontmatter from your profile:

```markdown
---
name: Max Mustermann
street: Musterstrasse 1
zip: 12345
city: Musterstadt
...
date: null  # YYYY-MM-DD (null = today)
subject: null
recipient:
  - Firma GmbH
  - Frau / Herrn Vorname Nachname
  - Strasse Nr.
  - PLZ Ort
attachments: []
---

Sehr geehrte Damen und Herren,


```

Edit the file: fill in `subject`, `recipient`, `date`, `attachments`, and write your letter body in Markdown.

```bash
# 4. Compile to PDF/A
mdo compile 2026-04-06_Brief01.md
```

Pipeline: Markdown body → Pandoc → Typst markup, frontmatter → JSON, both combined with din5008a template → PDF/A-2b.

## Printing

> **Always print with 100% scaling (no fit-to-page).** The DIN 5008 layout requires exact measurements for fold marks, address fields, and margins. Scaling will break the layout.

## Commands

### `mdo profile`

Interactive wizard to create `profile.yaml` in the current directory.

### `mdo new [FILENAME]`

Creates a letter `.md` with frontmatter from `profile.yaml`. Without `FILENAME`, auto-generates `YYYY-MM-DD_BriefCC.md` (collision-safe counter).

### `mdo compile FILENAME.md`

Compiles a letter `.md` to PDF/A-2b via Pandoc and Typst. Checks for required fonts before compilation.

### `mdo update`

Downloads/updates the din5008a Typst template to the local packages directory.

## Field Reference

### profile.yaml

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Sender name |
| `street` | string | Street address |
| `zip` | string | Postal code |
| `city` | string | City |
| `phone` | string | Phone number |
| `email` | string | Email address |
| `iban` | string | Bank IBAN |
| `bic` | string | Bank BIC |
| `bank` | string | Bank name |
| `qr_code` | boolean | Show vCard QR code |
| `signature` | string/null | Signature filename (e.g. `unterschrift.svg`) |
| `closing` | string | Closing line (e.g. "Mit freundlichem Gruss") |
| `accent` | string | Accent color as hex (e.g. `"#B03060"`) |
| `open` | boolean | Open PDF after compile |
| `reveal` | boolean | Reveal PDF in file manager after compile |

### Letter .md (additional fields)

| Field | Type | Description |
|-------|------|-------------|
| `date` | string/null | Letter date (`null` = today, format: `YYYY-MM-DD`) |
| `subject` | string | Subject line |
| `recipient` | list | Recipient address lines |
| `attachments` | list | Attachment descriptions (rendered at end of letter) |

### Signature

Place the signature image in the same directory as the letter. Supported formats: SVG, PNG, GIF, JPG. SVG or transparent PNG recommended.

## License

[MIT](LICENSE)

---

# mdo (Deutsch)

Ein minimales CLI-Tool zur Erstellung von Geschaeftsbriefen nach DIN 5008 Form A als PDF/A aus Markdown.

Verwendet [Typst](https://typst.app) und das [din5008a](https://github.com/jcmx9/typst-DIN5008a)-Template.

## Voraussetzungen

Installation via [Homebrew](https://brew.sh):

```bash
# Python
brew install python

# uv (Python-Paketmanager)
brew install uv

# Typst (Dokumenten-Compiler)
brew install typst

# Pandoc (Dokumenten-Konverter)
brew install pandoc
```

### din5008a-Template

Typst-Template installieren oder aktualisieren:

```bash
mdo update
```

Oder manuell:

```bash
git clone https://github.com/jcmx9/typst-DIN5008a.git
mkdir -p ~/.local/share/typst/packages/local/din5008a/0.1.1
cp -r typst-DIN5008a/src ~/.local/share/typst/packages/local/din5008a/0.1.1/
cp typst-DIN5008a/typst.toml ~/.local/share/typst/packages/local/din5008a/0.1.1/
```

## Installation

```bash
uv tool install git+https://github.com/jcmx9/mdo-cli.git
```

## Schnellstart

```bash
# 1. Typst-Template installieren
mdo update

# 2. Absenderprofil anlegen (interaktiver Wizard)
mdo profile
```

Der Wizard fragt Name, Adresse, Kontakt, Bankdaten, Akzentfarbe und mehr ab.
Ergebnis: `profile.yaml` im aktuellen Verzeichnis.

```yaml
# profile.yaml (Beispiel)
name: Max Mustermann
street: Musterstrasse 1
zip: 12345
city: Musterstadt
phone: 0123 456789
email: max@example.de
iban: DE89 3704 0044 0532 0130 00
bic: COBADEFFXXX
bank: Commerzbank
accent: "#B03060"
qr_code: true
signature: unterschrift.svg
closing: Mit freundlichem Gruss
open: true
reveal: true
```

```bash
# 3. Neuen Brief anlegen
mdo new
```

Erzeugt eine `.md`-Datei (z.B. `2026-04-06_Brief01.md`) mit Frontmatter aus dem Profil:

```markdown
---
name: Max Mustermann
street: Musterstrasse 1
zip: 12345
city: Musterstadt
...
date: null  # JJJJ-MM-TT (null = heute)
subject: null
recipient:
  - Firma GmbH
  - Frau / Herrn Vorname Nachname
  - Strasse Nr.
  - PLZ Ort
attachments: []
---

Sehr geehrte Damen und Herren,


```

Datei bearbeiten: `subject`, `recipient`, `date`, `attachments` ausfuellen und Brieftext in Markdown schreiben.

```bash
# 4. Als PDF/A kompilieren
mdo compile 2026-04-06_Brief01.md
```

Pipeline: Markdown-Body → Pandoc → Typst-Markup, Frontmatter → JSON, beides mit din5008a-Template → PDF/A-2b.

## Drucken

> **Immer mit Skalierung 100% drucken (kein "An Seite anpassen").** Das DIN-5008-Layout erfordert exakte Masse fuer Faltmarken, Adressfelder und Raender. Skalierung zerstoert das Layout.

## Befehle

### `mdo profile`

Interaktiver Wizard zum Erstellen von `profile.yaml` im aktuellen Verzeichnis.

### `mdo new [DATEINAME]`

Erstellt eine Brief-`.md` mit Frontmatter aus `profile.yaml`. Ohne `DATEINAME` wird `JJJJ-MM-TT_BriefCC.md` erzeugt (kollisionssicherer Zaehler).

### `mdo compile DATEINAME.md`

Kompiliert eine Brief-`.md` zu PDF/A-2b via Pandoc und Typst. Prueft vorher, ob die benoetigten Schriften installiert sind.

### `mdo update`

Laedt das din5008a Typst-Template herunter oder aktualisiert es.

## Feldreferenz

### profile.yaml

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `name` | String | Absendername |
| `street` | String | Strasse |
| `zip` | String | Postleitzahl |
| `city` | String | Ort |
| `phone` | String | Telefonnummer |
| `email` | String | E-Mail-Adresse |
| `iban` | String | Bank-IBAN |
| `bic` | String | Bank-BIC |
| `bank` | String | Bankname |
| `qr_code` | Boolean | vCard-QR-Code anzeigen |
| `signature` | String/null | Dateiname der Unterschrift (z.B. `unterschrift.svg`) |
| `closing` | String | Schlussgruss (z.B. "Mit freundlichem Gruss") |
| `accent` | String | Akzentfarbe als Hex (z.B. `"#B03060"`) |
| `open` | Boolean | PDF nach Kompilierung oeffnen |
| `reveal` | Boolean | PDF im Dateimanager anzeigen |

### Brief-`.md` (zusaetzliche Felder)

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `date` | String/null | Briefdatum (`null` = heute, Format: `JJJJ-MM-TT`) |
| `subject` | String | Betreff |
| `recipient` | Liste | Empfaenger-Adresszeilen |
| `attachments` | Liste | Anlagen-Beschriftungen (am Briefende dargestellt) |

### Unterschrift

Die Unterschrift-Datei im selben Verzeichnis wie den Brief ablegen. Unterstuetzte Formate: SVG, PNG, GIF, JPG. SVG oder transparentes PNG empfohlen.

## Lizenz

[MIT](LICENSE)
