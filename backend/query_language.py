"""
Chess Query Language Module
Simplified query language for SQL queries on metadata and regex queries on moves.
"""

from typing import List, Dict, Any, Optional
from database import ChessDatabase
import re


class ChessQueryLanguage:
    """Simplified query language processor for chess game searches."""
    
    def __init__(self, db_path: str = "chess_games.db", reference_player: str = "lecorvus", account_id: Optional[int] = None, platform: Optional[str] = None):
        """Initialize the query language with database connection."""
        self.db_path = db_path  # Store for later reference
        self.db = ChessDatabase(db_path)
        self.reference_player = reference_player
        self.account_id = account_id  # Account ID for filtering games
        self.platform = platform  # Platform for filtering games
    
    def execute_query(self, query: str, account_id: Optional[int] = None, platform: Optional[str] = None, show_final_query: bool = False) -> List[Dict[str, Any]]:
        """Execute a query and return results.
        
        Args:
            query: SQL query string
            account_id: Optional account ID to filter games by. If provided, overrides self.account_id.
            platform: Optional platform to filter by. If provided, overrides self.platform.
            show_final_query: Whether to print the final SQL query after filters are applied.
        """
        query = query.strip()
        
        # Use provided values or fall back to instance values
        filter_account_id = account_id if account_id is not None else self.account_id
        filter_platform = platform if platform is not None else self.platform
        
        # Check if it's a regex query for moves (starts with /regex/)
        if query.startswith('/') and query.endswith('/'):
            regex_pattern = query[1:-1]  # Remove the slashes
            results = self.db.search_moves(regex_pattern)
            # Apply account_id filter if specified
            if filter_account_id:
                results = [r for r in results if r.get('account_id') == filter_account_id]
            # Apply platform filter if specified
            if filter_platform:
                if filter_platform == 'lichess':
                    results = [r for r in results if r.get('lichess_id')]
                elif filter_platform == 'chesscom':
                    results = [r for r in results if r.get('chesscom_id')]
            return results
        
        # Pre-process player result conditions to convert them to explicit field queries
        query = self._preprocess_player_result_conditions(query)
        
        # Add account_id filter if specified
        if filter_account_id:
            query = self._add_account_filter(query, filter_account_id)
        
        # Add platform filter if specified (but only if not already in query from natural language)
        # Note: Natural language search may already add platform filter, so we skip if it exists
        if filter_platform:
            # Check if platform filter already exists in query
            platform_filter_exists = False
            if filter_platform == 'lichess' and 'lichess_id IS NOT NULL' in query:
                platform_filter_exists = True
            elif filter_platform == 'chesscom' and 'chesscom_id IS NOT NULL' in query:
                platform_filter_exists = True
            
            if not platform_filter_exists:
                query = self._add_platform_filter(query, filter_platform)
        
        # Show final query after all filters are applied
        if show_final_query:
            print(f"Final SQL (after filters): {query}")
            # Don't execute twice, just show the query
            print(f"Filter account_id: {filter_account_id}, Filter platform: {filter_platform}")
            print("-" * 50)
        
        # Check for SQL queries with capture conditions
        if self._has_capture_condition(query):
            return self._handle_sql_with_captures(query)
        
        # Otherwise, treat as regular SQL query
        return self.db.execute_sql_query(query)
    
    def _add_account_filter(self, query: str, account_id: int) -> str:
        """Add account_id filter to SQL query."""
        import re
        
        # Check if account_id filter already exists
        if f'account_id = {account_id}' in query or f'account_id={account_id}' in query:
            return query
        
        # Check if query already has a WHERE clause
        where_match = re.search(r'\bWHERE\b', query, re.IGNORECASE)
        if where_match:
            # Find the end of the WHERE clause (before ORDER BY, GROUP BY, LIMIT, or end of query)
            where_end = len(query)
            for keyword in ['ORDER BY', 'GROUP BY', 'LIMIT']:
                match = re.search(rf'\b{keyword}\b', query[where_match.end():], re.IGNORECASE)
                if match:
                    where_end = where_match.end() + match.start()
                    break
            
            # Insert AND account_id = X before ORDER BY/GROUP BY/LIMIT or at end
            before_clause = query[:where_end].rstrip()
            after_clause = query[where_end:].lstrip()
            query = before_clause + f' AND account_id = {account_id} ' + after_clause
        else:
            # Add WHERE clause with account_id filter
            # Insert before ORDER BY, GROUP BY, or LIMIT if they exist
            insert_pos = len(query)
            for keyword in ['ORDER BY', 'GROUP BY', 'LIMIT']:
                match = re.search(rf'\b{keyword}\b', query, re.IGNORECASE)
                if match and match.start() < insert_pos:
                    insert_pos = match.start()
            
            query = query[:insert_pos].rstrip() + f' WHERE account_id = {account_id} ' + query[insert_pos:].lstrip()
        
        return query
    
    def _preprocess_player_result_conditions(self, query: str) -> str:
        """Pre-process player result conditions to convert them to explicit field queries."""
        import re
        
        # Find all player result conditions and replace them
        def replace_player_result(match):
            condition = match.group(1)
            player_name = self._extract_player_name_from_query(condition)
            result_type = self._extract_result_type_from_query(condition)
            
            if not player_name or not result_type:
                return match.group(0)  # Return original if can't parse
            
            if result_type in ['won', 'win']:
                return f"((white_player = '{player_name}' AND white_result = 'win') OR (black_player = '{player_name}' AND black_result = 'win'))"
            elif result_type in ['lost', 'loss']:
                return f"((white_player = '{player_name}' AND white_result = 'loss') OR (black_player = '{player_name}' AND black_result = 'loss'))"
            elif result_type in ['drew', 'draw']:
                return f"((white_player = '{player_name}' AND white_result = 'draw') OR (black_player = '{player_name}' AND black_result = 'draw'))"
            else:
                return match.group(0)  # Return original if can't parse
        
        # Replace player result conditions
        query = re.sub(
            r'\(([^)]*["\']?(\w+)["\']?\s+(won|lost|drew|win|loss|draw)[^)]*)\)',
            replace_player_result,
            query,
            flags=re.IGNORECASE
        )
        
        return query
    
    def _has_capture_condition(self, query: str) -> bool:
        """Check if SQL query contains capture conditions."""
        import re
        
        # Look for patterns like "(queen captured queen)", "(knight captured rook)", etc.
        capture_patterns = [
            r'\([^)]*\b(pawn|bishop|knight|rook|queen|king)\s+captured\s+(pawn|bishop|knight|rook|queen|king)',
            r'\([^)]*\b(captured|took)\s+(pawn|bishop|knight|rook|queen|king)\s+with\s+(pawn|bishop|knight|rook|queen|king)',
            r'\([^)]*\b(pawn|bishop|knight|rook|queen|king)\s+(exchanged|sacrificed)',
            r'\([^)]*\b(exchanged|sacrificed)\s+(pawn|bishop|knight|rook|queen|king)',
            r'\([^)]*\b(\w+)\s+(pawn|bishop|knight|rook|queen|king)\s+(exchanged|sacrificed)',
            r'\([^)]*\b(opponent)\s+(pawn|bishop|knight|rook|queen|king)\s+(exchanged|sacrificed)',
            r'\([^)]*\b(pawn\s+promoted\s+to\s+(pawn|bishop|knight|rook|queen|king))',
            r'\([^)]*\b(promoted\s+to\s+(pawn|bishop|knight|rook|queen|king))',
            r'\([^)]*\b(pawn\s+promoted\s+to\s+(pawn|bishop|knight|rook|queen|king)\s+x\s+\d+)',
            r'\([^)]*\b(promoted\s+to\s+(pawn|bishop|knight|rook|queen|king)\s+x\s+\d+)',
        ]
        
        for pattern in capture_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        return False
    
    def _handle_sql_with_captures(self, query: str) -> List[Dict[str, Any]]:
        """Handle SQL queries that contain capture conditions."""
        import re
        
        # First, preprocess any remaining player result conditions
        query = self._preprocess_player_result_conditions(query)
        
        # Check for opponent-specific exchange/sacrifice patterns first
        opponent_exchange_match = re.search(
            r'\(([^)]*\b(opponent)\s+(pawn|bishop|knight|rook|queen|king)\s+(exchanged|sacrificed)[^)]*)\)',
            query, re.IGNORECASE
        )
        
        if opponent_exchange_match:
            condition = opponent_exchange_match.group(1)
            piece = self._extract_piece_from_query(condition)
            event_type = self._extract_exchange_type_from_query(condition)
            move_condition = self._extract_move_condition_from_query(condition)
            
            if not piece or not event_type:
                return []
            
            # Build the SQL query for opponent-specific exchanges/sacrifices
            move_clause = ""
            if move_condition:
                if move_condition['type'] == 'before':
                    move_clause = f"AND c.move_number <= {move_condition['move']}"
                elif move_condition['type'] == 'after':
                    move_clause = f"AND c.move_number >= {move_condition['move']}"
            
            if event_type == 'exchanged':
                subquery = f"""
                    EXISTS (
                        SELECT 1 FROM captures c 
                        WHERE c.game_id = games.id 
                        AND c.captured_piece = '{piece.upper()}' 
                        AND c.is_exchange = 1
                        AND ((games.white_player = '{self.reference_player}' AND c.side = 'white') OR (games.black_player = '{self.reference_player}' AND c.side = 'black'))
                        {move_clause}
                    )
                """
            else:  # sacrificed
                subquery = f"""
                    EXISTS (
                        SELECT 1 FROM captures c 
                        WHERE c.game_id = games.id 
                        AND c.captured_piece = '{piece.upper()}' 
                        AND c.is_sacrifice = 1
                        AND ((games.white_player = '{self.reference_player}' AND c.side = 'white') OR (games.black_player = '{self.reference_player}' AND c.side = 'black'))
                        {move_clause}
                    )
                """
            
            # Replace the condition with the subquery
            modified_query = query.replace(opponent_exchange_match.group(0), subquery)
            return self.db.execute_sql_query(modified_query)
        
        # Check for pawn promotion patterns
        promotion_match = re.search(
            r'\(([^)]*\b(pawn\s+promoted\s+to\s+(pawn|bishop|knight|rook|queen|king)|promoted\s+to\s+(pawn|bishop|knight|rook|queen|king))[^)]*)\)',
            query, re.IGNORECASE
        )
        
        if promotion_match:
            condition = promotion_match.group(1)
            promoted_piece = self._extract_promoted_piece_from_query(condition)
            move_condition = self._extract_move_condition_from_query(condition)
            promotion_count = self._extract_promotion_count_from_query(condition)
            
            if not promoted_piece:
                return []
            
            # Check if this is a player-specific promotion query
            player_name = self._extract_player_name_from_query(condition)
            
            # Also check if there's a player condition in the broader query context
            # Look for patterns like "(player_name won)" or "(player_name lost)" in the query
            broader_player_match = re.search(r'\(([^)]*\b(\w+)\s+(won|lost|drew)[^)]*)\)', query, re.IGNORECASE)
            if broader_player_match and not player_name:
                broader_player_name = broader_player_match.group(2)
                # Check if this broader player name is not a chess term
                if broader_player_name.lower() not in ['won', 'lost', 'drew', 'win', 'loss', 'draw', 'and', 'or', 'where', '(', ')', 
                                                     'pawn', 'bishop', 'knight', 'rook', 'queen', 'king', 'promoted', 'to', 'exchanged', 'sacrificed']:
                    player_name = broader_player_name
            
            # If still no player name, look for preprocessed SQL patterns like "white_player = 'player_name'"
            if not player_name:
                preprocessed_player_match = re.search(r"white_player\s*=\s*['\"]([^'\"]+)['\"]", query)
                if preprocessed_player_match:
                    player_name = preprocessed_player_match.group(1)
            
            if player_name:
                # Player-specific promotion - need to determine which side made the promotion
                # White promotes to rank 8 (e.g., e8=Q), Black promotes to rank 1 (e.g., e1=Q)
                # Use individual patterns for each file since SQLite LIKE doesn't support [a-h]
                files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
                white_conditions = []
                black_conditions = []
                
                for file in files:
                    white_conditions.append(f"g2.moves LIKE '%{file}8={promoted_piece.upper()}%'")
                    black_conditions.append(f"g2.moves LIKE '%{file}1={promoted_piece.upper()}%'")
                
                white_pattern = ' OR '.join(white_conditions)
                black_pattern = ' OR '.join(black_conditions)
                
                # Handle promotion count
                if promotion_count:
                    # Count the number of promotions for the specific player
                    # We need to count only the promotions made by the specific player
                    if promoted_piece.upper() == 'Q':
                        # For queen promotions, count 8=Q for white, 1=Q for black
                        subquery = f"""
                            EXISTS (
                                SELECT 1 FROM games g2 
                                WHERE g2.id = games.id 
                                AND (
                                    (g2.white_player = '{player_name}' AND (
                                        (LENGTH(g2.moves) - LENGTH(REPLACE(g2.moves, '8=Q', ''))) / 3 >= {promotion_count}
                                        AND ({white_pattern})
                                    ))
                                    OR 
                                    (g2.black_player = '{player_name}' AND (
                                        (LENGTH(g2.moves) - LENGTH(REPLACE(g2.moves, '1=Q', ''))) / 3 >= {promotion_count}
                                        AND ({black_pattern})
                                    ))
                                )
                            )
                        """
                    elif promoted_piece.upper() == 'N':
                        # For knight promotions, count 8=N for white, 1=N for black
                        subquery = f"""
                            EXISTS (
                                SELECT 1 FROM games g2 
                                WHERE g2.id = games.id 
                                AND (
                                    (g2.white_player = '{player_name}' AND (
                                        (LENGTH(g2.moves) - LENGTH(REPLACE(g2.moves, '8=N', ''))) / 3 >= {promotion_count}
                                        AND ({white_pattern})
                                    ))
                                    OR 
                                    (g2.black_player = '{player_name}' AND (
                                        (LENGTH(g2.moves) - LENGTH(REPLACE(g2.moves, '1=N', ''))) / 3 >= {promotion_count}
                                        AND ({black_pattern})
                                    ))
                                )
                            )
                        """
                    elif promoted_piece.upper() == 'R':
                        # For rook promotions, count 8=R for white, 1=R for black
                        subquery = f"""
                            EXISTS (
                                SELECT 1 FROM games g2 
                                WHERE g2.id = games.id 
                                AND (
                                    (g2.white_player = '{player_name}' AND (
                                        (LENGTH(g2.moves) - LENGTH(REPLACE(g2.moves, '8=R', ''))) / 3 >= {promotion_count}
                                        AND ({white_pattern})
                                    ))
                                    OR 
                                    (g2.black_player = '{player_name}' AND (
                                        (LENGTH(g2.moves) - LENGTH(REPLACE(g2.moves, '1=R', ''))) / 3 >= {promotion_count}
                                        AND ({black_pattern})
                                    ))
                                )
                            )
                        """
                    elif promoted_piece.upper() == 'B':
                        # For bishop promotions, count 8=B for white, 1=B for black
                        subquery = f"""
                            EXISTS (
                                SELECT 1 FROM games g2 
                                WHERE g2.id = games.id 
                                AND (
                                    (g2.white_player = '{player_name}' AND (
                                        (LENGTH(g2.moves) - LENGTH(REPLACE(g2.moves, '8=B', ''))) / 3 >= {promotion_count}
                                        AND ({white_pattern})
                                    ))
                                    OR 
                                    (g2.black_player = '{player_name}' AND (
                                        (LENGTH(g2.moves) - LENGTH(REPLACE(g2.moves, '1=B', ''))) / 3 >= {promotion_count}
                                        AND ({black_pattern})
                                    ))
                                )
                            )
                        """
                    else:
                        # For other pieces, use generic pattern
                        count_pattern = f"={promoted_piece.upper()}"
                        subquery = f"""
                            EXISTS (
                                SELECT 1 FROM games g2 
                                WHERE g2.id = games.id 
                                AND (
                                    (g2.white_player = '{player_name}' AND (
                                        (LENGTH(g2.moves) - LENGTH(REPLACE(g2.moves, '{count_pattern}', ''))) / LENGTH('{count_pattern}') >= {promotion_count}
                                        AND ({white_pattern})
                                    ))
                                    OR 
                                    (g2.black_player = '{player_name}' AND (
                                        (LENGTH(g2.moves) - LENGTH(REPLACE(g2.moves, '{count_pattern}', ''))) / LENGTH('{count_pattern}') >= {promotion_count}
                                        AND ({black_pattern})
                                    ))
                                )
                            )
                        """
                else:
                    # No count specified - just check if promotion exists
                    subquery = f"""
                        EXISTS (
                            SELECT 1 FROM games g2 
                            WHERE g2.id = games.id 
                            AND (
                                (g2.white_player = '{player_name}' AND ({white_pattern}))
                                OR 
                                (g2.black_player = '{player_name}' AND ({black_pattern}))
                            )
                        )
                    """
            else:
                # General promotion query - any player can promote
                promotion_pattern = f"={promoted_piece.upper()}"
                if promotion_count:
                    # Count the number of promotions
                    subquery = f"""
                        EXISTS (
                            SELECT 1 FROM games g2 
                            WHERE g2.id = games.id 
                            AND (LENGTH(g2.moves) - LENGTH(REPLACE(g2.moves, '{promotion_pattern}', ''))) / LENGTH('{promotion_pattern}') >= {promotion_count}
                        )
                    """
                else:
                    # No count specified - just check if promotion exists
                    subquery = f"""
                        EXISTS (
                            SELECT 1 FROM games g2 
                            WHERE g2.id = games.id 
                            AND g2.moves LIKE '%{promotion_pattern}%'
                        )
                    """
            
            # Replace the condition with the subquery
            modified_query = query.replace(promotion_match.group(0), subquery)
            return self.db.execute_sql_query(modified_query)
        
        # Check for player-specific exchange/sacrifice patterns
        player_exchange_match = re.search(
            r'\(([^)]*\b(\w+)\s+(pawn|bishop|knight|rook|queen|king)\s+(exchanged|sacrificed)[^)]*)\)',
            query, re.IGNORECASE
        )
        
        if player_exchange_match:
            condition = player_exchange_match.group(1)
            player_name = self._extract_player_name_from_query(condition)
            piece = self._extract_piece_from_query(condition)
            event_type = self._extract_exchange_type_from_query(condition)
            move_condition = self._extract_move_condition_from_query(condition)
            
            if not player_name or not piece or not event_type:
                return []
            
            # Build the SQL query for player-specific exchanges/sacrifices
            move_clause = ""
            if move_condition:
                if move_condition['type'] == 'before':
                    move_clause = f"AND c.move_number <= {move_condition['move']}"
                elif move_condition['type'] == 'after':
                    move_clause = f"AND c.move_number >= {move_condition['move']}"
            
            if event_type == 'exchanged':
                subquery = f"""
                    EXISTS (
                        SELECT 1 FROM captures c 
                        WHERE c.game_id = games.id 
                        AND c.captured_piece = '{piece.upper()}' 
                        AND c.is_exchange = 1
                        AND ((games.white_player = '{player_name}' AND c.side = 'black') OR (games.black_player = '{player_name}' AND c.side = 'white'))
                        {move_clause}
                    )
                """
            else:  # sacrificed
                subquery = f"""
                    EXISTS (
                        SELECT 1 FROM captures c 
                        WHERE c.game_id = games.id 
                        AND c.captured_piece = '{piece.upper()}' 
                        AND c.is_sacrifice = 1
                        AND ((games.white_player = '{player_name}' AND c.side = 'black') OR (games.black_player = '{player_name}' AND c.side = 'white'))
                        {move_clause}
                    )
                """
            
            # Replace the condition with the subquery
            modified_query = query.replace(player_exchange_match.group(0), subquery)
            return self.db.execute_sql_query(modified_query)
        
        # Check for general exchange/sacrifice patterns
        exchange_match = re.search(
            r'\(([^)]*\b(pawn|bishop|knight|rook|queen|king)\s+(exchanged|sacrificed)[^)]*)\)',
            query, re.IGNORECASE
        )
        
        if exchange_match:
            condition = exchange_match.group(1)
            piece = self._extract_piece_from_query(condition)
            event_type = self._extract_exchange_type_from_query(condition)
            move_condition = self._extract_move_condition_from_query(condition)
            
            if not piece or not event_type:
                return []
            
            # Build the SQL query for exchanges/sacrifices
            move_clause = ""
            if move_condition:
                if move_condition['type'] == 'before':
                    move_clause = f"AND c.move_number <= {move_condition['move']}"
                elif move_condition['type'] == 'after':
                    move_clause = f"AND c.move_number >= {move_condition['move']}"
            
            if event_type == 'exchanged':
                subquery = f"""
                    EXISTS (
                        SELECT 1 FROM captures c 
                        WHERE c.game_id = games.id 
                        AND c.captured_piece = '{piece.upper()}' 
                        AND c.is_exchange = 1
                        {move_clause}
                    )
                """
            else:  # sacrificed
                subquery = f"""
                    EXISTS (
                        SELECT 1 FROM captures c 
                        WHERE c.game_id = games.id 
                        AND c.captured_piece = '{piece.upper()}' 
                        AND c.is_sacrifice = 1
                        {move_clause}
                    )
                """
            
            # Replace the condition with the subquery
            modified_query = query.replace(exchange_match.group(0), subquery)
            return self.db.execute_sql_query(modified_query)
        
        # Handle specific piece capture patterns
        capture_match = re.search(
            r'\(([^)]*\b(pawn|bishop|knight|rook|queen|king)\s+captured\s+(pawn|bishop|knight|rook|queen|king)[^)]*)\)',
            query, re.IGNORECASE
        )
        
        if not capture_match:
            # Try alternative pattern
            capture_match = re.search(
                r'\(([^)]*\b(captured|took)\s+(pawn|bishop|knight|rook|queen|king)\s+with\s+(pawn|bishop|knight|rook|queen|king)[^)]*)\)',
                query, re.IGNORECASE
            )
        
        if not capture_match:
            return []
        
        condition = capture_match.group(1)
        
        # Parse the condition
        capturing_piece = self._extract_piece_from_query(condition)
        captured_piece = self._extract_captured_piece_from_query(condition)
        move_condition = self._extract_move_condition_from_query(condition)
        
        if not capturing_piece or not captured_piece:
            return []
        
        # Build the SQL query by replacing the capture condition
        move_clause = ""
        if move_condition:
            if move_condition['type'] == 'before':
                move_clause = f"AND c.move_number <= {move_condition['move']}"
            elif move_condition['type'] == 'after':
                move_clause = f"AND c.move_number >= {move_condition['move']}"
        
        subquery = f"""
            EXISTS (
                SELECT 1 FROM captures c 
                WHERE c.game_id = games.id 
                AND c.capturing_piece = '{capturing_piece.upper()}' 
                AND c.captured_piece = '{captured_piece.upper()}'
                {move_clause}
            )
        """
        
        # Replace the capture condition with the subquery
        modified_query = query.replace(capture_match.group(0), subquery)
        
        return self.db.execute_sql_query(modified_query)
    
    def _has_player_result_condition(self, query: str) -> bool:
        """Check if SQL query contains player result conditions."""
        import re
        
        # Look for patterns like "(lecorvus won)", "(player lost)", "(player drew)", etc.
        player_result_patterns = [
            r'\([^)]*["\']?(\w+)["\']?\s+(won|lost|drew|win|loss|draw)',
            r'\([^)]*\b(won|lost|drew|win|loss|draw)\s+["\']?(\w+)["\']?',
        ]
        
        for pattern in player_result_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        return False
    
    def _handle_sql_with_player_results(self, query: str) -> List[Dict[str, Any]]:
        """Handle SQL queries that contain player result conditions."""
        import re
        
        # If query contains AND/OR, we need to handle it differently
        if re.search(r'\b(AND|OR)\b', query, re.IGNORECASE):
            # For combined queries, just return empty and let SQL handle it
            return []
        
        # Extract the player result condition
        player_result_match = re.search(
            r'\(([^)]*["\']?(\w+)["\']?\s+(won|lost|drew|win|loss|draw)[^)]*)\)',
            query, re.IGNORECASE
        )
        
        if not player_result_match:
            # Try alternative pattern
            player_result_match = re.search(
                r'\(([^)]*\b(won|lost|drew|win|loss|draw)\s+["\']?(\w+)["\']?[^)]*)\)',
                query, re.IGNORECASE
            )
        
        if not player_result_match:
            return []
        
        condition = player_result_match.group(1)
        
        # Parse the condition
        player_name = self._extract_player_name_from_query(condition)
        result_type = self._extract_result_type_from_query(condition)
        
        if not player_name or not result_type:
            return []
        
        # Build the SQL query by replacing the player result condition
        if result_type in ['won', 'win']:
            subquery = f"""
                (white_player = '{player_name}' AND white_result = 'win') 
                OR (black_player = '{player_name}' AND black_result = 'win')
            """
        elif result_type in ['lost', 'loss']:
            subquery = f"""
                (white_player = '{player_name}' AND white_result = 'loss') 
                OR (black_player = '{player_name}' AND black_result = 'loss')
            """
        elif result_type in ['drew', 'draw']:
            subquery = f"""
                (white_player = '{player_name}' AND white_result = 'draw') 
                OR (black_player = '{player_name}' AND black_result = 'draw')
            """
        else:
            return []
        
        # Replace the player result condition with the subquery
        modified_query = query.replace(player_result_match.group(0), f"({subquery})")
        
        return self.db.execute_sql_query(modified_query)
    
    def _extract_player_name_from_query(self, query: str) -> str:
        """Extract player name from query."""
        import re
        
        # Look for quoted strings first
        quoted_match = re.search(r'"([^"]+)"', query)
        if quoted_match:
            return quoted_match.group(1)
        
        # Look for single quoted strings
        single_quoted_match = re.search(r"'([^']+)'", query)
        if single_quoted_match:
            return single_quoted_match.group(1)
        
        # Look for unquoted words (simplified)
        words = query.split()
        for word in words:
            # Skip numbers and exclude common chess terms, piece names, and count words
            if word.isdigit():
                continue
            if word.lower() not in ['won', 'lost', 'drew', 'win', 'loss', 'draw', 'and', 'or', 'where', '(', ')', 
                                  'pawn', 'bishop', 'knight', 'rook', 'queen', 'king', 'promoted', 'to', 'exchanged', 'sacrificed',
                                  'once', 'twice', 'thrice', 'times', 'time', 'x']:
                return word
        
        return None
    
    def _extract_result_type_from_query(self, query: str) -> str:
        """Extract result type from query (won/lost/drew)."""
        query_lower = query.lower()
        
        if 'won' in query_lower or 'win' in query_lower:
            return 'won'
        elif 'lost' in query_lower or 'loss' in query_lower:
            return 'lost'
        elif 'drew' in query_lower or 'draw' in query_lower:
            return 'drew'
        
        return None
    
    def _extract_piece_from_query(self, query: str) -> str:
        """Extract piece name from query."""
        piece_mapping = {
            'pawn': 'P',
            'bishop': 'B', 
            'knight': 'N',
            'rook': 'R',
            'queen': 'Q',
            'king': 'K'
        }
        
        query_lower = query.lower()
        for piece_name, piece_symbol in piece_mapping.items():
            if piece_name in query_lower:
                return piece_symbol
        
        return None
    
    def _extract_exchange_type_from_query(self, query: str) -> str:
        """Extract exchange type from query (exchanged or sacrificed)."""
        query_lower = query.lower()
        
        if 'exchanged' in query_lower:
            return 'exchanged'
        elif 'sacrificed' in query_lower:
            return 'sacrificed'
        
        return None
    
    def _extract_captured_piece_from_query(self, query: str) -> str:
        """Extract captured piece from query."""
        piece_mapping = {
            'pawn': 'P',
            'bishop': 'B', 
            'knight': 'N',
            'rook': 'R',
            'queen': 'Q',
            'king': 'K'
        }
        
        query_lower = query.lower()
        
        # Split by "captured" and get the second part
        if 'captured' in query_lower:
            parts = query_lower.split('captured')
            if len(parts) > 1:
                captured_part = parts[1].strip()
                for piece_name, piece_symbol in piece_mapping.items():
                    if piece_name in captured_part:
                        return piece_symbol
        
        return None
    
    def _extract_promoted_piece_from_query(self, query: str) -> str:
        """Extract promoted piece from query."""
        piece_mapping = {
            'pawn': 'P',
            'bishop': 'B', 
            'knight': 'N',
            'rook': 'R',
            'queen': 'Q',
            'king': 'K'
        }
        
        query_lower = query.lower()
        
        # Look for "promoted to X" pattern
        if 'promoted to' in query_lower:
            parts = query_lower.split('promoted to')
            if len(parts) > 1:
                promoted_part = parts[1].strip()
                for piece_name, piece_symbol in piece_mapping.items():
                    if piece_name in promoted_part:
                        return piece_symbol
        
        return None
    
    def _extract_promotion_count_from_query(self, query: str) -> Optional[int]:
        """Extract promotion count from query (x N format)."""
        import re
        
        # Look for "x N" pattern (e.g., "x 2", "x 3")
        count_match = re.search(r'x\s+(\d+)', query.lower())
        if count_match:
            return int(count_match.group(1))
        
        return None
    
    def _extract_move_condition_from_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract move condition from query (before/after move N)."""
        import re
        
        query_lower = query.lower()
        
        # Look for "before move N" pattern
        before_match = re.search(r'before\s+move\s+(\d+)', query_lower)
        if before_match:
            return {
                'type': 'before',
                'move': int(before_match.group(1))
            }
        
        # Look for "after move N" pattern
        after_match = re.search(r'after\s+move\s+(\d+)', query_lower)
        if after_match:
            return {
                'type': 'after',
                'move': int(after_match.group(1))
            }
        
        return None
    
    def get_query_examples(self) -> List[str]:
        """Get example queries for the user."""
        return [
            # SQL queries for metadata
            'SELECT white_player, black_player, result FROM games',
            'SELECT * FROM games WHERE white_player = "lecorvus"',
            'SELECT * FROM games WHERE result = "1-0"',
            'SELECT * FROM games WHERE eco_code = "B10"',
            'SELECT COUNT(*) as total_games FROM games',
            'SELECT white_player, COUNT(*) as games FROM games GROUP BY white_player',
            
            # Regex queries for moves
            '/e4.*c5/',  # Games with e4 followed by c5
            '/O-O/',     # Games with castling
            '/Qh5\\+/',   # Games with Qh5+
            '/1\\. e4/',  # Games starting with 1. e4
            
            # Capture queries (with position tracking)
            'SELECT white_player FROM games WHERE (queen captured queen)',
            'SELECT black_player FROM games WHERE (knight captured rook)',
            'SELECT COUNT(*) FROM games WHERE (bishop captured bishop)',
            'SELECT * FROM games WHERE (pawn captured queen)',
            
            # Exchange and sacrifice queries
            'SELECT white_player FROM games WHERE (queen exchanged)',
            'SELECT black_player FROM games WHERE (knight sacrificed)',
            'SELECT COUNT(*) FROM games WHERE (pawn exchanged before move 10)',
            'SELECT * FROM games WHERE (rook sacrificed after move 15)',
            
            # Player result queries
            'SELECT white_player, black_player FROM games WHERE (player won)',
            'SELECT COUNT(*) FROM games WHERE (player lost)',
            'SELECT * FROM games WHERE (player drew)',
            'SELECT white_player FROM games WHERE (player won) AND (queen sacrificed)',
            
            # Sorting queries
            'SELECT white_player, black_player, result FROM games ORDER BY white_player',
            'SELECT white_player, black_player, white_elo FROM games ORDER BY CAST(white_elo AS INTEGER) DESC',
            'SELECT white_player, black_player, date_played FROM games ORDER BY date_played DESC',
            'SELECT white_player, COUNT(*) as games FROM games GROUP BY white_player ORDER BY games DESC',
            'SELECT white_player, black_player FROM games WHERE (player won) ORDER BY date_played DESC',
            
            # Capture queries with move numbers
            'SELECT white_player FROM games WHERE (queen captured bishop before move 20)',
            'SELECT black_player FROM games WHERE (knight captured pawn after move 10)',
            'SELECT COUNT(*) FROM games WHERE (bishop captured bishop before move 15)',
            'SELECT * FROM games WHERE (pawn captured queen after move 5)',
            'SELECT COUNT(*) FROM games WHERE ("player" won) AND (queen sacrificed)',
            
            # Variant queries
            "SELECT * FROM games WHERE variant = 'standard'",
            "SELECT * FROM games WHERE variant = 'chess960'",
            "SELECT COUNT(*) FROM games WHERE variant = 'standard' AND (player won)",
            "SELECT variant, COUNT(*) as count FROM games GROUP BY variant",
        ]