#!/bin/bash

# ChessQL Monorepo Setup Script
# Installs dependencies for both backend and UI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "ChessQL Monorepo Setup"
echo "======================================"

# Setup Backend
echo ""
echo "Setting up Backend (Python)..."
echo "--------------------------------------"
cd "$ROOT_DIR/backend"

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt

deactivate
echo "✓ Backend setup complete!"

# Setup UI
echo ""
echo "Setting up UI (Node.js)..."
echo "--------------------------------------"
cd "$ROOT_DIR/ui"

echo "Installing Node.js dependencies..."
npm install

echo "✓ UI setup complete!"

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "To start the application:"
echo "  1. Start backend: ./scripts/start-backend.sh"
echo "  2. Start UI:      ./scripts/start-ui.sh"
echo "  Or start both:    ./scripts/start-all.sh"
echo ""

