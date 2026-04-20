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

# Install dependencies with Serious Python's own Python
echo "==> Installing Python dependencies..."
SP_PYTHON="$FLUTTER_DIR/build/build_python_3.12.9/python/bin/python3"
if [ ! -f "$SP_PYTHON" ]; then
    echo "Error: Serious Python's Python not found. Run 'dart run serious_python:main package' once first."
    exit 1
fi
"$SP_PYTHON" -m pip install --target "$PACK_DIR" pydantic pyyaml --quiet --disable-pip-version-check

echo "==> Running serious_python packager..."

cd "$FLUTTER_DIR"
dart run serious_python:main package "$PACK_DIR" \
    -p Darwin \
    --skip-site-packages \
    --verbose

echo "==> Cleaning up..."
rm -rf "$PACK_DIR"

echo "==> Done. Asset at flutter/app/app.zip"
