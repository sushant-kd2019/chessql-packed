# NL to CQL Testing Suite - Commit Plan

## Overview
This testing suite will validate natural language to CQL conversion accuracy. It will serve as a regression test when models or infrastructure change.

## Commit Structure

### Commit 1: Create folder structure, base files, feature catalog, and test case structure
**Files to create:**
- `testing-suite/README.md` - Documentation for the testing suite
- `testing-suite/__init__.py` - Python package marker
- `testing-suite/config.py` - Configuration (reference player, database path, etc.)
- `testing-suite/requirements.txt` - Dependencies (if any additional ones needed)
- `testing-suite/features.py` - Complete list of all supported features
- `testing-suite/test_cases.py` - Test case data structure and base classes

**Features to catalog:**
1. Player Results (won/lost/drew)
2. Piece Sacrifices (queen, rook, bishop, knight, pawn)
3. Piece Exchanges
4. Captures (piece1 captured piece2)
5. Pawn Promotions (to queen/rook/bishop/knight, with x N for multiple)
6. Move Timing (before/after move N)
7. ELO Rating Queries
8. Time Control/Speed (ultraBullet, bullet, blitz, rapid, classical)
9. Variant (standard, chess960)
10. Platform Filtering (lichess, chesscom)
11. Account Filtering
12. Sorting (ORDER BY)
13. Counting (COUNT)
14. Grouping (GROUP BY)
15. Combined Queries (multiple conditions with AND/OR)

**Purpose:** Set up the basic structure, configuration, document all features, and create test case structure

---

### Commit 2: Add individual and combined feature test cases
**Files to create:**
- `testing-suite/test_cases_individual.py` - 1-2 test questions per individual feature
- `testing-suite/test_cases_combined.py` - 1-2 questions per combined feature combination

**Individual test cases per feature:**
- Player Results: 2 questions
- Piece Sacrifices: 2 questions (different pieces)
- Piece Exchanges: 2 questions
- Captures: 2 questions
- Pawn Promotions: 2 questions (including multiple promotions)
- Move Timing: 2 questions
- ELO Rating: 2 questions
- Time Control: 2 questions (different speeds)
- Variant: 2 questions
- Sorting: 2 questions
- Counting: 2 questions
- Grouping: 2 questions

**Combined test cases:**
- Player result + Sacrifice (e.g., "games where I sacrificed a queen and won")
- Player result + Exchange
- Player result + Promotion
- Player result + Time Control
- Player result + ELO Rating
- Sacrifice + Time Control
- Sacrifice + Variant
- Promotion + Multiple (x 2, x 3)
- Time Control + Variant
- Player result + Sacrifice + Time Control
- Player result + Promotion + Time Control
- ELO Rating + Time Control
- And more combinations...

**Purpose:** Create baseline test cases for each individual feature and complex queries with multiple conditions

---

### Commit 3: Create CQL query comparison utility
**Files to create:**
- `testing-suite/cql_comparator.py` - Utility to compare two CQL queries accounting for:
  - Different whitespace
  - Different ordering of conditions
  - Different ordering of SELECT columns
  - Case insensitivity
  - Equivalent SQL structures

**Purpose:** Normalize and compare CQL queries to handle variations in output format

---

### Commit 4: Create baseline truth generator
**Files to create:**
- `testing-suite/generate_baseline.py` - Script to:
  - Run all test cases through current NL→CQL system
  - Capture the generated CQL queries
  - Save as baseline truth in JSON format
  - Handle errors gracefully

**Purpose:** Generate the "gold standard" CQL queries using current infrastructure

---

### Commit 5: Create test runner and reporting
**Files to create:**
- `testing-suite/test_runner.py` - Main test execution:
  - Load baseline truth
  - Run test cases through current system
  - Compare results using CQL comparator
  - Generate test report (pass/fail, accuracy metrics)
- `testing-suite/report_generator.py` - Generate human-readable test reports

**Purpose:** Execute tests and generate reports showing accuracy

---

### Commit 6: Add CLI interface and documentation
**Files to create:**
- `testing-suite/cli.py` - Command-line interface for:
  - Running tests
  - Generating baseline
  - Viewing reports
- Update `testing-suite/README.md` with usage instructions

**Purpose:** Make the testing suite easy to use

---

## File Structure
```
backend/testing-suite/
├── __init__.py
├── README.md
├── config.py
├── features.py
├── test_cases.py
├── test_cases_individual.py
├── test_cases_combined.py
├── cql_comparator.py
├── generate_baseline.py
├── test_runner.py
├── report_generator.py
├── cli.py
├── baseline/
│   └── baseline_truth.json
└── reports/
    └── (generated reports)
```

## Usage Flow
1. Generate baseline: `python -m testing-suite.cli generate-baseline`
2. Run tests: `python -m testing-suite.cli run-tests`
3. View report: `python -m testing-suite.cli view-report`

