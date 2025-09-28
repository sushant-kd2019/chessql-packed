"""
Chess PGN Ingestion Module
Handles parsing PGN files and ingesting them into the SQLite database.
"""

import re
import os
from typing import List, Dict, Any, Optional
from database import ChessDatabase
from piece_analysis import ChessPieceAnalyzer


class PGNIngestion:
    """Handles PGN file parsing and database ingestion."""
    
    def __init__(self, db_path: str = "chess_games.db"):
        """Initialize the ingestion system with database connection."""
        self.db = ChessDatabase(db_path)
        self.piece_analyzer = ChessPieceAnalyzer()
    
    def parse_pgn_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse a PGN file and extract game data."""
        games = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Split content into individual games
            game_blocks = self._split_pgn_games(content)
            
            for game_block in game_blocks:
                if game_block.strip():
                    game_data = self._parse_single_game(game_block)
                    if game_data:
                        games.append(game_data)
        
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
            return []
        except Exception as e:
            print(f"Error reading file '{file_path}': {e}")
            return []
        
        return games
    
    def _split_pgn_games(self, content: str) -> List[str]:
        """Split PGN content into individual games."""
        # Split on double newlines that separate games, but be more careful
        # Look for patterns like: \n\n[Event "..." or \n\n\n[Event "..."
        games = re.split(r'\n\s*\n\s*\n', content)  # Split on 2+ newlines
        
        # If that doesn't work, try splitting on single newline followed by [Event
        if len(games) == 1:
            games = re.split(r'\n(?=\[Event)', content)
        
        # Filter out empty games and games without proper PGN structure
        valid_games = []
        for game in games:
            game = game.strip()
            if game and '[' in game and ']' in game:  # Must have tags
                valid_games.append(game)
        return valid_games
    
    def _parse_single_game(self, game_text: str) -> Optional[Dict[str, Any]]:
        """Parse a single PGN game and extract metadata."""
        lines = game_text.split('\n')
        
        # Extract tags (metadata)
        tags = {}
        moves_text = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                # Parse tag
                tag_match = re.match(r'\[(\w+)\s+"([^"]*)"\]', line)
                if tag_match:
                    tag_name = tag_match.group(1)
                    tag_value = tag_match.group(2)
                    tags[tag_name] = tag_value
            else:
                # This is part of the moves
                if line:  # Only add non-empty lines
                    moves_text += line + " "
        
        # Extract key information
        game_data = {
            'pgn_text': game_text,
            'moves': moves_text.strip(),
            'white_player': tags.get('White', ''),
            'black_player': tags.get('Black', ''),
            'result': tags.get('Result', ''),
            'date_played': tags.get('Date', ''),
            'event': tags.get('Event', ''),
            'site': tags.get('Site', ''),
            'round': tags.get('Round', ''),
            'eco_code': tags.get('ECO', ''),
            'opening': tags.get('Opening', ''),
            'time_control': tags.get('TimeControl', ''),
            'white_elo': tags.get('WhiteElo', ''),
            'black_elo': tags.get('BlackElo', ''),
            'variant': tags.get('Variant', ''),
            'termination': tags.get('Termination', '')
        }
        
        return game_data
    
    
    def ingest_file(self, file_path: str) -> int:
        """Ingest a PGN file into the database."""
        print(f"Parsing PGN file: {file_path}")
        games = self.parse_pgn_file(file_path)
        
        if not games:
            print("No games found in the file.")
            return 0
        
        print(f"Found {len(games)} games. Ingesting into database...")
        
        ingested_count = 0
        for game in games:
            try:
                moves_length = len(game.get('moves', ''))
                print(f"  Game has {moves_length} characters of moves")
                game_id = self.db.insert_game(game)
                
                # Analyze captures with position tracking
                captures = self.piece_analyzer.analyze_captures(game.get('moves', ''))
                
                if captures:
                    self.db.insert_captures(game_id, captures)
                    print(f"    Found {len(captures)} captures with position data")
                
                ingested_count += 1
                print(f"  Ingested game {ingested_count}: {game.get('white_player', 'Unknown')} vs {game.get('black_player', 'Unknown')}")
            except Exception as e:
                print(f"  Error ingesting game: {e}")
        
        print(f"Successfully ingested {ingested_count} games.")
        return ingested_count
    
    def ingest_directory(self, directory_path: str, file_pattern: str = "*.pgn") -> int:
        """Ingest all PGN files in a directory."""
        import glob
        
        total_ingested = 0
        pgn_files = glob.glob(os.path.join(directory_path, file_pattern))
        
        if not pgn_files:
            print(f"No PGN files found in {directory_path}")
            return 0
        
        print(f"Found {len(pgn_files)} PGN files in {directory_path}")
        
        for file_path in pgn_files:
            print(f"\nProcessing: {os.path.basename(file_path)}")
            ingested = self.ingest_file(file_path)
            total_ingested += ingested
        
        print(f"\nTotal games ingested: {total_ingested}")
        return total_ingested


def main():
    """Command line interface for ingestion."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest PGN files into chess database')
    parser.add_argument('input', help='PGN file or directory to ingest')
    parser.add_argument('--db', default='chess_games.db', help='Database file path')
    parser.add_argument('--pattern', default='*.pgn', help='File pattern for directory ingestion')
    
    args = parser.parse_args()
    
    ingestion = PGNIngestion(args.db)
    
    if os.path.isfile(args.input):
        ingestion.ingest_file(args.input)
    elif os.path.isdir(args.input):
        ingestion.ingest_directory(args.input, args.pattern)
    else:
        print(f"Error: '{args.input}' is not a valid file or directory.")


if __name__ == "__main__":
    main()
