"""
Enhanced Chess Piece Analysis Module
Analyzes chess moves with position tracking to accurately detect captures and exchanges.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Piece:
    """Represents a chess piece with its value."""
    symbol: str
    name: str
    value: int


class ChessPieceAnalyzer:
    """Analyzes chess moves with position tracking for accurate piece events."""
    
    # Piece definitions with values
    PIECES = {
        'P': Piece('P', 'pawn', 1),
        'B': Piece('B', 'bishop', 3),
        'N': Piece('N', 'knight', 3),
        'R': Piece('R', 'rook', 5),
        'Q': Piece('Q', 'queen', 9),
        'K': Piece('K', 'king', 0),  # King has no exchange value
    }
    
    def __init__(self):
        """Initialize the enhanced piece analyzer."""
        self.piece_values = {piece.symbol: piece.value for piece in self.PIECES.values()}
        self.piece_names = {piece.symbol: piece.name for piece in self.PIECES.values()}
        self.board = self._init_board()
    
    def _init_board(self):
        """Initialize starting chess board position."""
        board = {}
        # Standard starting position
        for file in 'abcdefgh':
            for rank in range(1, 9):
                square = f"{file}{rank}"
                if rank == 2:
                    board[square] = 'P'  # White pawns
                elif rank == 7:
                    board[square] = 'p'  # Black pawns
                elif rank == 1:
                    if file in 'a,h':
                        board[square] = 'R'  # White rooks
                    elif file in 'b,g':
                        board[square] = 'N'  # White knights
                    elif file in 'c,f':
                        board[square] = 'B'  # White bishops
                    elif file == 'd':
                        board[square] = 'Q'  # White queen
                    elif file == 'e':
                        board[square] = 'K'  # White king
                elif rank == 8:
                    if file in 'a,h':
                        board[square] = 'r'  # Black rooks
                    elif file in 'b,g':
                        board[square] = 'n'  # Black knights
                    elif file in 'c,f':
                        board[square] = 'b'  # Black bishops
                    elif file == 'd':
                        board[square] = 'q'  # Black queen
                    elif file == 'e':
                        board[square] = 'k'  # Black king
                else:
                    board[square] = None
        return board
    
    def reset_board(self):
        """Reset board to starting position."""
        self.board = self._init_board()
    
    def parse_moves_with_captures(self, moves_text: str) -> List[Dict[str, Any]]:
        """Parse moves and track captures with position information."""
        moves = []
        self.reset_board()
        
        # Remove result markers
        moves_text = re.sub(r'\s+(1-0|0-1|1/2-1/2|\*)\s*$', '', moves_text)
        
        # Split by move numbers
        move_blocks = re.split(r'(\d+\.)', moves_text)
        
        # Process each move block
        for i in range(1, len(move_blocks), 2):
            if i + 1 < len(move_blocks):
                move_num = move_blocks[i].strip(' .')
                move_text = move_blocks[i + 1].strip()
                
                # Split white and black moves
                move_parts = move_text.split()
                white_move = move_parts[0] if len(move_parts) > 0 else ''
                black_move = move_parts[1] if len(move_parts) > 1 else ''
                
                # Parse white move (both regular and capture)
                white_capture = self._parse_move(white_move, 'white', int(move_num))
                
                # Parse black move (both regular and capture)
                black_capture = self._parse_move(black_move, 'black', int(move_num)) if black_move else None
                
                moves.append({
                    'move_number': int(move_num),
                    'white_move': white_move,
                    'black_move': black_move,
                    'white_capture': white_capture,
                    'black_capture': black_capture,
                })
        
        return moves
    
    def _parse_move(self, move: str, side: str, move_number: int) -> Optional[Dict[str, Any]]:
        """Parse a single move and update board position. Return capture info if it's a capture."""
        if not move or move in ['O-O', 'O-O-O']:
            # Handle castling
            if move == 'O-O':
                # Kingside castling
                if side == 'white':
                    self.board['e1'] = None
                    self.board['f1'] = 'R'
                    self.board['g1'] = 'K'
                    self.board['h1'] = None
                else:
                    self.board['e8'] = None
                    self.board['f8'] = 'r'
                    self.board['g8'] = 'k'
                    self.board['h8'] = None
            elif move == 'O-O-O':
                # Queenside castling
                if side == 'white':
                    self.board['e1'] = None
                    self.board['d1'] = 'R'
                    self.board['c1'] = 'K'
                    self.board['a1'] = None
                else:
                    self.board['e8'] = None
                    self.board['d8'] = 'r'
                    self.board['c8'] = 'k'
                    self.board['a8'] = None
            return None
        
        # Extract piece and destination
        piece = self._extract_piece_from_move(move)
        destination = self._extract_destination_square(move)
        
        if not destination:
            return None
        
        # Determine source square
        source_square = self._determine_source_square(move, piece, destination, side)
        
        # Check if it's a capture
        if 'x' in move:
            # Determine what piece is being captured
            captured_piece = self.board.get(destination)
            if not captured_piece:
                return None
            
            # Convert to uppercase for consistency
            captured_piece = captured_piece.upper()
            
            # Update board
            self.board[destination] = piece if side == 'white' else piece.lower()
            if source_square:
                self.board[source_square] = None
            
            # Get piece values for later analysis
            piece_value = self.piece_values.get(piece, 0)
            captured_value = self.piece_values.get(captured_piece, 0)
            
            # Initial values - will be updated by _analyze_sacrifices
            is_exchange = False
            is_sacrifice = False
            
            return {
                'move_number': move_number,
                'side': side,
                'capturing_piece': piece,
                'captured_piece': captured_piece,
                'from_square': source_square,
                'to_square': destination,
                'move_notation': move,
                'piece_value': piece_value,
                'captured_value': captured_value,
                'is_exchange': is_exchange,
                'is_sacrifice': is_sacrifice,
            }
        else:
            # Regular move - update board position
            self.board[destination] = piece if side == 'white' else piece.lower()
            if source_square:
                self.board[source_square] = None
            return None
    
    def _parse_capture_move(self, move: str, side: str, move_number: int) -> Optional[Dict[str, Any]]:
        """Parse a single move and determine if it's a capture."""
        if not move or move in ['O-O', 'O-O-O']:
            return None
        
        # Check if it's a capture
        if 'x' not in move:
            return None
        
        # Extract piece and destination
        piece = self._extract_piece_from_move(move)
        destination = self._extract_destination_square(move)
        
        if not destination:
            return None
        
        # Determine what piece is being captured
        captured_piece = self.board.get(destination)
        if not captured_piece:
            return None
        
        # Convert to uppercase for consistency
        captured_piece = captured_piece.upper()
        
        # Determine source square (simplified)
        source_square = self._determine_source_square(move, piece, destination, side)
        
        # Update board
        self.board[destination] = piece if side == 'white' else piece.lower()
        if source_square:
            self.board[source_square] = None
        
        # Get piece values for later analysis
        piece_value = self.piece_values.get(piece, 0)
        captured_value = self.piece_values.get(captured_piece, 0)
        
        # Initial values - will be updated by _analyze_sacrifices
        is_exchange = False
        is_sacrifice = False
        
        return {
            'move_number': move_number,
            'side': side,
            'capturing_piece': piece,
            'captured_piece': captured_piece,
            'from_square': source_square,
            'to_square': destination,
            'move_notation': move,
            'piece_value': piece_value,
            'captured_value': captured_value,
            'is_exchange': is_exchange,
            'is_sacrifice': is_sacrifice,
        }
    
    def _extract_piece_from_move(self, move: str) -> str:
        """Extract piece symbol from a move."""
        if not move or move in ['O-O', 'O-O-O']:
            return 'K'  # Castling involves king
        
        # Check for piece symbols at the start of the move
        if move[0] in self.PIECES:
            return move[0]
        
        # If no piece symbol, it's a pawn move
        return 'P'
    
    def _extract_destination_square(self, move: str) -> Optional[str]:
        """Extract destination square from a move."""
        # Remove piece symbols and capture indicators
        clean_move = re.sub(r'^[KQRBN]', '', move)
        clean_move = re.sub(r'[+#]', '', clean_move)
        
        # For pawn captures like "exd5", remove the source file
        if 'x' in clean_move and len(clean_move) >= 4:
            # Pattern: file + x + square (e.g., "exd5" -> "d5")
            pawn_capture_match = re.match(r'^([a-h])x([a-h][1-8])', clean_move)
            if pawn_capture_match:
                return pawn_capture_match.group(2)
        
        # Extract square pattern (letter + number)
        square_match = re.search(r'([a-h][1-8])', clean_move)
        if square_match:
            return square_match.group(1)
        
        return None
    
    def _determine_source_square(self, move: str, piece: str, destination: str, side: str) -> Optional[str]:
        """Determine source square for a move."""
        # Handle special cases
        if move in ['O-O', 'O-O-O']:
            return None
        
        # Find all squares where this piece could be
        possible_sources = []
        piece_symbol = piece if side == 'white' else piece.lower()
        
        for square, board_piece in self.board.items():
            if board_piece == piece_symbol:
                possible_sources.append(square)
        
        if not possible_sources:
            return None
        
        # If only one possible source, use it
        if len(possible_sources) == 1:
            return possible_sources[0]
        
        # For moves with disambiguation (like Nbd2, R1a1, etc.)
        if len(move) > 3 and move[1] in 'abcdefgh12345678':
            disambiguation = move[1]
            if disambiguation in 'abcdefgh':
                # File disambiguation (e.g., Nbd2)
                for square in possible_sources:
                    if square[0] == disambiguation:
                        return square
            elif disambiguation in '12345678':
                # Rank disambiguation (e.g., N1d2)
                for square in possible_sources:
                    if square[1] == disambiguation:
                        return square
        
        # For captures, try to find the piece that can legally capture on the destination
        if 'x' in move:
            for square in possible_sources:
                if self._can_piece_capture_from_square(piece, square, destination, side):
                    return square
        
        # For regular moves, try to find the piece that can legally move to the destination
        for square in possible_sources:
            if self._can_piece_move_from_square(piece, square, destination, side):
                return square
        
        # If we can't determine, return the first possible source
        return possible_sources[0]
    
    def _can_piece_capture_from_square(self, piece: str, source: str, destination: str, side: str) -> bool:
        """Check if a piece can legally capture from source to destination."""
        # This is a simplified check - in a real engine this would be more complex
        if piece == 'P':
            # Pawn capture
            if side == 'white':
                return (ord(destination[0]) - ord(source[0])) == 1 and (int(destination[1]) - int(source[1])) == 1
            else:
                return (ord(destination[0]) - ord(source[0])) == 1 and (int(source[1]) - int(destination[1])) == 1
        else:
            # For other pieces, just check if it's a reasonable distance
            return True  # Simplified for now
    
    def _can_piece_move_from_square(self, piece: str, source: str, destination: str, side: str) -> bool:
        """Check if a piece can legally move from source to destination."""
        # This is a simplified check - in a real engine this would be more complex
        return True  # Simplified for now
    
    def analyze_captures(self, moves_text: str, white_player: str = None, black_player: str = None) -> List[Dict[str, Any]]:
        """Analyze moves to find all captures with detailed information."""
        moves = self.parse_moves_with_captures(moves_text)
        captures = []
        
        for move in moves:
            if move['white_capture']:
                move['white_capture']['white_player'] = white_player
                move['white_capture']['black_player'] = black_player
                captures.append(move['white_capture'])
            if move['black_capture']:
                move['black_capture']['white_player'] = white_player
                move['black_capture']['black_player'] = black_player
                captures.append(move['black_capture'])
        
        # Analyze sacrifices by looking at consecutive captures
        self._analyze_sacrifices(captures)
        
        return captures
    
    def _analyze_sacrifices(self, captures: List[Dict[str, Any]]) -> None:
        """Analyze sacrifices by looking at queen captures and opponent queen status."""
        # Reset all sacrifice flags first
        for capture in captures:
            capture['is_sacrifice'] = False
            capture['is_exchange'] = False
        
        # Group captures by move number for analysis
        captures_by_move = {}
        for capture in captures:
            move_num = capture['move_number']
            if move_num not in captures_by_move:
                captures_by_move[move_num] = []
            captures_by_move[move_num].append(capture)
        
        # Analyze queen sacrifices
        for move_num in sorted(captures_by_move.keys()):
            current_captures = captures_by_move[move_num]
            
            # Look for queen captures in this move
            for capture in current_captures:
                if capture['captured_piece'] == 'Q':
                    # Check if this is a queen sacrifice
                    # A queen sacrifice means: lecorvus' queen is captured AND opponent's queen survives
                    if self._is_queen_sacrifice(capture, captures_by_move, move_num):
                        capture['is_sacrifice'] = True
                    elif self._is_queen_exchange(capture, captures_by_move, move_num):
                        capture['is_exchange'] = True
    
    def _is_queen_sacrifice(self, queen_capture: Dict[str, Any], captures_by_move: Dict[int, List[Dict]], move_num: int) -> bool:
        """Check if a queen capture is a sacrifice (opponent's queen survives)."""
        # Get the side that captured the queen
        capturing_side = queen_capture['side']
        lecorvus_side = 'white' if queen_capture.get('white_player') == 'lecorvus' else 'black'
        
        # If lecorvus' queen was captured, check if lecorvus captures opponent's queen soon after
        if capturing_side != lecorvus_side:
            # lecorvus' queen was captured - check if lecorvus captures opponent's queen soon after
            for check_move in range(move_num, min(move_num + 3, max(captures_by_move.keys()) + 1)):
                if check_move in captures_by_move:
                    for capture in captures_by_move[check_move]:
                        if capture['side'] == lecorvus_side and capture['captured_piece'] == 'Q':
                            # lecorvus captured opponent's queen soon after, so this is not a sacrifice
                            return False
            
            # Also check if lecorvus captured opponent's queen before this move
            for check_move in range(1, move_num):
                if check_move in captures_by_move:
                    for capture in captures_by_move[check_move]:
                        if capture['side'] == lecorvus_side and capture['captured_piece'] == 'Q':
                            # lecorvus already captured opponent's queen earlier, so this is not a sacrifice
                            return False
            
            # If we get here, lecorvus didn't capture opponent's queen before or soon after, so this is a sacrifice
            return True
        
        # If opponent's queen was captured, check if opponent captures lecorvus' queen soon after
        elif capturing_side == lecorvus_side:
            # opponent's queen was captured - check if opponent captures lecorvus' queen soon after
            for check_move in range(move_num, min(move_num + 3, max(captures_by_move.keys()) + 1)):
                if check_move in captures_by_move:
                    for capture in captures_by_move[check_move]:
                        if capture['side'] != lecorvus_side and capture['captured_piece'] == 'Q':
                            # opponent captured lecorvus' queen soon after, so this is not a sacrifice
                            return False
            
            # Also check if opponent captured lecorvus' queen before this move
            for check_move in range(1, move_num):
                if check_move in captures_by_move:
                    for capture in captures_by_move[check_move]:
                        if capture['side'] != lecorvus_side and capture['captured_piece'] == 'Q':
                            # opponent already captured lecorvus' queen earlier, so this is not a sacrifice
                            return False
            
            # If we get here, opponent didn't capture lecorvus' queen before or soon after, so this is a sacrifice
            return True
        
        return False
    
    def _is_queen_exchange(self, queen_capture: Dict[str, Any], captures_by_move: Dict[int, List[Dict]], move_num: int) -> bool:
        """Check if a queen capture is an exchange (opponent's queen is captured soon after)."""
        # Get the side that captured the queen
        capturing_side = queen_capture['side']
        lecorvus_side = 'white' if queen_capture.get('white_player') == 'lecorvus' else 'black'
        
        # If lecorvus' queen was captured, check if lecorvus captures opponent's queen soon after
        if capturing_side != lecorvus_side:
            # lecorvus' queen was captured - check if lecorvus captures opponent's queen soon after
            for check_move in range(move_num, min(move_num + 2, max(captures_by_move.keys()) + 1)):
                if check_move in captures_by_move:
                    for capture in captures_by_move[check_move]:
                        if capture['side'] == lecorvus_side and capture['captured_piece'] == 'Q':
                            # lecorvus captured opponent's queen soon after, so this is an exchange
                            return True
        
        return False
    
    def get_capture_statistics(self, moves_text: str) -> Dict[str, Any]:
        """Get statistics about captures in a game."""
        captures = self.analyze_captures(moves_text)
        
        stats = {
            'total_captures': len(captures),
            'exchanges': len([c for c in captures if c['is_exchange']]),
            'sacrifices': len([c for c in captures if c['is_sacrifice']]),
            'captures_by_piece': {},
            'exchanges_by_piece': {},
            'sacrifices_by_piece': {},
        }
        
        # Count captures by piece type
        for capture in captures:
            piece = capture['capturing_piece']
            stats['captures_by_piece'][piece] = stats['captures_by_piece'].get(piece, 0) + 1
            
            if capture['is_exchange']:
                stats['exchanges_by_piece'][piece] = stats['exchanges_by_piece'].get(piece, 0) + 1
            
            if capture['is_sacrifice']:
                stats['sacrifices_by_piece'][piece] = stats['sacrifices_by_piece'].get(piece, 0) + 1
        
        return stats
