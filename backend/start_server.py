#!/usr/bin/env python3
"""
ChessQL Server Startup Script
Convenient script to start the FastAPI server with proper configuration.
"""

import os
import sys
import uvicorn
from pathlib import Path


def is_packaged():
    """Check if running as a PyInstaller packaged executable."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_data_dir():
    """Get the appropriate data directory based on platform and packaging."""
    if sys.platform == 'darwin':  # macOS
        data_dir = Path.home() / 'Library' / 'Application Support' / 'ChessQL'
    elif sys.platform == 'win32':  # Windows
        data_dir = Path(os.environ.get('APPDATA', Path.home())) / 'ChessQL'
    else:  # Linux and others
        data_dir = Path.home() / '.config' / 'chessql'
    
    # Create directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def main():
    """Start the ChessQL FastAPI server."""
    
    # Determine if we're running as a packaged app
    packaged = is_packaged()
    
    if packaged:
        # Packaged app: use Application Support folder for user data
        data_dir = get_data_dir()
        print(f"📁 Data directory: {data_dir}")
        
        # Set database path in user's data directory
        if not os.getenv("CHESSQL_DB_PATH"):
            os.environ["CHESSQL_DB_PATH"] = str(data_dir / "chess_games.db")
    else:
        # Development: use current directory
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        
        if not os.getenv("CHESSQL_DB_PATH"):
            os.environ["CHESSQL_DB_PATH"] = "chess_games.db"
    
    if not os.getenv("CHESSQL_REFERENCE_PLAYER"):
        os.environ["CHESSQL_REFERENCE_PLAYER"] = "lecorvus"
    
    # Initialize database if it doesn't exist
    db_path = os.environ["CHESSQL_DB_PATH"]
    if not os.path.exists(db_path):
        print(f"📦 Database '{db_path}' not found. Creating new database...")
        from database import ChessDatabase
        ChessDatabase(db_path)
        print("✅ Database initialized. Connect your Lichess account to sync games.")
    
    print("🚀 Starting ChessQL API Server...")
    print(f"📊 Database: {db_path}")
    print(f"👤 Reference Player: {os.environ['CHESSQL_REFERENCE_PLAYER']}")
    print("🌐 Server will be available at: http://localhost:9090")
    print("📚 API Documentation: http://localhost:9090/docs")
    print("🔍 Health Check: http://localhost:9090/health")
    print("📝 Examples: http://localhost:9090/examples")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Start the server
    if packaged:
        # In packaged mode, import app directly (reload doesn't work with PyInstaller)
        from server import app
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=9090,
            log_level="info"
        )
    else:
        # In development mode, use string import for reload support
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=9090,
            reload=True,
            log_level="info"
        )

if __name__ == "__main__":
    main()
