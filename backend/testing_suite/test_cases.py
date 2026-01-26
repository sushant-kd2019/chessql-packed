"""
Test case data structures and base classes.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class TestCaseType(Enum):
    """Type of test case."""
    INDIVIDUAL = "individual"
    COMBINED = "combined"


class TestCaseStatus(Enum):
    """Status of a test case."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class TestCase:
    """Represents a single test case."""
    
    id: str
    natural_language: str
    expected_cql: Optional[str] = None
    feature_names: List[str] = field(default_factory=list)
    test_type: TestCaseType = TestCaseType.INDIVIDUAL
    description: Optional[str] = None
    reference_player: Optional[str] = None
    platform: Optional[str] = None
    account_id: Optional[int] = None
    
    # Runtime fields (not serialized)
    actual_cql: Optional[str] = None
    status: TestCaseStatus = TestCaseStatus.PENDING
    error_message: Optional[str] = None
    comparison_details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "natural_language": self.natural_language,
            "expected_cql": self.expected_cql,
            "feature_names": self.feature_names,
            "test_type": self.test_type.value,
            "description": self.description,
            "reference_player": self.reference_player,
            "platform": self.platform,
            "account_id": self.account_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestCase":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            natural_language=data["natural_language"],
            expected_cql=data.get("expected_cql"),
            feature_names=data.get("feature_names", []),
            test_type=TestCaseType(data.get("test_type", "individual")),
            description=data.get("description"),
            reference_player=data.get("reference_player"),
            platform=data.get("platform"),
            account_id=data.get("account_id"),
        )
    
    def __repr__(self):
        return f"TestCase(id='{self.id}', nl='{self.natural_language[:50]}...', status={self.status.value})"


@dataclass
class TestSuite:
    """Represents a collection of test cases."""
    
    name: str
    description: Optional[str] = None
    test_cases: List[TestCase] = field(default_factory=list)
    
    def add_test_case(self, test_case: TestCase):
        """Add a test case to the suite."""
        self.test_cases.append(test_case)
    
    def get_test_case(self, test_id: str) -> Optional[TestCase]:
        """Get a test case by ID."""
        for tc in self.test_cases:
            if tc.id == test_id:
                return tc
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "test_cases": [tc.to_dict() for tc in self.test_cases]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestSuite":
        """Create from dictionary."""
        suite = cls(
            name=data["name"],
            description=data.get("description")
        )
        for tc_data in data.get("test_cases", []):
            suite.add_test_case(TestCase.from_dict(tc_data))
        return suite
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the test suite."""
        total = len(self.test_cases)
        status_counts = {}
        for status in TestCaseStatus:
            status_counts[status.value] = sum(
                1 for tc in self.test_cases if tc.status == status
            )
        
        return {
            "total": total,
            "by_status": status_counts,
            "pass_rate": (
                status_counts.get("passed", 0) / total * 100
                if total > 0 else 0
            )
        }

