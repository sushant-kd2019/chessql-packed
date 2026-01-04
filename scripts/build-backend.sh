#!/bin/bash

# Build ChessQL Backend using PyInstaller
# Creates a standalone executable from the Python server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$ROOT_DIR/backend"

echo "======================================"
echo "Building ChessQL Backend"
echo "======================================"

cd "$BACKEND_DIR"

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found. Run ./scripts/setup.sh first."
    exit 1
fi

source .venv/bin/activate

# Install PyInstaller if not already installed
echo "Ensuring PyInstaller is installed..."
pip install pyinstaller --quiet

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Build using the spec file
echo "Building executable with PyInstaller..."
pyinstaller chessql.spec --clean

# Verify the build
if [ -f "dist/chessql-server" ]; then
    echo ""
    echo "✓ Backend built successfully!"
    echo "  Executable: $BACKEND_DIR/dist/chessql-server"
    
    # Show file size
    SIZE=$(du -h dist/chessql-server | cut -f1)
    echo "  Size: $SIZE"
else
    echo ""
    echo "✗ Build failed - executable not found"
    exit 1
fi

deactivate

echo ""
echo "======================================"
echo "Backend Build Complete!"
echo "======================================"

