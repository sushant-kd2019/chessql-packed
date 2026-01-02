#!/bin/bash

# Start ChessQL Desktop UI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR/ui"

if [ ! -d "node_modules" ]; then
    echo "Error: Node modules not found. Run ./scripts/setup.sh first."
    exit 1
fi

echo "Starting ChessQL Desktop UI..."
echo "Make sure the backend server is running on port 9090"
echo ""

npm start

