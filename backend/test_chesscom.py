"""
Test script for Chess.com integration.
Run this to verify the implementation works correctly.
"""

import asyncio
import sys
from accounts import AccountManager
from chesscom_sync import get_sync_manager, ChessComSyncError
from database import ChessDatabase


def test_database_schema():
    """Test that database schema has the required columns."""
    print("=" * 60)
    print("Test 1: Database Schema")
    print("=" * 60)
    
    db = ChessDatabase("chess_games.db")
    
    # Check that accounts table has platform column
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(accounts)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'platform' in columns:
        print("✓ accounts.platform column exists")
    else:
        print("✗ accounts.platform column missing")
        conn.close()
        return False
    
    # Check games table has chesscom_id
    cursor.execute("PRAGMA table_info(games)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'chesscom_id' in columns:
        print("✓ games.chesscom_id column exists")
    else:
        print("✗ games.chesscom_id column missing")
        conn.close()
        return False
    
    conn.close()
    
    print("✓ Database schema is correct\n")
    return True


def test_account_validation():
    """Test Chess.com username validation."""
    print("=" * 60)
    print("Test 2: Username Validation")
    print("=" * 60)
    
    from accounts import AccountManager
    
    # Test valid usernames
    valid_usernames = ["hikaru", "magnus_carlsen", "player-123", "test_user"]
    for username in valid_usernames:
        if AccountManager.validate_chesscom_username(username):
            print(f"✓ '{username}' is valid")
        else:
            print(f"✗ '{username}' should be valid but failed")
            return False
    
    # Test invalid usernames
    invalid_usernames = ["ab", "a" * 30, "user@name", "user name", ""]
    for username in invalid_usernames:
        if not AccountManager.validate_chesscom_username(username):
            print(f"✓ '{username}' correctly rejected")
        else:
            print(f"✗ '{username}' should be invalid but passed")
            return False
    
    print("✓ Username validation works correctly\n")
    return True


def test_add_account():
    """Test adding a Chess.com account."""
    print("=" * 60)
    print("Test 3: Add Chess.com Account")
    print("=" * 60)
    
    account_manager = AccountManager("chess_games.db")
    
    # Use a well-known Chess.com username for testing
    test_username = "hikaru"
    
    try:
        # Check if account already exists
        existing = account_manager.get_account(test_username)
        if existing:
            print(f"ℹ Account '{test_username}' already exists, skipping add test")
            print(f"  Platform: {existing.get('platform', 'unknown')}")
        else:
            account_id = account_manager.add_account(
                username=test_username,
                access_token="",  # Chess.com doesn't need tokens
                token_expires_at=None,
                platform="chesscom"
            )
            print(f"✓ Added Chess.com account '{test_username}' (ID: {account_id})")
        
        # Verify account
        account = account_manager.get_account(test_username)
        if account and account.get('platform') == 'chesscom':
            print(f"✓ Account verified: platform = {account.get('platform')}")
        else:
            print(f"✗ Account verification failed")
            return False
        
        print("✓ Account management works correctly\n")
        return True
        
    except Exception as e:
        print(f"✗ Error adding account: {e}")
        return False


async def test_fetch_archives():
    """Test fetching archives from Chess.com API."""
    print("=" * 60)
    print("Test 4: Fetch Chess.com Archives")
    print("=" * 60)
    
    sync_manager = get_sync_manager()
    test_username = "hikaru"  # Well-known Chess.com player
    
    try:
        archives = await sync_manager.get_archives(test_username)
        
        if archives and len(archives) > 0:
            print(f"✓ Successfully fetched {len(archives)} archives")
            print(f"  Latest archive: {archives[-1] if archives else 'N/A'}")
            print(f"  Oldest archive: {archives[0] if archives else 'N/A'}")
        else:
            print(f"⚠ No archives found for '{test_username}'")
        
        print("✓ Archive fetching works\n")
        return True
        
    except ChessComSyncError as e:
        print(f"✗ Chess.com API error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_sync_small_batch():
    """Test syncing a small batch of games."""
    print("=" * 60)
    print("Test 5: Sync Small Batch of Games")
    print("=" * 60)
    
    sync_manager = get_sync_manager()
    db = ChessDatabase("chess_games.db")
    account_manager = AccountManager("chess_games.db")
    
    test_username = "hikaru"
    max_games = 5  # Just sync 5 games for testing
    
    # Get or create account
    account = account_manager.get_account(test_username)
    if not account or account.get('platform') != 'chesscom':
        print(f"ℹ Creating test account '{test_username}'...")
        account_manager.add_account(
            username=test_username,
            access_token="",
            platform="chesscom"
        )
        account = account_manager.get_account(test_username)
    
    account_id = account['id']
    
    try:
        print(f"Starting sync for '{test_username}' (max {max_games} games)...")
        
        games_count = 0
        async for game in sync_manager.stream_games(
            username=test_username,
            max_games=max_games
        ):
            games_count += 1
            
            # Check if game exists
            exists = db.game_exists(chesscom_id=game.id)
            
            if not exists:
                # Insert game
                game_data = game.to_pgn_dict()
                game_id = db.insert_game(game_data, account_id=account_id)
                print(f"  ✓ Game {games_count}: {game.white_player} vs {game.black_player} ({game.result}) - Inserted (ID: {game_id})")
            else:
                print(f"  ⊙ Game {games_count}: {game.white_player} vs {game.black_player} ({game.result}) - Already exists")
            
            if games_count >= max_games:
                break
        
        if games_count > 0:
            print(f"\n✓ Successfully processed {games_count} games")
        else:
            print(f"\n⚠ No games found to sync")
        
        print("✓ Game syncing works\n")
        return True
        
    except ChessComSyncError as e:
        print(f"✗ Chess.com API error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Chess.com Integration Tests")
    print("=" * 60 + "\n")
    
    results = []
    
    # Test 1: Database Schema (not async)
    results.append(("Database Schema", test_database_schema()))
    
    # Test 2: Username Validation
    results.append(("Username Validation", test_account_validation()))
    
    # Test 3: Add Account
    results.append(("Add Account", test_add_account()))
    
    # Test 4: Fetch Archives
    results.append(("Fetch Archives", await test_fetch_archives()))
    
    # Test 5: Sync Games (optional - requires API access)
    print("Note: Test 5 requires internet connection and Chess.com API access")
    try:
        results.append(("Sync Games", await test_sync_small_batch()))
    except Exception as e:
        print(f"⚠ Skipping sync test due to error: {e}\n")
        results.append(("Sync Games", False))
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

