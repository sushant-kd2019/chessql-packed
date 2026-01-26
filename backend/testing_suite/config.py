"""
Configuration for the testing suite.
"""

import os
from pathlib import Path
from typing import Optional

# Default configuration values
DEFAULT_REFERENCE_PLAYER = "lecorvus"
DEFAULT_DB_PATH = os.getenv("CHESSQL_DB_PATH", "chess_games.db")
DEFAULT_BASELINE_DIR = Path(__file__).parent / "baseline"
DEFAULT_REPORTS_DIR = Path(__file__).parent / "reports"

# Ensure directories exist
DEFAULT_BASELINE_DIR.mkdir(exist_ok=True)
DEFAULT_REPORTS_DIR.mkdir(exist_ok=True)


class TestConfig:
    """Configuration for test execution."""
    
    def __init__(
        self,
        reference_player: str = DEFAULT_REFERENCE_PLAYER,
        db_path: str = DEFAULT_DB_PATH,
        baseline_dir: Optional[Path] = None,
        reports_dir: Optional[Path] = None,
        api_key: Optional[str] = None
    ):
        """Initialize test configuration.
        
        Args:
            reference_player: The reference player name for queries
            db_path: Path to the chess games database
            baseline_dir: Directory for baseline truth files
            reports_dir: Directory for test reports
            api_key: OpenAI API key for natural language search
        """
        self.reference_player = reference_player
        self.db_path = db_path
        self.baseline_dir = baseline_dir or DEFAULT_BASELINE_DIR
        self.reports_dir = reports_dir or DEFAULT_REPORTS_DIR
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # Ensure directories exist
        self.baseline_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
    
    def get_baseline_path(self, filename: str = "baseline_truth.json") -> Path:
        """Get path to baseline truth file."""
        return self.baseline_dir / filename
    
    def get_report_path(self, filename: str = None) -> Path:
        """Get path to report file."""
        if filename is None:
            from datetime import datetime
            filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        return self.reports_dir / filename

