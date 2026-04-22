#!/usr/bin/env bash
# Build MarkdownOffice.app and create a DMG installer.
# Run from the repo root: ./scripts/build_dmg.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FLUTTER_DIR="$REPO_ROOT/flutter"
APP_NAME="MarkdownOffice"
ICON_DIR="$FLUTTER_DIR/macos/Runner/Assets.xcassets/AppIcon.appiconset"
RELEASE_DIR="$FLUTTER_DIR/build/macos/Build/Products/Release"
DMG_STAGING="/tmp/dmg_staging_$$"
DMG_OUTPUT="$REPO_ROOT/$APP_NAME.dmg"

# --- 1. Package Python backend ---
echo "==> Packaging Python backend..."
"$REPO_ROOT/scripts/package_app.sh"

# --- 2. Clear Serious Python cache ---
echo "==> Clearing Python cache..."
rm -rf "$HOME/Library/Application Support/de.jcmx9.markdownoffice/flet" 2>/dev/null || true

# --- 3. Build macOS app ---
echo "==> Building macOS app..."
cd "$FLUTTER_DIR"
flutter build macos

# --- 4. Generate .icns from icon PNGs ---
echo "==> Generating .icns..."
ICONSET="/tmp/AppIcon_$$.iconset"
mkdir -p "$ICONSET"
cp "$ICON_DIR/app_icon_16.png"   "$ICONSET/icon_16x16.png"
cp "$ICON_DIR/app_icon_32.png"   "$ICONSET/icon_16x16@2x.png"
cp "$ICON_DIR/app_icon_32.png"   "$ICONSET/icon_32x32.png"
cp "$ICON_DIR/app_icon_64.png"   "$ICONSET/icon_32x32@2x.png"
cp "$ICON_DIR/app_icon_128.png"  "$ICONSET/icon_128x128.png"
cp "$ICON_DIR/app_icon_256.png"  "$ICONSET/icon_128x128@2x.png"
cp "$ICON_DIR/app_icon_256.png"  "$ICONSET/icon_256x256.png"
cp "$ICON_DIR/app_icon_512.png"  "$ICONSET/icon_256x256@2x.png"
cp "$ICON_DIR/app_icon_512.png"  "$ICONSET/icon_512x512.png"
cp "$ICON_DIR/app_icon_1024.png" "$ICONSET/icon_512x512@2x.png"
iconutil -c icns "$ICONSET" -o "/tmp/AppIcon_$$.icns"
cp "/tmp/AppIcon_$$.icns" "$RELEASE_DIR/$APP_NAME.app/Contents/Resources/AppIcon.icns"
rm -rf "$ICONSET" "/tmp/AppIcon_$$.icns"

# --- 5. Create DMG ---
echo "==> Creating DMG..."
rm -f "$DMG_OUTPUT"
rm -rf "$DMG_STAGING"
mkdir -p "$DMG_STAGING"
cp -R "$RELEASE_DIR/$APP_NAME.app" "$DMG_STAGING/"

create-dmg \
  --volname "$APP_NAME" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "$APP_NAME.app" 175 190 \
  --app-drop-link 425 190 \
  --hide-extension "$APP_NAME.app" \
  --no-internet-enable \
  "$DMG_OUTPUT" \
  "$DMG_STAGING"

rm -rf "$DMG_STAGING"

echo "==> Done: $DMG_OUTPUT"
