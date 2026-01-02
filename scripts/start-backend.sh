#!/bin/bash

# Start ChessQL Backend Server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR/backend"

if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found. Run ./scripts/setup.sh first."
    exit 1
fi

echo "Starting ChessQL Backend Server..."
echo "API will be available at http://localhost:9090"
echo "Press Ctrl+C to stop"
echo ""

source .venv/bin/activate
python start_server.py

