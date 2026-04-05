# mdo-cli Design Spec

A minimal Python CLI that generates DIN 5008 Form A business letters as PDF/A using Typst and the `din5008a` template.

## Commands

### `mdo profile NAME`

Creates a `profile.yaml` in the current directory with sender defaults.

```yaml
name: Max Mustermann
street: Musterstrasse 1
zip: 12345
city: Musterstadt
phone: 0123 456789
email: max@example.de
iban: DE89 3704 0044 0532 0130 00
bic: COBADEFFXXX
bank: Commerzbank
qr_code: true
signature: null
closing: Mit freundlichem Gruß
```

- `NAME` is used as the `name` field value.
- All other fields get placeholder values.
- `signature` and `qr_code` default to `null` and `true` respectively.
- If `profile.yaml` already exists, abort with an error.

### `mdo new [FILENAME]`

Creates a new letter `.md` file with frontmatter populated from `profile.yaml`.

**Filename logic:**
- If `FILENAME` is provided, use it as-is.
- If omitted, auto-generate: `YYYY-MM-DD_BriefCC.md` where `CC` is a zero-padded counter (01, 02, ...) that avoids collision with existing files matching that date pattern.

**File content:**
- YAML frontmatter block containing all fields from `profile.yaml` plus letter-specific fields.
- `date: null` with a comment `# JJJJ-MM-TT`.
- `subject: null`
- `recipient` as an array with placeholder lines.
- Empty body below the frontmatter with a placeholder greeting.

```yaml
---
name: Max Mustermann
street: Musterstrasse 1
zip: 12345
city: Musterstadt
phone: 0123 456789
email: max@example.de
iban: DE89 3704 0044 0532 0130 00
bic: COBADEFFXXX
bank: Commerzbank
qr_code: true
signature: null
closing: Mit freundlichem Gruß
date: null  # JJJJ-MM-TT
subject: null
recipient:
  - Firma GmbH
  - Frau / Herrn Vorname Nachname
  - Strasse Nr.
  - PLZ Ort
---

Sehr geehrte Damen und Herren,



```

- If `profile.yaml` is missing, print a hint and offer to create one interactively (prompt for name, then write `profile.yaml` with defaults). After creation, remind the user to edit it before proceeding.

### `mdo compile FILENAME.md`

Compiles a letter `.md` to PDF/A-2b.

**Pipeline:**

1. **Font check** — verify that Source Serif 4, Source Sans 3, and Source Code Pro are installed as system fonts (static variants). If any font is missing, print a warning naming the missing font(s) and a link: `https://github.com/jcmx9/typst-DIN5008a#requirements`. Then abort.
2. **Parse** — read the `.md` file, split YAML frontmatter and Markdown body.
3. **Resolve defaults** — if `date` is `null`, use today's date formatted as German locale (e.g. `05. April 2026`).
4. **Convert body** — transform Markdown body to Typst markup:
   - `**bold**` → `*bold*`
   - `*italic*` / `_italic_` → `_italic_`
   - `# Heading` → `= Heading` (all levels)
   - Ordered and unordered lists pass through unchanged (Typst-compatible).
   - Inline code and code blocks pass through unchanged.
   - Other Markdown features are passed as-is (best effort).
5. **Build signature block** — after the body, append `closing` from frontmatter. If `signature` is set (not null), append `#image("unterschrift.EXT", width: 40mm)` between closing and sender name. The signature file must be named `unterschrift.{svg,png,gif,jpg}` and exist in the current directory.
6. **Generate `.typ`** — write a temporary `.typ` file importing `@local/din5008a:0.1.1` with all sender/recipient/date/subject data and the converted body.
7. **Compile** — run `typst compile --pdf-standard a-2b TEMP.typ OUTPUT.pdf` where `OUTPUT` has the same basename as the input `.md`.
8. **Cleanup** — delete the temporary `.typ` file.

**Generated `.typ` structure:**

```typst
#import "@local/din5008a:0.1.1": din5008a, bullet

#show: din5008a.with(
  sender: (
    name: "...",
    street: "...",
    city: "12345 Musterstadt",
    phone: "...",
    email: "...",
    iban: "...",
    bic: "...",
    bank: "...",
    qr: true,
  ),
  recipient: ("Line 1", "Line 2", ...),
  date: "05. April 2026",
  subject: "...",
)

// converted body content here

Mit freundlichem Gruß

#image("unterschrift.svg", width: 40mm)

Sender Name
```

**Field mapping (profile.yaml → din5008a template):**

| profile.yaml | din5008a sender dict |
|-------------|---------------------|
| `name` | `name` |
| `street` | `street` |
| `zip` + `city` | `city` (concatenated: "12345 Musterstadt") |
| `phone` | `phone` |
| `email` | `email` |
| `iban` | `iban` |
| `bic` | `bic` |
| `bank` | `bank` |
| `qr_code` (true/false) | `qr` (true/false) |

## Data Flow

```
profile.yaml ──┐
               ├──► mdo new ──► brief.md
               │                   │
               │                   ▼
               │              mdo compile
               │                   │
               │         ┌─────────┼──────────┐
               │         ▼         ▼          ▼
               │    font check   parse     resolve
               │         │        .md      defaults
               │         ▼         │          │
               │      (abort?)     ▼          │
               │              md → typst ◄────┘
               │                   │
               │                   ▼
               │              write .typ
               │                   │
               │                   ▼
               │            typst compile
               │            (PDF/A-2b)
               │                   │
               │                   ▼
               └──────────►   brief.pdf
```

## Error Handling

| Condition | Behavior |
|-----------|----------|
| `profile.yaml` not found (new/compile) | Error: "profile.yaml not found in current directory" |
| `profile.yaml` already exists (profile) | Error: "profile.yaml already exists" |
| Missing fonts (compile) | Warning listing missing fonts + link to README, then abort |
| `signature` set but file not found | Error: "Signature file not found: unterschrift.EXT" |
| `typst` not installed | Error: "typst not found. Install: https://typst.app" |
| `typst compile` fails | Forward typst stderr to user |
| Input `.md` not found | Error: "File not found: FILENAME.md" |

## Tech Stack

- Python >= 3.12 (target 3.14)
- `typer` — CLI framework
- `pyyaml` — YAML parsing
- `typst` CLI — compilation (subprocess, no shell=True)
- No other runtime dependencies

## Project Structure

```
src/mdo/
  __init__.py
  __main__.py
  cli.py
  commands/
    __init__.py
    profile.py
    new.py
    compile.py
  core/
    __init__.py
    fonts.py
    markdown.py
    typst_builder.py
  exceptions.py
tests/
  conftest.py
  test_profile.py
  test_new.py
  test_compile.py
  test_markdown.py
pyproject.toml
README.md
LICENSE
```

## Deliverables

### README.md

Bilingual (English + German / Deutsch section at the bottom). Contents:

- Project description and purpose
- Installation (Python, uv, typst CLI, fonts)
- Quick start with examples for all three commands
- Field reference table
- Font requirements (static variants of Source Serif 4, Source Sans 3, Source Code Pro) with download links
- License

### LICENSE

MIT license, author: jcmx9.

### pyproject.toml

- Package name: `mdo-cli`
- Version managed via `__init__.py` (`__version__`)
- Entry point: `mdo = "mdo.cli:app"`
- Dependencies: `typer`, `pyyaml`
- Dev dependencies: `pytest`, `pytest-cov`, `ruff`, `mypy`

### VERSION

Version tracked in `src/mdo/__init__.py` as `__version__ = "0.1.0"`.

## Font Check

Use `fc-list` (Linux/macOS) to verify the three required font families are installed as static (non-variable) variants:

- Source Serif 4
- Source Sans 3
- Source Code Pro

On failure, print:

```
Warning: Missing system fonts: Source Serif 4, Source Sans 3
Install static font variants. See: https://github.com/jcmx9/typst-DIN5008a#requirements
```
