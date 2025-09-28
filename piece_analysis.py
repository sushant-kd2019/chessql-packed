"""
Chess Piece Analysis Module
Analyzes chess moves to detect piece exchanges, sacrifices, and other events.
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
    """Analyzes chess moves for piece events."""
    
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
        """Initialize the piece analyzer."""
        self.piece_values = {piece.symbol: piece.value for piece in self.PIECES.values()}
        self.piece_names = {piece.symbol: piece.name for piece in self.PIECES.values()}
    
    def parse_moves(self, moves_text: str) -> List[Dict[str, Any]]:
        """Parse moves from PGN notation and extract piece information."""
        moves = []
        
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
                
                # Parse white move
                white_piece = self._extract_piece_from_move(white_move)
                white_captured = self._extract_captured_piece(white_move)
                
                # Parse black move
                black_piece = self._extract_piece_from_move(black_move) if black_move else None
                black_captured = self._extract_captured_piece(black_move) if black_move else None
                
                moves.append({
                    'move_number': int(move_num),
                    'white_move': white_move,
                    'black_move': black_move,
                    'white_piece': white_piece,
                    'black_piece': black_piece,
                    'white_captured': white_captured,
                    'black_captured': black_captured,
                    'white_piece_value': self.piece_values.get(white_piece, 0),
                    'black_piece_value': self.piece_values.get(black_piece, 0) if black_piece else 0,
                    'white_captured_value': self.piece_values.get(white_captured, 0) if white_captured else 0,
                    'black_captured_value': self.piece_values.get(black_captured, 0) if black_captured else 0,
                })
        
        return moves
    
    def _extract_piece_from_move(self, move: str) -> Optional[str]:
        """Extract piece symbol from a move."""
        if not move or move in ['O-O', 'O-O-O']:
            return 'K'  # Castling involves king
        
        # Check for piece symbols at the start of the move
        if move[0] in self.PIECES:
            return move[0]
        
        # If no piece symbol, it's a pawn move
        return 'P'
    
    def _extract_captured_piece(self, move: str) -> Optional[str]:
        """Extract captured piece from a move (indicated by 'x')."""
        if 'x' in move:
            # For captures, we can't determine the captured piece from PGN alone
            # This would require position analysis, so we return None for now
            # But we can at least detect that a capture occurred
            return 'P'  # Assume pawn capture for now - this is a simplification
        return None
    
    def analyze_events(self, moves: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze moves to detect piece events."""
        events = []
        
        for move in moves:
            # Detect piece exchanges (same value pieces)
            if self._is_piece_exchange(move):
                events.append({
                    'move_number': move['move_number'],
                    'event_type': 'piece_exchange',
                    'piece': move['white_piece'],
                    'piece_name': self.piece_names.get(move['white_piece'], 'unknown'),
                    'piece_value': move['white_piece_value'],
                    'move': move['white_move'],
                    'side': 'white'
                })
            
            if move['black_piece'] and self._is_piece_exchange(move, side='black'):
                events.append({
                    'move_number': move['move_number'],
                    'event_type': 'piece_exchange',
                    'piece': move['black_piece'],
                    'piece_name': self.piece_names.get(move['black_piece'], 'unknown'),
                    'piece_value': move['black_piece_value'],
                    'move': move['black_move'],
                    'side': 'black'
                })
            
            # Detect piece sacrifices (higher value for lower value)
            if self._is_piece_sacrifice(move):
                events.append({
                    'move_number': move['move_number'],
                    'event_type': 'piece_sacrifice',
                    'piece': move['white_piece'],
                    'piece_name': self.piece_names.get(move['white_piece'], 'unknown'),
                    'piece_value': move['white_piece_value'],
                    'move': move['white_move'],
                    'side': 'white'
                })
            
            if move['black_piece'] and self._is_piece_sacrifice(move, side='black'):
                events.append({
                    'move_number': move['move_number'],
                    'event_type': 'piece_sacrifice',
                    'piece': move['black_piece'],
                    'piece_name': self.piece_names.get(move['black_piece'], 'unknown'),
                    'piece_value': move['black_piece_value'],
                    'move': move['black_move'],
                    'side': 'black'
                })
        
        return events
    
    def _is_piece_exchange(self, move: Dict[str, Any], side: str = 'white') -> bool:
        """Check if a move represents a piece exchange."""
        # This is a simplified check - in reality, we'd need position analysis
        # to determine if pieces of equal value were exchanged
        piece = move[f'{side}_piece']
        captured = move[f'{side}_captured']
        
        if not piece or not captured:
            return False
        
        return self.piece_values.get(piece, 0) == self.piece_values.get(captured, 0)
    
    def _is_piece_sacrifice(self, move: Dict[str, Any], side: str = 'white') -> bool:
        """Check if a move represents a piece sacrifice."""
        # This is a simplified check - in reality, we'd need position analysis
        piece = move[f'{side}_piece']
        captured = move[f'{side}_captured']
        
        if not piece or not captured:
            return False
        
        return self.piece_values.get(piece, 0) > self.piece_values.get(captured, 0)
    
    def find_piece_events(self, moves_text: str, event_type: str = None, piece: str = None, 
                         max_move: int = None) -> List[Dict[str, Any]]:
        """Find specific piece events in a game."""
        moves = self.parse_moves(moves_text)
        events = self.analyze_events(moves)
        
        # Filter by event type
        if event_type:
            events = [e for e in events if e['event_type'] == event_type]
        
        # Filter by piece
        if piece:
            events = [e for e in events if e['piece'] == piece.upper()]
        
        # Filter by move number
        if max_move:
            events = [e for e in events if e['move_number'] <= max_move]
        
        return events
    
    def get_piece_statistics(self, moves_text: str) -> Dict[str, Any]:
        """Get statistics about pieces in a game."""
        moves = self.parse_moves(moves_text)
        events = self.analyze_events(moves)
        
        stats = {
            'total_moves': len(moves),
            'exchanges': len([e for e in events if e['event_type'] == 'piece_exchange']),
            'sacrifices': len([e for e in events if e['event_type'] == 'piece_sacrifice']),
            'pieces_exchanged': {},
            'pieces_sacrificed': {},
        }
        
        # Count pieces by type
        for event in events:
            piece = event['piece']
            if event['event_type'] == 'piece_exchange':
                stats['pieces_exchanged'][piece] = stats['pieces_exchanged'].get(piece, 0) + 1
            elif event['event_type'] == 'piece_sacrifice':
                stats['pieces_sacrificed'][piece] = stats['pieces_sacrificed'].get(piece, 0) + 1
        
        return stats
