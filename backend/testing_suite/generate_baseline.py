"""
Baseline Truth Generator

Generates baseline CQL queries using the current NL→CQL system.
This serves as the "gold standard" for future comparisons.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from .config import TestConfig
    from .test_cases import TestCase, TestSuite, TestCaseStatus
    from .test_cases_individual import get_individual_test_cases
    from .test_cases_combined import get_combined_test_cases
except ImportError:
    from config import TestConfig
    from test_cases import TestCase, TestSuite, TestCaseStatus
    from test_cases_individual import get_individual_test_cases
    from test_cases_combined import get_combined_test_cases

from natural_language_search import NaturalLanguageSearch


def generate_baseline(config: TestConfig) -> Dict[str, Any]:
    """Generate baseline truth for all test cases.
    
    Args:
        config: Test configuration
    
    Returns:
        Dictionary containing baseline data
    """
    print("Generating baseline truth...")
    print(f"Reference player: {config.reference_player}")
    print(f"Database: {config.db_path}")
    print("-" * 50)
    
    # Initialize natural language search
    try:
        nl_search = NaturalLanguageSearch(
            db_path=config.db_path,
            api_key=config.api_key,
            reference_player=config.reference_player
        )
    except Exception as e:
        print(f"Error initializing natural language search: {e}")
        return {
            "error": str(e),
            "generated_at": datetime.now().isoformat(),
            "test_cases": []
        }
    
    # Get all test cases
    individual_cases = get_individual_test_cases(config.reference_player)
    combined_cases = get_combined_test_cases(config.reference_player)
    all_cases = individual_cases + combined_cases
    
    print(f"Total test cases: {len(all_cases)}")
    print("-" * 50)
    
    # Generate CQL for each test case
    baseline_data = {
        "generated_at": datetime.now().isoformat(),
        "reference_player": config.reference_player,
        "db_path": config.db_path,
        "test_cases": []
    }
    
    success_count = 0
    error_count = 0
    
    for i, test_case in enumerate(all_cases, 1):
        print(f"[{i}/{len(all_cases)}] Processing: {test_case.id}")
        print(f"  NL: {test_case.natural_language}")
        
        try:
            # Convert to CQL (this calls the _convert_to_sql method internally)
            # We need to call it without executing the query
            cql_query = nl_search._convert_to_sql(
                test_case.natural_language,
                reference_player=test_case.reference_player or config.reference_player,
                platform=test_case.platform
            )
            
            if cql_query:
                test_case.expected_cql = cql_query
                test_case.status = TestCaseStatus.PASSED
                success_count += 1
                print(f"  ✓ Generated CQL: {cql_query[:100]}...")
            else:
                test_case.status = TestCaseStatus.ERROR
                test_case.error_message = "Failed to generate CQL query"
                error_count += 1
                print(f"  ✗ Failed to generate CQL")
        
        except Exception as e:
            test_case.status = TestCaseStatus.ERROR
            test_case.error_message = str(e)
            error_count += 1
            print(f"  ✗ Error: {e}")
        
        # Add to baseline data
        baseline_data["test_cases"].append(test_case.to_dict())
        print()
    
    baseline_data["summary"] = {
        "total": len(all_cases),
        "success": success_count,
        "errors": error_count,
        "success_rate": (success_count / len(all_cases) * 100) if all_cases else 0
    }
    
    print("-" * 50)
    print(f"Baseline generation complete!")
    print(f"  Total: {len(all_cases)}")
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  Success rate: {baseline_data['summary']['success_rate']:.1f}%")
    
    return baseline_data


def save_baseline(baseline_data: Dict[str, Any], config: TestConfig, filename: str = "baseline_truth.json"):
    """Save baseline data to file.
    
    Args:
        baseline_data: Baseline data dictionary
        config: Test configuration
        filename: Output filename
    """
    baseline_path = config.get_baseline_path(filename)
    
    with open(baseline_path, 'w') as f:
        json.dump(baseline_data, f, indent=2)
    
    print(f"\nBaseline saved to: {baseline_path}")


def load_baseline(config: TestConfig, filename: str = "baseline_truth.json") -> Optional[Dict[str, Any]]:
    """Load baseline data from file.
    
    Args:
        config: Test configuration
        filename: Baseline filename
    
    Returns:
        Baseline data dictionary or None if file doesn't exist
    """
    baseline_path = config.get_baseline_path(filename)
    
    if not baseline_path.exists():
        return None
    
    with open(baseline_path, 'r') as f:
        return json.load(f)


def main():
    """Main entry point for baseline generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate baseline truth for NL→CQL testing")
    parser.add_argument(
        "--reference-player",
        default="lecorvus",
        help="Reference player name (default: lecorvus)"
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Path to chess games database"
    )
    parser.add_argument(
        "--output",
        default="baseline_truth.json",
        help="Output filename (default: baseline_truth.json)"
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="OpenAI API key (default: from environment)"
    )
    
    args = parser.parse_args()
    
    # Create config
    config = TestConfig(
        reference_player=args.reference_player,
        db_path=args.db_path or TestConfig().db_path,
        api_key=args.api_key
    )
    
    # Generate baseline
    baseline_data = generate_baseline(config)
    
    # Save baseline
    if "error" not in baseline_data:
        save_baseline(baseline_data, config, args.output)
    else:
        print(f"\nError generating baseline: {baseline_data['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

