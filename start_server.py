#!/usr/bin/env python3
"""
ChessQL Server Startup Script
Convenient script to start the FastAPI server with proper configuration.
"""

import os
import sys
import uvicorn
from pathlib import Path

def main():
    """Start the ChessQL FastAPI server."""
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Set default environment variables if not set
    if not os.getenv("CHESSQL_DB_PATH"):
        os.environ["CHESSQL_DB_PATH"] = "chess_games.db"
    
    if not os.getenv("CHESSQL_REFERENCE_PLAYER"):
        os.environ["CHESSQL_REFERENCE_PLAYER"] = "lecorvus"
    
    # Check if database exists
    db_path = os.environ["CHESSQL_DB_PATH"]
    if not os.path.exists(db_path):
        print(f"❌ Error: Database file '{db_path}' not found.")
        print("Please run ingestion first:")
        print("  python cli.py ingest your_games.pgn")
        sys.exit(1)
    
    print("🚀 Starting ChessQL API Server...")
    print(f"📊 Database: {db_path}")
    print(f"👤 Reference Player: {os.environ['CHESSQL_REFERENCE_PLAYER']}")
    print("🌐 Server will be available at: http://localhost:9090")
    print("📚 API Documentation: http://localhost:9090/docs")
    print("🔍 Health Check: http://localhost:9090/health")
    print("📝 Examples: http://localhost:9090/examples")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Start the server
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=9090,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )

if __name__ == "__main__":
    main()
