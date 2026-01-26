"""
Combined feature test cases.

These test cases combine multiple features to validate complex queries.
"""

try:
    from .test_cases import TestCase, TestCaseType
except ImportError:
    from test_cases import TestCase, TestCaseType


def get_combined_test_cases(reference_player: str = "lecorvus") -> list[TestCase]:
    """Get all combined feature test cases.
    
    Args:
        reference_player: The reference player name for queries
    
    Returns:
        List of test cases for combined features
    """
    test_cases = []
    
    # Player result + Sacrifice
    test_cases.extend([
        TestCase(
            id="combined_001",
            natural_language=f"Games where {reference_player} sacrificed a queen and won",
            feature_names=["Player Results (won/lost/drew)", "Piece Sacrifices"],
            test_type=TestCaseType.COMBINED,
            description="Win with queen sacrifice",
            reference_player=reference_player
        ),
        TestCase(
            id="combined_002",
            natural_language=f"Show games where {reference_player} lost after sacrificing a knight",
            feature_names=["Player Results (won/lost/drew)", "Piece Sacrifices"],
            test_type=TestCaseType.COMBINED,
            description="Loss with knight sacrifice",
            reference_player=reference_player
        ),
    ])
    
    # Player result + Exchange
    test_cases.extend([
        TestCase(
            id="combined_003",
            natural_language=f"Find games where {reference_player} won and pawn was exchanged",
            feature_names=["Player Results (won/lost/drew)", "Piece Exchanges"],
            test_type=TestCaseType.COMBINED,
            description="Win with pawn exchange",
            reference_player=reference_player
        ),
        TestCase(
            id="combined_004",
            natural_language=f"Games where {reference_player} drew with queen exchanges",
            feature_names=["Player Results (won/lost/drew)", "Piece Exchanges"],
            test_type=TestCaseType.COMBINED,
            description="Draw with queen exchange",
            reference_player=reference_player
        ),
    ])
    
    # Player result + Promotion
    test_cases.extend([
        TestCase(
            id="combined_005",
            natural_language=f"Find games where {reference_player} promoted pawn to queen and won",
            feature_names=["Player Results (won/lost/drew)", "Pawn Promotions"],
            test_type=TestCaseType.COMBINED,
            description="Win with pawn promotion",
            reference_player=reference_player
        ),
        TestCase(
            id="combined_006",
            natural_language=f"Show games where {reference_player} won and promoted to queen twice",
            feature_names=["Player Results (won/lost/drew)", "Pawn Promotions"],
            test_type=TestCaseType.COMBINED,
            description="Win with multiple promotions",
            reference_player=reference_player
        ),
    ])
    
    # Player result + Time Control
    test_cases.extend([
        TestCase(
            id="combined_007",
            natural_language=f"How many bullet games did {reference_player} win",
            feature_names=["Player Results (won/lost/drew)", "Time Control/Speed", "Counting"],
            test_type=TestCaseType.COMBINED,
            description="Count wins in bullet",
            reference_player=reference_player
        ),
        TestCase(
            id="combined_008",
            natural_language=f"Find {reference_player} rapid losses",
            feature_names=["Player Results (won/lost/drew)", "Time Control/Speed"],
            test_type=TestCaseType.COMBINED,
            description="Losses in rapid",
            reference_player=reference_player
        ),
    ])
    
    # Player result + ELO Rating
    test_cases.extend([
        TestCase(
            id="combined_009",
            natural_language=f"Games where {reference_player} was rated over 1500 and won",
            feature_names=["Player Results (won/lost/drew)", "ELO Rating Queries"],
            test_type=TestCaseType.COMBINED,
            description="Win with high rating",
            reference_player=reference_player
        ),
        TestCase(
            id="combined_010",
            natural_language=f"Count games where {reference_player} lost when rated over 1500",
            feature_names=["Player Results (won/lost/drew)", "ELO Rating Queries", "Counting"],
            test_type=TestCaseType.COMBINED,
            description="Count losses with high rating",
            reference_player=reference_player
        ),
    ])
    
    # Sacrifice + Time Control
    test_cases.extend([
        TestCase(
            id="combined_011",
            natural_language=f"{reference_player} classical games where queen was sacrificed",
            feature_names=["Piece Sacrifices", "Time Control/Speed"],
            test_type=TestCaseType.COMBINED,
            description="Queen sacrifice in classical",
            reference_player=reference_player
        ),
        TestCase(
            id="combined_012",
            natural_language=f"Show blitz games where {reference_player} sacrificed a knight",
            feature_names=["Piece Sacrifices", "Time Control/Speed"],
            test_type=TestCaseType.COMBINED,
            description="Knight sacrifice in blitz",
            reference_player=reference_player
        ),
    ])
    
    # Sacrifice + Variant
    test_cases.extend([
        TestCase(
            id="combined_013",
            natural_language=f"Show chess960 games where queen was sacrificed",
            feature_names=["Piece Sacrifices", "Variant"],
            test_type=TestCaseType.COMBINED,
            description="Queen sacrifice in chess960",
            reference_player=reference_player
        ),
        TestCase(
            id="combined_014",
            natural_language=f"Standard games where {reference_player} sacrificed a rook",
            feature_names=["Piece Sacrifices", "Variant"],
            test_type=TestCaseType.COMBINED,
            description="Rook sacrifice in standard",
            reference_player=reference_player
        ),
    ])
    
    # Promotion + Multiple
    test_cases.extend([
        TestCase(
            id="combined_015",
            natural_language="Find games where pawn was promoted to queen x 2",
            feature_names=["Pawn Promotions"],
            test_type=TestCaseType.COMBINED,
            description="Multiple queen promotions",
            reference_player=reference_player
        ),
        TestCase(
            id="combined_016",
            natural_language="Show games with pawn promoted to knight x 2",
            feature_names=["Pawn Promotions"],
            test_type=TestCaseType.COMBINED,
            description="Multiple knight promotions",
            reference_player=reference_player
        ),
    ])
    
    # Time Control + Variant
    test_cases.extend([
        TestCase(
            id="combined_017",
            natural_language=f"Standard blitz games {reference_player} won",
            feature_names=["Player Results (won/lost/drew)", "Time Control/Speed", "Variant"],
            test_type=TestCaseType.COMBINED,
            description="Win in standard blitz",
            reference_player=reference_player
        ),
        TestCase(
            id="combined_018",
            natural_language="Show chess960 rapid games",
            feature_names=["Time Control/Speed", "Variant"],
            test_type=TestCaseType.COMBINED,
            description="Chess960 rapid games",
            reference_player=reference_player
        ),
    ])
    
    # Player result + Sacrifice + Time Control
    test_cases.extend([
        TestCase(
            id="combined_019",
            natural_language=f"My classical games where I sacrificed a queen and won",
            feature_names=["Player Results (won/lost/drew)", "Piece Sacrifices", "Time Control/Speed"],
            test_type=TestCaseType.COMBINED,
            description="Win with queen sacrifice in classical",
            reference_player=reference_player
        ),
        TestCase(
            id="combined_020",
            natural_language=f"Show blitz games where {reference_player} lost after sacrificing a bishop",
            feature_names=["Player Results (won/lost/drew)", "Piece Sacrifices", "Time Control/Speed"],
            test_type=TestCaseType.COMBINED,
            description="Loss with bishop sacrifice in blitz",
            reference_player=reference_player
        ),
    ])
    
    # Player result + Promotion + Time Control
    test_cases.extend([
        TestCase(
            id="combined_021",
            natural_language=f"My blitz games where I promoted to queen and won",
            feature_names=["Player Results (won/lost/drew)", "Pawn Promotions", "Time Control/Speed"],
            test_type=TestCaseType.COMBINED,
            description="Win with promotion in blitz",
            reference_player=reference_player
        ),
        TestCase(
            id="combined_022",
            natural_language=f"Rapid games where {reference_player} won and promoted to queen twice",
            feature_names=["Player Results (won/lost/drew)", "Pawn Promotions", "Time Control/Speed"],
            test_type=TestCaseType.COMBINED,
            description="Win with multiple promotions in rapid",
            reference_player=reference_player
        ),
    ])
    
    # ELO Rating + Time Control
    test_cases.extend([
        TestCase(
            id="combined_023",
            natural_language=f"Blitz games where {reference_player} was rated over 1500",
            feature_names=["ELO Rating Queries", "Time Control/Speed"],
            test_type=TestCaseType.COMBINED,
            description="High rating in blitz",
            reference_player=reference_player
        ),
        TestCase(
            id="combined_024",
            natural_language=f"Count bullet games where {reference_player} was rated under 1200",
            feature_names=["ELO Rating Queries", "Time Control/Speed", "Counting"],
            test_type=TestCaseType.COMBINED,
            description="Count low rating bullet games",
            reference_player=reference_player
        ),
    ])
    
    # Player result + Sacrifice + ELO Rating
    test_cases.extend([
        TestCase(
            id="combined_025",
            natural_language=f"Games where {reference_player} sacrificed queen and won when rated over 1500",
            feature_names=["Player Results (won/lost/drew)", "Piece Sacrifices", "ELO Rating Queries"],
            test_type=TestCaseType.COMBINED,
            description="Win with queen sacrifice at high rating",
            reference_player=reference_player
        ),
        TestCase(
            id="combined_026",
            natural_language=f"Count games where {reference_player} sacrificed knight and lost when rated over 1500",
            feature_names=["Player Results (won/lost/drew)", "Piece Sacrifices", "ELO Rating Queries", "Counting"],
            test_type=TestCaseType.COMBINED,
            description="Count losses with knight sacrifice at high rating",
            reference_player=reference_player
        ),
    ])
    
    # Player result + Promotion + Variant
    test_cases.extend([
        TestCase(
            id="combined_027",
            natural_language=f"Chess960 games where {reference_player} won and promoted to queen",
            feature_names=["Player Results (won/lost/drew)", "Pawn Promotions", "Variant"],
            test_type=TestCaseType.COMBINED,
            description="Win with promotion in chess960",
            reference_player=reference_player
        ),
        TestCase(
            id="combined_028",
            natural_language=f"Standard games where {reference_player} promoted to knight and won",
            feature_names=["Player Results (won/lost/drew)", "Pawn Promotions", "Variant"],
            test_type=TestCaseType.COMBINED,
            description="Win with knight promotion in standard",
            reference_player=reference_player
        ),
    ])
    
    return test_cases

