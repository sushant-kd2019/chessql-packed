"""
Account Management Module
Handles storing and retrieving Lichess account information.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime


class AccountManager:
    """Manages Lichess accounts in the SQLite database."""
    
    def __init__(self, db_path: str = "chess_games.db"):
        """Initialize the account manager with database connection."""
        self.db_path = db_path
        self.init_accounts_table()
    
    def init_accounts_table(self):
        """Create the accounts table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    access_token TEXT NOT NULL,
                    token_expires_at INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_sync_at TIMESTAMP,
                    last_game_at INTEGER,
                    games_count INTEGER DEFAULT 0,
                    platform TEXT DEFAULT 'lichess'
                )
            """)
            
            # Migration: Add platform column if it doesn't exist (for existing databases)
            cursor.execute("PRAGMA table_info(accounts)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'platform' not in columns:
                cursor.execute("ALTER TABLE accounts ADD COLUMN platform TEXT DEFAULT 'lichess'")
            
            # Create index for faster lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_username ON accounts(username)")
            
            conn.commit()
    
    def add_account(self, username: str, access_token: str, token_expires_at: Optional[int] = None) -> int:
        """
        Add a new Lichess account or update if exists.
        
        Args:
            username: Lichess username
            access_token: OAuth2 access token
            token_expires_at: Unix timestamp when token expires (None = never)
        
        Returns:
            Account ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Try to insert, update if exists
            cursor.execute("""
                INSERT INTO accounts (username, access_token, token_expires_at)
                VALUES (?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    access_token = excluded.access_token,
                    token_expires_at = excluded.token_expires_at
            """, (username.lower(), access_token, token_expires_at))
            
            # Get the account ID
            cursor.execute("SELECT id FROM accounts WHERE username = ?", (username.lower(),))
            account_id = cursor.fetchone()[0]
            
            conn.commit()
            return account_id
    
    def get_account(self, username: str) -> Optional[Dict[str, Any]]:
        """Get account by username."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM accounts WHERE username = ?", (username.lower(),))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_account_by_id(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get account by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def list_accounts(self) -> List[Dict[str, Any]]:
        """List all accounts (without exposing tokens)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, token_expires_at, created_at, 
                       last_sync_at, last_game_at, games_count
                FROM accounts
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def remove_account(self, username: str) -> bool:
        """Remove an account by username."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM accounts WHERE username = ?", (username.lower(),))
            deleted = cursor.rowcount > 0
            
            conn.commit()
            return deleted
    
    def update_sync_status(self, username: str, last_sync_at: Optional[datetime] = None, 
                           last_game_at: Optional[int] = None, games_count: Optional[int] = None):
        """Update sync status for an account."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if last_sync_at is not None:
                updates.append("last_sync_at = ?")
                params.append(last_sync_at.isoformat() if isinstance(last_sync_at, datetime) else last_sync_at)
            
            if last_game_at is not None:
                updates.append("last_game_at = ?")
                params.append(last_game_at)
            
            if games_count is not None:
                updates.append("games_count = ?")
                params.append(games_count)
            
            if updates:
                params.append(username.lower())
                cursor.execute(f"""
                    UPDATE accounts 
                    SET {', '.join(updates)}
                    WHERE username = ?
                """, params)
                conn.commit()
    
    def reset_sync_status(self, username: str):
        """Reset sync status for an account (for full re-sync). Sets last_sync_at, last_game_at to NULL and games_count to 0."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE accounts 
                SET last_sync_at = NULL, last_game_at = NULL, games_count = 0
                WHERE username = ?
            """, (username.lower(),))
            conn.commit()
    
    def increment_games_count(self, username: str, count: int = 1):
        """Increment the games count for an account."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE accounts 
                SET games_count = games_count + ?
                WHERE username = ?
            """, (count, username.lower()))
            
            conn.commit()
    
    def is_token_valid(self, username: str) -> bool:
        """Check if the token for an account is still valid."""
        account = self.get_account(username)
        
        if not account:
            return False
        
        if account['token_expires_at'] is None:
            # Token doesn't expire
            return True
        
        # Check if token has expired
        import time
        return account['token_expires_at'] > int(time.time())
    
    def get_access_token(self, username: str) -> Optional[str]:
        """Get the access token for an account (if valid)."""
        if not self.is_token_valid(username):
            return None
        
        account = self.get_account(username)
        return account['access_token'] if account else None

