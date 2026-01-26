# NL to CQL Testing Suite

This testing suite validates the accuracy of natural language to CQL (Chess Query Language) conversion. It serves as a regression test when models or infrastructure change.

## Purpose

- **Regression Testing**: Ensure accuracy doesn't degrade when changing models or infrastructure
- **Feature Coverage**: Test all supported features individually and in combination
- **Baseline Truth**: Generate and maintain expected CQL queries using current system
- **Comparison**: Compare CQL queries accounting for ordering and spacing differences

## Structure

```
testing-suite/
├── __init__.py
├── README.md
├── config.py              # Configuration
├── features.py            # Feature catalog
├── test_cases.py          # Test case data structures
├── test_cases_individual.py  # Individual feature test cases
├── test_cases_combined.py    # Combined feature test cases
├── cql_comparator.py      # CQL query comparison utility
├── generate_baseline.py    # Baseline truth generator
├── test_runner.py         # Test execution
├── report_generator.py    # Report generation
├── cli.py                 # Command-line interface
├── baseline/              # Baseline truth files
└── reports/               # Generated test reports
```

## Features Tested

The suite tests 15 categories of features:

1. **Player Results** - won/lost/drew queries
2. **Piece Sacrifices** - queen, rook, bishop, knight, pawn
3. **Piece Exchanges** - piece exchange queries
4. **Captures** - specific piece capture queries
5. **Pawn Promotions** - promotions to different pieces, multiple promotions
6. **Move Timing** - before/after move N conditions
7. **ELO Rating** - rating-based queries
8. **Time Control** - ultraBullet, bullet, blitz, rapid, classical
9. **Variant** - standard, chess960
10. **Platform Filtering** - lichess, chesscom
11. **Account Filtering** - account ID filtering
12. **Sorting** - ORDER BY operations
13. **Counting** - COUNT queries
14. **Grouping** - GROUP BY operations
15. **Combined Queries** - multiple conditions with AND/OR

## Usage

### Generate Baseline Truth

First, generate the baseline truth using the current system:

```bash
cd backend
python -m testing_suite.cli generate-baseline
```

Note: The folder is named `testing_suite` (with underscore) for Python module compatibility.

Or with options:

```bash
python -m testing_suite.cli generate-baseline \
    --reference-player lecorvus \
    --db-path chess_games.db \
    --output baseline_truth.json
```

This will:
- Run all test cases through the current NL→CQL system
- Capture the generated CQL queries
- Save them as baseline truth in `baseline/baseline_truth.json`

### Run Tests

Execute the test suite:

```bash
cd backend
python -m testing_suite.cli run-tests
```

Or with options:

```bash
python -m testing_suite.cli run-tests \
    --baseline baseline_truth.json \
    --output results.json
```

This will:
- Load baseline truth
- Run test cases through current system
- Compare results using CQL comparator
- Generate test report

### View Report

View the latest test report:

```bash
cd backend
python -m testing_suite.cli view-report
```

Or with options:

```bash
python -m testing_suite.cli view-report \
    --format html \
    --results-file reports/test_report_20240101_120000.json
```

### Other Commands

List available baselines:
```bash
python -m testing_suite.cli list-baselines
```

List available reports:
```bash
python -m testing_suite.cli list-reports
```

## Configuration

Configuration is managed in `config.py`. Key settings:

- `reference_player`: Default player name (default: "lecorvus")
- `db_path`: Path to chess games database
- `baseline_dir`: Directory for baseline files
- `reports_dir`: Directory for test reports

## Test Case Format

Test cases are defined with:

- `id`: Unique identifier
- `natural_language`: The natural language query
- `expected_cql`: The expected CQL query (generated from baseline)
- `feature_names`: List of features being tested
- `test_type`: "individual" or "combined"
- `description`: Optional description

## CQL Comparison

The CQL comparator handles:

- Different whitespace
- Different ordering of conditions
- Different ordering of SELECT columns
- Case insensitivity
- Equivalent SQL structures

## Development

When adding new features or test cases:

1. Add feature to `features.py`
2. Add test cases to `test_cases_individual.py` or `test_cases_combined.py`
3. Regenerate baseline: `generate-baseline`
4. Run tests: `run-tests`
5. Review report and fix any issues

