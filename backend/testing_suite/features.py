"""
Feature catalog for NL to CQL conversion testing.

This module defines all supported features that can be queried.
"""

from typing import List, Dict, Any
from enum import Enum


class FeatureCategory(Enum):
    """Categories of features."""
    PLAYER_RESULTS = "player_results"
    PIECE_EVENTS = "piece_events"
    GAME_METADATA = "game_metadata"
    QUERY_OPERATIONS = "query_operations"
    FILTERING = "filtering"


class Feature:
    """Represents a testable feature."""
    
    def __init__(
        self,
        name: str,
        category: FeatureCategory,
        description: str,
        examples: List[str],
        cql_patterns: List[str]
    ):
        """Initialize a feature.
        
        Args:
            name: Feature name
            category: Feature category
            description: Description of what the feature does
            examples: Example natural language queries
            cql_patterns: Example CQL patterns used
        """
        self.name = name
        self.category = category
        self.description = description
        self.examples = examples
        self.cql_patterns = cql_patterns
    
    def __repr__(self):
        return f"Feature(name='{self.name}', category={self.category.value})"


# Define all supported features
FEATURES: List[Feature] = [
    # Player Results
    Feature(
        name="Player Results (won/lost/drew)",
        category=FeatureCategory.PLAYER_RESULTS,
        description="Query games by player outcome (win, loss, draw)",
        examples=[
            "Show me games where I won",
            "Find games where I lost",
            "Games that ended in a draw"
        ],
        cql_patterns=[
            "(player_name won)",
            "(player_name lost)",
            "(player_name drew)"
        ]
    ),
    
    # Piece Sacrifices
    Feature(
        name="Piece Sacrifices",
        category=FeatureCategory.PIECE_EVENTS,
        description="Query games where pieces were sacrificed (queen, rook, bishop, knight, pawn)",
        examples=[
            "Show me games where queen was sacrificed",
            "Find games where I sacrificed my knight"
        ],
        cql_patterns=[
            "(queen sacrificed)",
            "(player_name queen sacrificed)",
            "(knight sacrificed)"
        ]
    ),
    
    # Piece Exchanges
    Feature(
        name="Piece Exchanges",
        category=FeatureCategory.PIECE_EVENTS,
        description="Query games where pieces were exchanged",
        examples=[
            "Find games with queen exchanges",
            "Show games where pawns were exchanged"
        ],
        cql_patterns=[
            "(queen exchanged)",
            "(pawn exchanged)"
        ]
    ),
    
    # Captures
    Feature(
        name="Captures",
        category=FeatureCategory.PIECE_EVENTS,
        description="Query games with specific piece captures (piece1 captured piece2)",
        examples=[
            "Show games where knight captured rook",
            "Find games where bishop captured queen"
        ],
        cql_patterns=[
            "(knight captured rook)",
            "(bishop captured queen)"
        ]
    ),
    
    # Pawn Promotions
    Feature(
        name="Pawn Promotions",
        category=FeatureCategory.PIECE_EVENTS,
        description="Query games with pawn promotions (to queen/rook/bishop/knight, with x N for multiple)",
        examples=[
            "Find games where pawn was promoted to queen",
            "Show games with pawn promoted to queen x 2"
        ],
        cql_patterns=[
            "(pawn promoted to queen)",
            "(pawn promoted to queen x 2)"
        ]
    ),
    
    # Move Timing
    Feature(
        name="Move Timing",
        category=FeatureCategory.PIECE_EVENTS,
        description="Query events that occurred before/after a specific move number",
        examples=[
            "Find pawn exchanges before move 10",
            "Show queen sacrifices after move 20"
        ],
        cql_patterns=[
            "(pawn exchanged before move 10)",
            "(queen sacrificed after move 20)"
        ]
    ),
    
    # ELO Rating
    Feature(
        name="ELO Rating Queries",
        category=FeatureCategory.GAME_METADATA,
        description="Query games by player ELO rating",
        examples=[
            "Games where I was rated over 1500",
            "Find games where I was rated under 1200"
        ],
        cql_patterns=[
            "CAST(white_elo AS INTEGER) > 1500",
            "CAST(black_elo AS INTEGER) < 1200"
        ]
    ),
    
    # Time Control/Speed
    Feature(
        name="Time Control/Speed",
        category=FeatureCategory.GAME_METADATA,
        description="Query games by time control category (ultraBullet, bullet, blitz, rapid, classical)",
        examples=[
            "Show my blitz games",
            "How many bullet games did I win"
        ],
        cql_patterns=[
            "speed = 'blitz'",
            "speed = 'bullet'"
        ]
    ),
    
    # Variant
    Feature(
        name="Variant",
        category=FeatureCategory.GAME_METADATA,
        description="Query games by chess variant (standard, chess960)",
        examples=[
            "Show my chess960 games",
            "How many standard games have I won"
        ],
        cql_patterns=[
            "variant = 'chess960'",
            "variant = 'standard'"
        ]
    ),
    
    # Platform Filtering
    Feature(
        name="Platform Filtering",
        category=FeatureCategory.FILTERING,
        description="Filter games by platform (lichess, chesscom)",
        examples=[
            "Show my Lichess games",
            "Find my Chess.com wins"
        ],
        cql_patterns=[
            "lichess_id IS NOT NULL",
            "chesscom_id IS NOT NULL"
        ]
    ),
    
    # Account Filtering
    Feature(
        name="Account Filtering",
        category=FeatureCategory.FILTERING,
        description="Filter games by account ID",
        examples=[
            "Show games from my account"
        ],
        cql_patterns=[
            "account_id = 1"
        ]
    ),
    
    # Sorting
    Feature(
        name="Sorting",
        category=FeatureCategory.QUERY_OPERATIONS,
        description="Sort query results (ORDER BY)",
        examples=[
            "Show games sorted by ELO rating",
            "Find most recent games"
        ],
        cql_patterns=[
            "ORDER BY CAST(white_elo AS INTEGER) DESC",
            "ORDER BY date_played DESC"
        ]
    ),
    
    # Counting
    Feature(
        name="Counting",
        category=FeatureCategory.QUERY_OPERATIONS,
        description="Count games matching conditions (COUNT)",
        examples=[
            "How many games did I win",
            "Count games where queen was sacrificed"
        ],
        cql_patterns=[
            "SELECT COUNT(*) FROM games WHERE ..."
        ]
    ),
    
    # Grouping
    Feature(
        name="Grouping",
        category=FeatureCategory.QUERY_OPERATIONS,
        description="Group and aggregate results (GROUP BY)",
        examples=[
            "Show games by speed category",
            "Show games by variant"
        ],
        cql_patterns=[
            "SELECT speed, COUNT(*) as count FROM games GROUP BY speed"
        ]
    ),
    
    # Combined Queries
    Feature(
        name="Combined Queries",
        category=FeatureCategory.QUERY_OPERATIONS,
        description="Multiple conditions combined with AND/OR",
        examples=[
            "Games where I sacrificed a queen and won",
            "My blitz games where I promoted to queen"
        ],
        cql_patterns=[
            "(player_name won) AND (queen sacrificed)",
            "(player_name won) AND speed = 'blitz' AND (pawn promoted to queen)"
        ]
    ),
]


def get_feature_by_name(name: str) -> Feature:
    """Get a feature by name."""
    for feature in FEATURES:
        if feature.name == name:
            return feature
    raise ValueError(f"Feature '{name}' not found")


def get_features_by_category(category: FeatureCategory) -> List[Feature]:
    """Get all features in a category."""
    return [f for f in FEATURES if f.category == category]


def list_all_features() -> List[str]:
    """List all feature names."""
    return [f.name for f in FEATURES]

