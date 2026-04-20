#!/usr/bin/env bash
# Package the Python backend for Serious Python embedding.
# Run from the repo root: ./scripts/package_app.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FLUTTER_DIR="$REPO_ROOT/flutter"
PACK_DIR="$FLUTTER_DIR/_pack"

echo "==> Preparing Python package..."

# Clean previous packaging
rm -rf "$PACK_DIR"
mkdir -p "$PACK_DIR"

# Copy Python source
cp -r "$REPO_ROOT/src/mdo" "$PACK_DIR/mdo"
cp "$FLUTTER_DIR/python/main.py" "$PACK_DIR/main.py"
cp "$FLUTTER_DIR/python/requirements.txt" "$PACK_DIR/requirements.txt"

echo "==> Running serious_python packager..."

cd "$FLUTTER_DIR"
dart run serious_python:main package "$PACK_DIR" \
    -p Darwin \
    --requirements "pydantic>=2.0" \
    --requirements "pyyaml>=6.0" \
    --verbose

echo "==> Cleaning up..."
rm -rf "$PACK_DIR"

echo "==> Done. Asset at flutter/app/app.zip"
