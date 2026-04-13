# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Project infrastructure: CHANGELOG, CONTRIBUTING, SECURITY, CODEOWNERS
- CI/CD: GitHub Actions workflows (ci.yml, release.yml)
- Dependabot configuration for automated dependency updates
- Pre-commit configuration (ruff, trailing whitespace, YAML/TOML checks)
- PEP 561 py.typed marker
- Coverage configuration with 80% minimum threshold

### Changed
- pyproject.toml aligned with project standards (classifiers, URLs, ruff rules, coverage)
- bump-my-version config: CalVer field names (year/month/micro), commit/tag settings
- .gitignore extended with missing patterns

## [26.4.28] - 2026-04-13

### Added
- Interactive `new` command with wizard prompts
- `signature_width` field for controlling signature image width
- Release infrastructure (scripts/release.sh, docs/github-release.md)

## [26.4.0] - 2026-04-05

### Added
- Initial release with DIN 5008 Form A letter generation
- Commands: compile, new, profile, update, install-fonts
- Pandoc + Typst pipeline for PDF/A-2b output
- Pydantic validation for letter data
- Auto-rename compiled files to date_recipient - subject format
- Font installation from Adobe GitHub releases

[Unreleased]: https://github.com/jcmx9/mdo-cli/compare/v26.4.28...HEAD
[26.4.28]: https://github.com/jcmx9/mdo-cli/compare/v26.4.0...v26.4.28
[26.4.0]: https://github.com/jcmx9/mdo-cli/releases/tag/v26.4.0
