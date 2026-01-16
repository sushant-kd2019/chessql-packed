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
    
    def __init__(self, reference_player: str = "lecorvus"):
        """Initialize the enhanced piece analyzer."""
        self.piece_values = {piece.symbol: piece.value for piece in self.PIECES.values()}
        self.piece_names = {piece.symbol: piece.name for piece in self.PIECES.values()}
        self.board = self._init_board()
        self.reference_player = reference_player
    
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
        """Parse moves and track captures with position information.
        
        Supports both formats:
        - PGN format with move numbers: "1. e4 e5 2. Nf3 Nc6"
        - Lichess format without move numbers: "e4 e5 Nf3 Nc6"
        """
        moves = []
        self.reset_board()
        
        # Remove result markers
        moves_text = re.sub(r'\s+(1-0|0-1|1/2-1/2|\*)\s*$', '', moves_text)
        
        # Check if moves have move numbers (PGN format) or not (Lichess format)
        has_move_numbers = bool(re.search(r'\d+\.', moves_text))
        
        if has_move_numbers:
            # PGN format with move numbers: "1. e4 e5 2. Nf3 Nc6"
            move_blocks = re.split(r'(\d+\.)', moves_text)
            
            for i in range(1, len(move_blocks), 2):
                if i + 1 < len(move_blocks):
                    move_num = move_blocks[i].strip(' .')
                    move_text = move_blocks[i + 1].strip()
                    
                    move_parts = move_text.split()
                    white_move = move_parts[0] if len(move_parts) > 0 else ''
                    black_move = move_parts[1] if len(move_parts) > 1 else ''
                    
                    white_capture, black_capture = self._parse_move_pair(
                        white_move, black_move, 'white', 'black', int(move_num)
                    )
                    
                    moves.append({
                        'move_number': int(move_num),
                        'white_move': white_move,
                        'black_move': black_move,
                        'white_capture': white_capture,
                        'black_capture': black_capture,
                    })
        else:
            # Lichess format without move numbers: "e4 e5 Nf3 Nc6"
            all_moves = moves_text.split()
            move_num = 0
            
            for i in range(0, len(all_moves), 2):
                move_num += 1
                white_move = all_moves[i] if i < len(all_moves) else ''
                black_move = all_moves[i + 1] if i + 1 < len(all_moves) else ''
                
                white_capture, black_capture = self._parse_move_pair(
                    white_move, black_move, 'white', 'black', move_num
                )
                
                moves.append({
                    'move_number': move_num,
                    'white_move': white_move,
                    'black_move': black_move,
                    'white_capture': white_capture,
                    'black_capture': black_capture,
                })
        
        return moves
    
    def _parse_move_pair(self, white_move: str, black_move: str, white_side: str, black_side: str, move_number: int) -> tuple:
        """Parse a pair of moves (white and black) sequentially."""
        white_capture = None
        black_capture = None
        
        # Handle castling first
        if white_move in ['O-O', 'O-O-O']:
            self._handle_castling(white_move, white_side)
        elif black_move in ['O-O', 'O-O-O']:
            self._handle_castling(black_move, black_side)
        
        # Parse white move first
        if white_move and white_move not in ['O-O', 'O-O-O']:
            white_capture = self._parse_single_move(white_move, white_side, move_number)
        
        # Parse black move second (board state has been updated by white move)
        if black_move and black_move not in ['O-O', 'O-O-O']:
            black_capture = self._parse_single_move(black_move, black_side, move_number)
        
        return white_capture, black_capture
    
    def _handle_castling(self, move: str, side: str):
        """Handle castling moves."""
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
    
    def _parse_single_move(self, move: str, side: str, move_number: int) -> Optional[Dict[str, Any]]:
        """Parse a single move and update board position. Return capture info if it's a capture."""
        if not move or move in ['O-O', 'O-O-O']:
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
                # If no piece on destination, this might be en passant or an error
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
            # Regular move (no capture) - still update board
            self.board[destination] = piece if side == 'white' else piece.lower()
            if source_square:
                self.board[source_square] = None
        
        return None
    
    # Old _parse_move method removed - now using _parse_single_move
    
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
        
        # Check for pawn promotion (e.g., "bxa8=Q", "e8=Q", "dxe1=Q+")
        if '=' in move:
            # Extract the promoted piece (e.g., "Q" from "bxa8=Q")
            promoted_piece = move.split('=')[-1]
            # Remove check/checkmate symbols (+ and #)
            promoted_piece = promoted_piece.replace('+', '').replace('#', '')
            if promoted_piece in self.PIECES:
                return promoted_piece
        
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
        
        # For pawn captures like "exd4", the source file is explicitly given in the notation
        if piece == 'P' and 'x' in move:
            pawn_capture_match = re.match(r'^([a-h])x([a-h][1-8])', move)
            if pawn_capture_match:
                source_file = pawn_capture_match.group(1)
                piece_symbol = 'P' if side == 'white' else 'p'
                # Find the pawn on that file that can capture to destination
                for square, board_piece in self.board.items():
                    if board_piece == piece_symbol and square[0] == source_file:
                        if self._can_piece_capture_from_square(piece, square, destination, side):
                            return square
        
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
            # Pawn capture - pawns capture diagonally (one file left or right, one rank forward)
            file_diff = abs(ord(destination[0]) - ord(source[0]))
            if side == 'white':
                rank_diff = int(destination[1]) - int(source[1])
                return file_diff == 1 and rank_diff == 1
            else:
                rank_diff = int(source[1]) - int(destination[1])
                return file_diff == 1 and rank_diff == 1
        else:
            # For other pieces, just check if it's a reasonable distance
            return True  # Simplified for now
    
    def _can_piece_move_from_square(self, piece: str, source: str, destination: str, side: str) -> bool:
        """Check if a piece can legally move from source to destination."""
        if not source or not destination:
            return False
        
        source_file, source_rank = source[0], int(source[1])
        dest_file, dest_rank = destination[0], int(destination[1])
        
        file_diff = abs(ord(dest_file) - ord(source_file))
        rank_diff = abs(dest_rank - source_rank)
        
        if piece == 'N':
            # Knight moves in L-shape: 2 squares in one direction, 1 in the other
            return (file_diff == 2 and rank_diff == 1) or (file_diff == 1 and rank_diff == 2)
        elif piece == 'P':
            # Pawn moves forward (simplified - not handling en passant or promotion)
            if side == 'white':
                if source_rank == 2:
                    # Can move 1 or 2 squares forward from starting position
                    return file_diff == 0 and (rank_diff == 1 or rank_diff == 2)
                else:
                    # Can move 1 square forward
                    return file_diff == 0 and rank_diff == 1 and dest_rank > source_rank
            else:
                if source_rank == 7:
                    # Can move 1 or 2 squares forward from starting position
                    return file_diff == 0 and (rank_diff == 1 or rank_diff == 2)
                else:
                    # Can move 1 square forward
                    return file_diff == 0 and rank_diff == 1 and dest_rank < source_rank
        elif piece == 'R':
            # Rook moves horizontally or vertically
            return file_diff == 0 or rank_diff == 0
        elif piece == 'B':
            # Bishop moves diagonally
            return file_diff == rank_diff
        elif piece == 'Q':
            # Queen moves like rook or bishop
            return file_diff == 0 or rank_diff == 0 or file_diff == rank_diff
        elif piece == 'K':
            # King moves one square in any direction
            return file_diff <= 1 and rank_diff <= 1
        
        return False
    
    def analyze_captures(self, moves_text: str, white_player: str = None, black_player: str = None, reference_player: str = None) -> List[Dict[str, Any]]:
        """Analyze moves to find all captures with detailed information."""
        moves = self.parse_moves_with_captures(moves_text)
        captures = []
        
        # Use provided reference_player or fall back to instance default
        ref_player = reference_player or self.reference_player
        
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
        self._analyze_sacrifices(captures, ref_player)
        
        return captures
    
    def _analyze_sacrifices(self, captures: List[Dict[str, Any]], reference_player: str) -> None:
        """Analyze sacrifices and exchanges for all piece types based on material imbalance."""
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
        
        # Analyze all captures for sacrifices/exchanges
        for move_num in sorted(captures_by_move.keys()):
            current_captures = captures_by_move[move_num]
            
            for capture in current_captures:
                captured_piece = capture['captured_piece']
                captured_value = self.piece_values.get(captured_piece, 0)
                
                # Skip if no meaningful piece value (e.g., king)
                if captured_value == 0:
                    continue
                
                # Determine who lost the piece
                capturing_side = capture['side']  # side that made the capture
                ref_player_side = 'white' if capture.get('white_player') == reference_player else 'black'
                
                # Check if this capture results in a sacrifice or exchange
                is_sacrifice, is_exchange = self._analyze_material_trade(
                    capture, captures_by_move, move_num, reference_player, ref_player_side
                )
                
                capture['is_sacrifice'] = is_sacrifice
                capture['is_exchange'] = is_exchange
    
    def _analyze_material_trade(self, capture: Dict[str, Any], captures_by_move: Dict[int, List[Dict]], 
                                  move_num: int, reference_player: str, ref_player_side: str) -> Tuple[bool, bool]:
        """
        Analyze if a capture is a sacrifice or exchange based on material balance.
        
        A sacrifice: The side that lost the piece doesn't get equivalent material back soon.
        An exchange: Both sides trade pieces of similar value within a short window.
        
        Returns: (is_sacrifice, is_exchange)
        """
        captured_piece = capture['captured_piece']
        captured_value = self.piece_values.get(captured_piece, 0)
        capturing_side = capture['side']  # The side that MADE the capture (opponent of who lost the piece)
        losing_side = 'black' if capturing_side == 'white' else 'white'
        
        # Look for compensation within 2 moves (recapture window)
        max_move = max(captures_by_move.keys()) if captures_by_move else move_num
        compensation_value = 0
        
        # Check captures in same move and next move for recaptures
        for check_move in range(move_num, min(move_num + 2, max_move + 1)):
            if check_move in captures_by_move:
                for other_capture in captures_by_move[check_move]:
                    # Skip the original capture we're analyzing
                    if other_capture is capture:
                        continue
                    
                    # Look for recaptures by the side that lost the piece
                    if other_capture['side'] == losing_side:
                        compensation_value += self.piece_values.get(other_capture['captured_piece'], 0)
        
        # Determine if it's a sacrifice or exchange
        # Sacrifice: Lost significantly more material than gained back (at least 2 points difference)
        # Exchange: Traded pieces of similar value (within 1 point)
        material_diff = captured_value - compensation_value
        
        is_sacrifice = material_diff >= 2  # Lost at least 2 points of material
        is_exchange = abs(material_diff) <= 1 and compensation_value > 0  # Traded similar value
        
        return is_sacrifice, is_exchange
    
    def get_capture_statistics(self, moves_text: str, reference_player: str = None) -> Dict[str, Any]:
        """Get statistics about captures in a game."""
        # Use provided reference_player or fall back to instance default
        ref_player = reference_player or self.reference_player
        captures = self.analyze_captures(moves_text, reference_player=ref_player)
        
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
