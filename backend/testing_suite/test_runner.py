"""
Test Runner

Executes test cases and compares results with baseline truth.
"""

import json
import sys
import time
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
    from .cql_comparator import CQLComparator
    from .generate_baseline import load_baseline
except ImportError:
    from config import TestConfig
    from test_cases import TestCase, TestSuite, TestCaseStatus
    from test_cases_individual import get_individual_test_cases
    from test_cases_combined import get_combined_test_cases
    from cql_comparator import CQLComparator
    from generate_baseline import load_baseline

from natural_language_search import NaturalLanguageSearch


class TestRunner:
    """Runs test cases and compares with baseline."""
    
    def __init__(self, config: TestConfig):
        """Initialize test runner.
        
        Args:
            config: Test configuration
        """
        self.config = config
        self.comparator = CQLComparator()
        
        # Initialize natural language search
        try:
            self.nl_search = NaturalLanguageSearch(
                db_path=config.db_path,
                api_key=config.api_key,
                reference_player=config.reference_player
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize natural language search: {e}")
    
    def run_tests(self, baseline_filename: str = "baseline_truth.json") -> Dict[str, Any]:
        """Run all test cases and compare with baseline.
        
        Args:
            baseline_filename: Name of baseline file
        
        Returns:
            Test results dictionary
        """
        print("Running test suite...")
        print(f"Reference player: {self.config.reference_player}")
        print(f"Database: {self.config.db_path}")
        print("-" * 50)
        
        # Load baseline
        baseline_data = load_baseline(self.config, baseline_filename)
        if not baseline_data:
            raise FileNotFoundError(
                f"Baseline file not found: {self.config.get_baseline_path(baseline_filename)}\n"
                "Please run 'generate-baseline' first."
            )
        
        print(f"Loaded baseline from: {baseline_data.get('generated_at', 'unknown')}")
        print("-" * 50)
        
        # Create baseline lookup
        baseline_lookup = {
            tc["id"]: tc for tc in baseline_data.get("test_cases", [])
        }
        
        # Get all test cases
        individual_cases = get_individual_test_cases(self.config.reference_player)
        combined_cases = get_combined_test_cases(self.config.reference_player)
        all_cases = individual_cases + combined_cases
        
        print(f"Total test cases: {len(all_cases)}")
        print("-" * 50)
        
        # Run tests
        results = {
            "run_at": datetime.now().isoformat(),
            "baseline_generated_at": baseline_data.get("generated_at"),
            "reference_player": self.config.reference_player,
            "test_cases": []
        }
        
        passed = 0
        failed = 0
        errors = 0
        
        for i, test_case in enumerate(all_cases, 1):
            print(f"[{i}/{len(all_cases)}] Testing: {test_case.id}")
            print(f"  NL: {test_case.natural_language}")
            
            # Get expected CQL from baseline
            baseline_tc = baseline_lookup.get(test_case.id)
            if not baseline_tc:
                test_case.status = TestCaseStatus.ERROR
                test_case.error_message = "Test case not found in baseline"
                errors += 1
                print(f"  ✗ Not found in baseline")
                results["test_cases"].append(test_case.to_dict())
                continue
            
            expected_cql = baseline_tc.get("expected_cql")
            if not expected_cql:
                test_case.status = TestCaseStatus.ERROR
                test_case.error_message = "No expected CQL in baseline"
                errors += 1
                print(f"  ✗ No expected CQL in baseline")
                results["test_cases"].append(test_case.to_dict())
                continue
            
            test_case.expected_cql = expected_cql
            baseline_latency_ms = baseline_tc.get("latency_ms")
            
            # Generate actual CQL with latency measurement
            try:
                start_time = time.time()
                actual_cql = self.nl_search._convert_to_sql(
                    test_case.natural_language,
                    reference_player=test_case.reference_player or self.config.reference_player,
                    platform=test_case.platform
                )
                end_time = time.time()
                test_case.latency_ms = (end_time - start_time) * 1000  # Convert to milliseconds
                
                if not actual_cql:
                    test_case.status = TestCaseStatus.ERROR
                    test_case.error_message = "Failed to generate CQL query"
                    errors += 1
                    print(f"  ✗ Failed to generate CQL")
                    results["test_cases"].append(test_case.to_dict())
                    continue
                
                test_case.actual_cql = actual_cql
                
                # Compare
                comparison = self.comparator.compare(expected_cql, actual_cql)
                test_case.comparison_details = comparison
                
                # Add latency comparison if baseline latency exists
                latency_info = f"{test_case.latency_ms:.1f}ms"
                if baseline_latency_ms is not None:
                    latency_diff = test_case.latency_ms - baseline_latency_ms
                    latency_pct = (latency_diff / baseline_latency_ms * 100) if baseline_latency_ms > 0 else 0
                    if latency_diff > 0:
                        latency_info += f" (+{latency_diff:.1f}ms, +{latency_pct:.1f}%)"
                    else:
                        latency_info += f" ({latency_diff:.1f}ms, {latency_pct:.1f}%)"
                    latency_info += f" [baseline: {baseline_latency_ms:.1f}ms]"
                
                if comparison["equal"]:
                    test_case.status = TestCaseStatus.PASSED
                    passed += 1
                    print(f"  ✓ PASSED ({latency_info})")
                else:
                    test_case.status = TestCaseStatus.FAILED
                    failed += 1
                    print(f"  ✗ FAILED ({latency_info})")
                    print(f"    Expected: {expected_cql[:80]}...")
                    print(f"    Actual:   {actual_cql[:80]}...")
            
            except Exception as e:
                test_case.status = TestCaseStatus.ERROR
                test_case.error_message = str(e)
                errors += 1
                print(f"  ✗ ERROR: {e}")
            
            results["test_cases"].append(test_case.to_dict())
            print()
        
        # Summary with latency statistics
        total = len(all_cases)
        latencies = [tc.latency_ms for tc in all_cases if tc.latency_ms is not None]
        
        latency_stats = {}
        if latencies:
            latency_stats = {
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "avg_ms": sum(latencies) / len(latencies),
                "median_ms": sorted(latencies)[len(latencies) // 2] if latencies else None,
                "total_ms": sum(latencies),
                "count": len(latencies)
            }
        
        results["summary"] = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "latency": latency_stats
        }
        
        print("-" * 50)
        print("Test Results:")
        print(f"  Total:  {total}")
        print(f"  Passed: {passed} ({results['summary']['pass_rate']:.1f}%)")
        print(f"  Failed: {failed}")
        print(f"  Errors: {errors}")
        if latency_stats:
            print(f"\nLatency Statistics:")
            print(f"  Min:    {latency_stats['min_ms']:.1f}ms")
            print(f"  Max:    {latency_stats['max_ms']:.1f}ms")
            print(f"  Avg:    {latency_stats['avg_ms']:.1f}ms")
            print(f"  Median: {latency_stats['median_ms']:.1f}ms")
            print(f"  Total:  {latency_stats['total_ms']:.1f}ms")
        print("-" * 50)
        
        return results


def save_results(results: Dict[str, Any], config: TestConfig, filename: str = None):
    """Save test results to file.
    
    Args:
        results: Test results dictionary
        config: Test configuration
        filename: Output filename (auto-generated if None)
    """
    results_path = config.get_report_path(filename)
    
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_path}")
    return results_path


def main():
    """Main entry point for test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run NL→CQL test suite")
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
        "--baseline",
        default="baseline_truth.json",
        help="Baseline filename (default: baseline_truth.json)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output filename (auto-generated if not provided)"
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
    
    # Run tests
    try:
        runner = TestRunner(config)
        results = runner.run_tests(args.baseline)
        
        # Save results
        results_path = save_results(results, config, args.output)
        
        # Exit with appropriate code
        if results["summary"]["failed"] > 0 or results["summary"]["errors"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    
    except Exception as e:
        print(f"\nError running tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

