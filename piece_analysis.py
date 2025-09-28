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
            return None
        
        # Extract piece and destination
        piece = self._extract_piece_from_move(move)
        destination = self._extract_destination_square(move)
        
        if not destination:
            return None
        
        # Check if it's a capture
        if 'x' in move:
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
            
            # Determine if it's an exchange or sacrifice
            piece_value = self.piece_values.get(piece, 0)
            captured_value = self.piece_values.get(captured_piece, 0)
            
            is_exchange = piece_value == captured_value
            is_sacrifice = piece_value > captured_value
            
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
            # Regular move - just update board position
            self.board[destination] = piece if side == 'white' else piece.lower()
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
        
        # Determine if it's an exchange or sacrifice
        piece_value = self.piece_values.get(piece, 0)
        captured_value = self.piece_values.get(captured_piece, 0)
        
        is_exchange = piece_value == captured_value
        is_sacrifice = piece_value > captured_value
        
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
        """Determine source square for a move (simplified)."""
        # This is a simplified implementation
        # In a real chess engine, this would require complex position analysis
        
        # For now, we'll use a simple heuristic
        # This is not perfect but better than nothing
        return None  # We'll leave this as None for now
    
    def analyze_captures(self, moves_text: str) -> List[Dict[str, Any]]:
        """Analyze moves to find all captures with detailed information."""
        moves = self.parse_moves_with_captures(moves_text)
        captures = []
        
        for move in moves:
            if move['white_capture']:
                captures.append(move['white_capture'])
            if move['black_capture']:
                captures.append(move['black_capture'])
        
        return captures
    
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
