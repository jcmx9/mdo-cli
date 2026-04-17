#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/release.sh dev              - bump dev pre-release on dev branch
#   ./scripts/release.sh prod             - merge dev -> main, tag, GitHub release
#   ./scripts/release.sh prod --new-month - advance CalVer month before prod release

MODE="${1:-}"
NEW_MONTH="${2:-}"

if [[ -z "$MODE" ]]; then
    echo "Usage: $0 {dev|prod} [--new-month]"
    exit 1
fi

ensure_clean() {
    if [[ -n "$(git status --porcelain)" ]]; then
        echo "Error: working tree is not clean"
        exit 1
    fi
}

current_version() {
    python -c "from mdo import __version__; print(__version__)"
}

case "$MODE" in
    dev)
        ensure_clean
        BRANCH="$(git branch --show-current)"
        if [[ "$BRANCH" != "dev" ]]; then
            echo "Error: must be on dev branch (currently on $BRANCH)"
            exit 1
        fi

        bump-my-version bump dev
        VERSION="$(current_version)"
        git push origin dev
        echo "Dev release: $VERSION"
        ;;

    prod)
        ensure_clean
        BRANCH="$(git branch --show-current)"
        if [[ "$BRANCH" != "dev" ]]; then
            echo "Error: must be on dev branch (currently on $BRANCH)"
            exit 1
        fi

        if [[ "$NEW_MONTH" == "--new-month" ]]; then
            bump-my-version bump month
        fi

        # Ensure clean prod version (strip .devN)
        bump-my-version bump micro

        VERSION="$(current_version)"

        git checkout main
        git merge dev --no-edit
        git tag "v$VERSION"
        git push origin main --tags
        gh release create "v$VERSION" --title "v$VERSION" --generate-notes
        git checkout dev
        echo "Prod release: v$VERSION"
        ;;

    *)
        echo "Usage: $0 {dev|prod} [--new-month]"
        exit 1
        ;;
esac
