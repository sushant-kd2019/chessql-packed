#!/bin/bash

# ChessQL Desktop App Startup Script

echo "Starting ChessQL Desktop Application..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "Error: Please run this script from the chessql-ui directory"
    exit 1
fi

# Check if ChessQL backend exists
if [ ! -d "../chessql" ]; then
    echo "Error: ChessQL backend not found. Please ensure it's in the parent directory."
    exit 1
fi

# Start ChessQL backend in background
echo "Starting ChessQL backend..."
cd ../chessql
python3 server.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start Electron app
echo "Starting Electron application..."
cd ../chessql-ui
npm start

# Clean up background process when Electron closes
trap "kill $BACKEND_PID 2>/dev/null" EXIT
