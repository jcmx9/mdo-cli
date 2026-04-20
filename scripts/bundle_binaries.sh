#!/usr/bin/env bash
# Download typst and pandoc binaries for macOS and place them in the app bundle.
# Run from the repo root: ./scripts/bundle_binaries.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RESOURCES_DIR="$REPO_ROOT/flutter/macos/Runner/Resources"
ARCH=$(uname -m)  # arm64 or x86_64

mkdir -p "$RESOURCES_DIR"

echo "==> Architecture: $ARCH"

# --- Typst ---
echo "==> Downloading typst..."
TYPST_VERSION=$(curl -sL https://api.github.com/repos/typst/typst/releases/latest | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'])")
echo "    Version: $TYPST_VERSION"

if [ "$ARCH" = "arm64" ]; then
    TYPST_ARCH="aarch64-apple-darwin"
else
    TYPST_ARCH="x86_64-apple-darwin"
fi

TYPST_URL="https://github.com/typst/typst/releases/download/${TYPST_VERSION}/typst-${TYPST_ARCH}.tar.xz"
curl -sL "$TYPST_URL" | tar xJ -C /tmp
cp "/tmp/typst-${TYPST_ARCH}/typst" "$RESOURCES_DIR/typst"
chmod +x "$RESOURCES_DIR/typst"
rm -rf "/tmp/typst-${TYPST_ARCH}"
echo "    Installed: $RESOURCES_DIR/typst"

# --- Pandoc ---
echo "==> Downloading pandoc..."
PANDOC_VERSION=$(curl -sL https://api.github.com/repos/jgm/pandoc/releases/latest | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'])")
echo "    Version: $PANDOC_VERSION"

if [ "$ARCH" = "arm64" ]; then
    PANDOC_ARCH="arm64"
else
    PANDOC_ARCH="x86_64"
fi

PANDOC_URL="https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-${PANDOC_ARCH}-macOS.zip"
curl -sL -o /tmp/pandoc.zip "$PANDOC_URL"
unzip -qo /tmp/pandoc.zip -d /tmp/pandoc
cp "/tmp/pandoc/pandoc-${PANDOC_VERSION}-${PANDOC_ARCH}/bin/pandoc" "$RESOURCES_DIR/pandoc"
chmod +x "$RESOURCES_DIR/pandoc"
rm -rf /tmp/pandoc /tmp/pandoc.zip
echo "    Installed: $RESOURCES_DIR/pandoc"

echo ""
echo "==> Done. Binaries in: $RESOURCES_DIR"
echo "    typst: $($RESOURCES_DIR/typst --version)"
echo "    pandoc: $($RESOURCES_DIR/pandoc --version | head -1)"
