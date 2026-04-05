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
```

### Required Fonts

Install the **static** (not variable) variants of these fonts as system fonts:

- [Source Serif 4](https://github.com/adobe-fonts/source-serif/releases) -- body text
- [Source Sans 3](https://github.com/adobe-fonts/source-sans/releases) -- header, footer, UI elements
- [Source Code Pro](https://github.com/adobe-fonts/source-code-pro/releases) -- code blocks, tables

Download the latest release of each, install the files from the `TTF/` or `OTF/` **static** folder.

> **Important:** Use the static font files, not the variable ones. Typst requires static font variants.

### din5008a Template

Install or update the Typst template with:

```bash
mdo update
```

Or manually:

```bash
git clone https://github.com/jcmx9/typst-DIN5008a.git
mkdir -p ~/.local/share/typst/packages/local/din5008a/0.1.1
cp -r typst-DIN5008a/src/* ~/.local/share/typst/packages/local/din5008a/0.1.1/
cp typst-DIN5008a/typst.toml ~/.local/share/typst/packages/local/din5008a/0.1.1/
```

## Installation

```bash
uv tool install git+https://github.com/jcmx9/mdo-cli.git
```

## Quick Start

```bash
# 1. Create a sender profile
mdo profile

# 2. Edit profile.yaml with your data
#    Optional: add a signature image (unterschrift.svg or .png recommended)

# 3. Create a new letter
mdo new

# 4. Edit the generated .md file (frontmatter + body)

# 5. Compile to PDF/A
mdo compile 2026-04-05_Brief01.md
```

## Printing

> **Always print with 100% scaling (no fit-to-page).** The DIN 5008 layout requires exact measurements for fold marks, address fields, and margins. Scaling will break the layout.

## Commands

### `mdo profile`

Interactive wizard to create `profile.yaml` in the current directory.

### `mdo new [FILENAME]`

Creates a letter `.md` with frontmatter from `profile.yaml`. Without `FILENAME`, auto-generates `YYYY-MM-DD_BriefCC.md` (collision-safe counter).

### `mdo compile FILENAME.md`

Compiles a letter `.md` to PDF/A-2b. Checks for required fonts before compilation.

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

### Letter .md (additional fields)

| Field | Type | Description |
|-------|------|-------------|
| `date` | string/null | Letter date (`null` = today, format: `YYYY-MM-DD`) |
| `subject` | string | Subject line |
| `recipient` | list | Recipient address lines |

### Signature

Place the signature image in the same directory as the letter. Supported formats: SVG, PNG, GIF, JPG. The file must be named `unterschrift.{ext}`. SVG or transparent PNG recommended.

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
```

### Benoetigte Schriften

Die **statischen** (nicht variablen) Varianten dieser Schriften als Systemschriften installieren:

- [Source Serif 4](https://github.com/adobe-fonts/source-serif/releases) -- Fliesstext
- [Source Sans 3](https://github.com/adobe-fonts/source-sans/releases) -- Kopf-/Fusszeile, UI-Elemente
- [Source Code Pro](https://github.com/adobe-fonts/source-code-pro/releases) -- Code, Tabellen

Jeweils den neuesten Release herunterladen und die Dateien aus dem `TTF/`- oder `OTF/`-**static**-Ordner installieren.

> **Wichtig:** Die statischen Schriftdateien verwenden, nicht die variablen. Typst benoetigt statische Varianten.

### din5008a-Template

Typst-Template installieren oder aktualisieren:

```bash
mdo update
```

Oder manuell:

```bash
git clone https://github.com/jcmx9/typst-DIN5008a.git
mkdir -p ~/.local/share/typst/packages/local/din5008a/0.1.1
cp -r typst-DIN5008a/src/* ~/.local/share/typst/packages/local/din5008a/0.1.1/
cp typst-DIN5008a/typst.toml ~/.local/share/typst/packages/local/din5008a/0.1.1/
```

## Installation

```bash
uv tool install git+https://github.com/jcmx9/mdo-cli.git
```

## Schnellstart

```bash
# 1. Absenderprofil anlegen
mdo profile

# 2. profile.yaml mit eigenen Daten bearbeiten
#    Optional: Unterschrift-Bild hinzufuegen (unterschrift.svg oder .png empfohlen)

# 3. Neuen Brief anlegen
mdo new

# 4. Die erzeugte .md-Datei bearbeiten (Frontmatter + Brieftext)

# 5. Als PDF/A kompilieren
mdo compile 2026-04-05_Brief01.md
```

## Drucken

> **Immer mit Skalierung 100% drucken (kein "An Seite anpassen").** Das DIN-5008-Layout erfordert exakte Masse fuer Faltmarken, Adressfelder und Raender. Skalierung zerstoert das Layout.

## Befehle

### `mdo profile`

Interaktiver Wizard zum Erstellen von `profile.yaml` im aktuellen Verzeichnis.

### `mdo new [DATEINAME]`

Erstellt eine Brief-`.md` mit Frontmatter aus `profile.yaml`. Ohne `DATEINAME` wird `JJJJ-MM-TT_BriefCC.md` erzeugt (kollisionssicherer Zaehler).

### `mdo compile DATEINAME.md`

Kompiliert eine Brief-`.md` zu PDF/A-2b. Prueft vorher, ob die benoetigten Schriften installiert sind.

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

### Brief-`.md` (zusaetzliche Felder)

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `date` | String/null | Briefdatum (`null` = heute, Format: `JJJJ-MM-TT`) |
| `subject` | String | Betreff |
| `recipient` | Liste | Empfaenger-Adresszeilen |

### Unterschrift

Die Unterschrift-Datei im selben Verzeichnis wie den Brief ablegen. Unterstuetzte Formate: SVG, PNG, GIF, JPG. Die Datei muss `unterschrift.{ext}` heissen. SVG oder transparentes PNG empfohlen.

## Lizenz

[MIT](LICENSE)
