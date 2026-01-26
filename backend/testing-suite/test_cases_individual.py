"""
Individual feature test cases.

Each feature has 1-2 test questions to validate basic functionality.
"""

from test_cases import TestCase, TestCaseType
from features import FEATURES, get_feature_by_name


def get_individual_test_cases(reference_player: str = "lecorvus") -> list[TestCase]:
    """Get all individual feature test cases.
    
    Args:
        reference_player: The reference player name for queries
    
    Returns:
        List of test cases for individual features
    """
    test_cases = []
    
    # Player Results
    test_cases.extend([
        TestCase(
            id="player_results_001",
            natural_language=f"Show me games where {reference_player} won",
            feature_names=["Player Results (won/lost/drew)"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Basic player win query",
            reference_player=reference_player
        ),
        TestCase(
            id="player_results_002",
            natural_language=f"Find games where {reference_player} lost",
            feature_names=["Player Results (won/lost/drew)"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Basic player loss query",
            reference_player=reference_player
        ),
    ])
    
    # Piece Sacrifices
    test_cases.extend([
        TestCase(
            id="piece_sacrifices_001",
            natural_language="Show me games where queen was sacrificed",
            feature_names=["Piece Sacrifices"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Queen sacrifice query",
            reference_player=reference_player
        ),
        TestCase(
            id="piece_sacrifices_002",
            natural_language="Find games where knight was sacrificed",
            feature_names=["Piece Sacrifices"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Knight sacrifice query",
            reference_player=reference_player
        ),
    ])
    
    # Piece Exchanges
    test_cases.extend([
        TestCase(
            id="piece_exchanges_001",
            natural_language="Find games with queen exchanges",
            feature_names=["Piece Exchanges"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Queen exchange query",
            reference_player=reference_player
        ),
        TestCase(
            id="piece_exchanges_002",
            natural_language="Show games where pawns were exchanged",
            feature_names=["Piece Exchanges"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Pawn exchange query",
            reference_player=reference_player
        ),
    ])
    
    # Captures
    test_cases.extend([
        TestCase(
            id="captures_001",
            natural_language="Show games where knight captured rook",
            feature_names=["Captures"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Knight captures rook query",
            reference_player=reference_player
        ),
        TestCase(
            id="captures_002",
            natural_language="Find games where bishop captured queen",
            feature_names=["Captures"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Bishop captures queen query",
            reference_player=reference_player
        ),
    ])
    
    # Pawn Promotions
    test_cases.extend([
        TestCase(
            id="pawn_promotions_001",
            natural_language="Find games where pawn was promoted to queen",
            feature_names=["Pawn Promotions"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Basic pawn promotion to queen",
            reference_player=reference_player
        ),
        TestCase(
            id="pawn_promotions_002",
            natural_language="Show games with pawn promoted to queen x 2",
            feature_names=["Pawn Promotions"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Multiple pawn promotions",
            reference_player=reference_player
        ),
    ])
    
    # Move Timing
    test_cases.extend([
        TestCase(
            id="move_timing_001",
            natural_language="Find pawn exchanges before move 10",
            feature_names=["Move Timing"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Early move timing condition",
            reference_player=reference_player
        ),
        TestCase(
            id="move_timing_002",
            natural_language="Show queen sacrifices after move 20",
            feature_names=["Move Timing"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Late move timing condition",
            reference_player=reference_player
        ),
    ])
    
    # ELO Rating
    test_cases.extend([
        TestCase(
            id="elo_rating_001",
            natural_language=f"Games where {reference_player} was rated over 1500",
            feature_names=["ELO Rating Queries"],
            test_type=TestCaseType.INDIVIDUAL,
            description="ELO rating above threshold",
            reference_player=reference_player
        ),
        TestCase(
            id="elo_rating_002",
            natural_language=f"Find games where {reference_player} was rated under 1200",
            feature_names=["ELO Rating Queries"],
            test_type=TestCaseType.INDIVIDUAL,
            description="ELO rating below threshold",
            reference_player=reference_player
        ),
    ])
    
    # Time Control/Speed
    test_cases.extend([
        TestCase(
            id="time_control_001",
            natural_language=f"Show {reference_player} blitz games",
            feature_names=["Time Control/Speed"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Blitz time control query",
            reference_player=reference_player
        ),
        TestCase(
            id="time_control_002",
            natural_language=f"How many bullet games did {reference_player} win",
            feature_names=["Time Control/Speed"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Bullet time control with count",
            reference_player=reference_player
        ),
    ])
    
    # Variant
    test_cases.extend([
        TestCase(
            id="variant_001",
            natural_language=f"Show {reference_player} chess960 games",
            feature_names=["Variant"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Chess960 variant query",
            reference_player=reference_player
        ),
        TestCase(
            id="variant_002",
            natural_language=f"How many standard games has {reference_player} won",
            feature_names=["Variant"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Standard variant with count",
            reference_player=reference_player
        ),
    ])
    
    # Sorting
    test_cases.extend([
        TestCase(
            id="sorting_001",
            natural_language="Show games sorted by ELO rating",
            feature_names=["Sorting"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Sort by ELO rating",
            reference_player=reference_player
        ),
        TestCase(
            id="sorting_002",
            natural_language="Find most recent games",
            feature_names=["Sorting"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Sort by date",
            reference_player=reference_player
        ),
    ])
    
    # Counting
    test_cases.extend([
        TestCase(
            id="counting_001",
            natural_language=f"How many games did {reference_player} win",
            feature_names=["Counting"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Count wins",
            reference_player=reference_player
        ),
        TestCase(
            id="counting_002",
            natural_language="Count games where queen was sacrificed",
            feature_names=["Counting"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Count sacrifices",
            reference_player=reference_player
        ),
    ])
    
    # Grouping
    test_cases.extend([
        TestCase(
            id="grouping_001",
            natural_language="Show games by speed category",
            feature_names=["Grouping"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Group by speed",
            reference_player=reference_player
        ),
        TestCase(
            id="grouping_002",
            natural_language="Show games by variant",
            feature_names=["Grouping"],
            test_type=TestCaseType.INDIVIDUAL,
            description="Group by variant",
            reference_player=reference_player
        ),
    ])
    
    return test_cases

