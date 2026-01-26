"""
Report Generator

Generates human-readable test reports from test results.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from .config import TestConfig
    from .test_cases import TestCaseStatus
except ImportError:
    from config import TestConfig
    from test_cases import TestCaseStatus


def generate_text_report(results: Dict[str, Any]) -> str:
    """Generate a text report from test results.
    
    Args:
        results: Test results dictionary
    
    Returns:
        Text report string
    """
    lines = []
    lines.append("=" * 80)
    lines.append("NL→CQL Test Suite Report")
    lines.append("=" * 80)
    lines.append("")
    
    # Summary
    summary = results.get("summary", {})
    lines.append("Summary:")
    lines.append(f"  Total tests:  {summary.get('total', 0)}")
    lines.append(f"  Passed:       {summary.get('passed', 0)}")
    lines.append(f"  Failed:       {summary.get('failed', 0)}")
    lines.append(f"  Errors:       {summary.get('errors', 0)}")
    lines.append(f"  Pass rate:    {summary.get('pass_rate', 0):.1f}%")
    lines.append("")
    
    # Test run info
    lines.append("Test Run Information:")
    lines.append(f"  Run at:              {results.get('run_at', 'unknown')}")
    lines.append(f"  Baseline generated:  {results.get('baseline_generated_at', 'unknown')}")
    lines.append(f"  Reference player:    {results.get('reference_player', 'unknown')}")
    lines.append("")
    
    # Failed tests
    failed_tests = [
        tc for tc in results.get("test_cases", [])
        if tc.get("status") == TestCaseStatus.FAILED.value
    ]
    
    if failed_tests:
        lines.append("=" * 80)
        lines.append(f"Failed Tests ({len(failed_tests)}):")
        lines.append("=" * 80)
        lines.append("")
        
        for i, tc in enumerate(failed_tests, 1):
            lines.append(f"{i}. {tc.get('id')}")
            lines.append(f"   Natural Language: {tc.get('natural_language')}")
            lines.append(f"   Expected CQL:     {tc.get('expected_cql', 'N/A')}")
            lines.append(f"   Actual CQL:       {tc.get('actual_cql', 'N/A')}")
            
            comparison = tc.get("comparison_details", {})
            if comparison:
                details = comparison.get("details", {})
                lines.append(f"   Comparison:       {comparison.get('method', 'unknown')}")
                if not comparison.get("equal", False):
                    lines.append(f"   - SELECT equal:   {details.get('select_equal', 'N/A')}")
                    lines.append(f"   - WHERE equal:    {details.get('where_equal', 'N/A')}")
                    lines.append(f"   - ORDER equal:    {details.get('order_equal', 'N/A')}")
                    lines.append(f"   - GROUP equal:    {details.get('group_equal', 'N/A')}")
            
            lines.append("")
    
    # Error tests
    error_tests = [
        tc for tc in results.get("test_cases", [])
        if tc.get("status") == TestCaseStatus.ERROR.value
    ]
    
    if error_tests:
        lines.append("=" * 80)
        lines.append(f"Error Tests ({len(error_tests)}):")
        lines.append("=" * 80)
        lines.append("")
        
        for i, tc in enumerate(error_tests, 1):
            lines.append(f"{i}. {tc.get('id')}")
            lines.append(f"   Natural Language: {tc.get('natural_language')}")
            lines.append(f"   Error:           {tc.get('error_message', 'Unknown error')}")
            lines.append("")
    
    # Passed tests (summary only)
    passed_tests = [
        tc for tc in results.get("test_cases", [])
        if tc.get("status") == TestCaseStatus.PASSED.value
    ]
    
    if passed_tests:
        lines.append("=" * 80)
        lines.append(f"Passed Tests ({len(passed_tests)}):")
        lines.append("=" * 80)
        lines.append("")
        lines.append("All passed tests are listed below:")
        lines.append("")
        
        for tc in passed_tests:
            lines.append(f"  ✓ {tc.get('id')}: {tc.get('natural_language')}")
        
        lines.append("")
    
    lines.append("=" * 80)
    lines.append("End of Report")
    lines.append("=" * 80)
    
    return "\n".join(lines)


def generate_html_report(results: Dict[str, Any]) -> str:
    """Generate an HTML report from test results.
    
    Args:
        results: Test results dictionary
    
    Returns:
        HTML report string
    """
    summary = results.get("summary", {})
    pass_rate = summary.get("pass_rate", 0)
    
    # Determine status color
    if pass_rate == 100:
        status_color = "#28a745"  # Green
        status_text = "All Tests Passed"
    elif pass_rate >= 80:
        status_color = "#ffc107"  # Yellow
        status_text = "Mostly Passing"
    else:
        status_color = "#dc3545"  # Red
        status_text = "Many Failures"
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NL→CQL Test Suite Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid {status_color};
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid {status_color};
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .test-case {{
            margin: 15px 0;
            padding: 15px;
            border-left: 4px solid #ddd;
            background-color: #f8f9fa;
        }}
        .test-case.failed {{
            border-left-color: #dc3545;
            background-color: #fff5f5;
        }}
        .test-case.error {{
            border-left-color: #ffc107;
            background-color: #fffbf0;
        }}
        .test-case.passed {{
            border-left-color: #28a745;
            background-color: #f0fff4;
        }}
        .test-id {{
            font-weight: bold;
            color: #333;
        }}
        .nl-query {{
            color: #666;
            font-style: italic;
            margin: 5px 0;
        }}
        .cql-query {{
            font-family: monospace;
            background-color: #f0f0f0;
            padding: 5px;
            border-radius: 3px;
            margin: 5px 0;
            word-break: break-all;
        }}
        .error-message {{
            color: #dc3545;
            font-weight: bold;
        }}
        .section {{
            margin: 30px 0;
        }}
        .section h2 {{
            color: #333;
            border-bottom: 2px solid #ddd;
            padding-bottom: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>NL→CQL Test Suite Report</h1>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="value">{summary.get('total', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Passed</h3>
                <div class="value" style="color: #28a745;">{summary.get('passed', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Failed</h3>
                <div class="value" style="color: #dc3545;">{summary.get('failed', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Errors</h3>
                <div class="value" style="color: #ffc107;">{summary.get('errors', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Pass Rate</h3>
                <div class="value" style="color: {status_color};">{pass_rate:.1f}%</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Test Information</h2>
            <p><strong>Run at:</strong> {results.get('run_at', 'unknown')}</p>
            <p><strong>Baseline generated:</strong> {results.get('baseline_generated_at', 'unknown')}</p>
            <p><strong>Reference player:</strong> {results.get('reference_player', 'unknown')}</p>
        </div>
"""
    
    # Failed tests
    failed_tests = [
        tc for tc in results.get("test_cases", [])
        if tc.get("status") == TestCaseStatus.FAILED.value
    ]
    
    if failed_tests:
        html += """
        <div class="section">
            <h2>Failed Tests</h2>
"""
        for tc in failed_tests:
            html += f"""
            <div class="test-case failed">
                <div class="test-id">{tc.get('id')}</div>
                <div class="nl-query">{tc.get('natural_language')}</div>
                <div><strong>Expected:</strong></div>
                <div class="cql-query">{tc.get('expected_cql', 'N/A')}</div>
                <div><strong>Actual:</strong></div>
                <div class="cql-query">{tc.get('actual_cql', 'N/A')}</div>
            </div>
"""
        html += """
        </div>
"""
    
    # Error tests
    error_tests = [
        tc for tc in results.get("test_cases", [])
        if tc.get("status") == TestCaseStatus.ERROR.value
    ]
    
    if error_tests:
        html += """
        <div class="section">
            <h2>Error Tests</h2>
"""
        for tc in error_tests:
            html += f"""
            <div class="test-case error">
                <div class="test-id">{tc.get('id')}</div>
                <div class="nl-query">{tc.get('natural_language')}</div>
                <div class="error-message">Error: {tc.get('error_message', 'Unknown error')}</div>
            </div>
"""
        html += """
        </div>
"""
    
    # Passed tests (summary)
    passed_tests = [
        tc for tc in results.get("test_cases", [])
        if tc.get("status") == TestCaseStatus.PASSED.value
    ]
    
    if passed_tests:
        html += f"""
        <div class="section">
            <h2>Passed Tests ({len(passed_tests)})</h2>
            <p>All tests passed successfully.</p>
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    return html


def save_report(report: str, config: TestConfig, filename: str = None, format: str = "txt"):
    """Save report to file.
    
    Args:
        report: Report content
        config: Test configuration
        filename: Output filename (auto-generated if None)
        format: Report format ("txt" or "html")
    """
    if filename is None:
        from datetime import datetime
        ext = "html" if format == "html" else "txt"
        filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    
    report_path = config.reports_dir / filename
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Report saved to: {report_path}")
    return report_path


def load_latest_results(config: TestConfig) -> Optional[Dict[str, Any]]:
    """Load the most recent test results.
    
    Args:
        config: Test configuration
    
    Returns:
        Test results dictionary or None
    """
    results_files = sorted(
        config.reports_dir.glob("test_report_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not results_files:
        return None
    
    with open(results_files[0], 'r') as f:
        return json.load(f)


def main():
    """Main entry point for report generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate test report")
    parser.add_argument(
        "--results-file",
        default=None,
        help="Path to results JSON file (default: latest)"
    )
    parser.add_argument(
        "--format",
        choices=["txt", "html", "both"],
        default="both",
        help="Report format (default: both)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output filename (auto-generated if not provided)"
    )
    
    args = parser.parse_args()
    
    # Create config
    config = TestConfig()
    
    # Load results
    if args.results_file:
        with open(args.results_file, 'r') as f:
            results = json.load(f)
    else:
        results = load_latest_results(config)
        if not results:
            print("No test results found. Please run tests first.")
            return
    
    # Generate reports
    if args.format in ["txt", "both"]:
        text_report = generate_text_report(results)
        save_report(text_report, config, args.output, "txt")
    
    if args.format in ["html", "both"]:
        html_report = generate_html_report(results)
        save_report(html_report, config, args.output, "html")


if __name__ == "__main__":
    main()

