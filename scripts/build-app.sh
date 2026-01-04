#!/bin/bash

# Build complete ChessQL application
# This script builds both the Python backend and Electron app

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "Building ChessQL Desktop Application"
echo "======================================"
echo ""

# Parse arguments
BUILD_TARGET="mac"  # Default to macOS
while [[ $# -gt 0 ]]; do
    case $1 in
        --mac)
            BUILD_TARGET="mac"
            shift
            ;;
        --win)
            BUILD_TARGET="win"
            shift
            ;;
        --linux)
            BUILD_TARGET="linux"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--mac|--win|--linux]"
            exit 1
            ;;
    esac
done

echo "Target platform: $BUILD_TARGET"
echo ""

# Step 1: Build Python Backend
echo "Step 1/3: Building Python backend..."
echo "--------------------------------------"
"$SCRIPT_DIR/build-backend.sh"
echo ""

# Verify backend build
if [ ! -f "$ROOT_DIR/backend/dist/chessql-server" ]; then
    echo "Error: Backend build failed - chessql-server not found"
    exit 1
fi

# Step 2: Install UI dependencies (if needed)
echo "Step 2/3: Preparing Electron app..."
echo "--------------------------------------"
cd "$ROOT_DIR/ui"

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Install electron-builder if not present
if ! npm list electron-builder > /dev/null 2>&1; then
    echo "Installing electron-builder..."
    npm install --save-dev electron-builder
fi

echo "✓ UI dependencies ready"
echo ""

# Step 3: Build Electron app
echo "Step 3/3: Building Electron app..."
echo "--------------------------------------"

case $BUILD_TARGET in
    mac)
        npm run build:mac
        ;;
    win)
        npm run build:win
        ;;
    linux)
        npm run build:linux
        ;;
esac

echo ""
echo "======================================"
echo "Build Complete!"
echo "======================================"
echo ""
echo "Output location: $ROOT_DIR/ui/dist/"
echo ""

# List the output files
if [ -d "$ROOT_DIR/ui/dist" ]; then
    echo "Built artifacts:"
    ls -la "$ROOT_DIR/ui/dist/" 2>/dev/null || echo "(empty)"
fi

