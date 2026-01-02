#!/bin/bash

# Start both ChessQL Backend and UI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "Starting ChessQL (Backend + UI)"
echo "======================================"

# Start backend in background
echo "Starting backend server..."
cd "$ROOT_DIR/backend"

if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found. Run ./scripts/setup.sh first."
    exit 1
fi

source .venv/bin/activate
python start_server.py &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to start..."
sleep 3

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "Error: Backend failed to start"
    exit 1
fi

echo "✓ Backend started (PID: $BACKEND_PID)"

# Start UI
echo "Starting UI..."
cd "$ROOT_DIR/ui"

if [ ! -d "node_modules" ]; then
    echo "Error: Node modules not found. Run ./scripts/setup.sh first."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

npm start

# When UI closes, stop backend
echo "UI closed. Stopping backend..."
kill $BACKEND_PID 2>/dev/null
echo "Done."

