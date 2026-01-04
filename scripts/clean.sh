#!/bin/bash

# Clean all build artifacts

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Cleaning build artifacts..."

# Clean backend build
rm -rf "$ROOT_DIR/backend/build"
rm -rf "$ROOT_DIR/backend/dist"
echo "✓ Cleaned backend/build and backend/dist"

# Clean UI build
rm -rf "$ROOT_DIR/ui/dist"
rm -rf "$ROOT_DIR/ui/out"
echo "✓ Cleaned ui/dist and ui/out"

echo ""
echo "All build artifacts cleaned!"

