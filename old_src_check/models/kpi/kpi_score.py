"""KPI score models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class KPICategory(str, Enum):
    """KPI categories based on the four main quality areas."""
    CODE_QUALITY = "code_quality"
    ARCHITECTURE_QUALITY = "architecture_quality"
    TEST_QUALITY = "test_quality"
    SECURITY_QUALITY = "security_quality"


class Severity(str, Enum):
    """Severity levels for issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ScorableItem:
    """An item that can be scored in the KPI system."""
    category: KPICategory
    severity: Severity
    impact_points: float
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    rule_id: Optional[str] = None
    
    def get_score_impact(self) -> float:
        """Calculate the score impact based on severity."""
        severity_multipliers = {
            Severity.CRITICAL: 2.0,
            Severity.HIGH: 1.5,
            Severity.MEDIUM: 1.0,
            Severity.LOW: 0.5,
            Severity.INFO: 0.1
        }
        return self.impact_points * severity_multipliers.get(self.severity, 1.0)


@dataclass
class CategoryScore:
    """Score for a specific category."""
    category: KPICategory
    raw_score: float
    weighted_score: float
    issues_count: int
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    details: List[ScorableItem] = field(default_factory=list)
    
    def add_issue(self, item: ScorableItem):
        """Add an issue to this category."""
        self.details.append(item)
        self.issues_count += 1
        
        # Update severity counts
        if item.severity == Severity.CRITICAL:
            self.critical_issues += 1
        elif item.severity == Severity.HIGH:
            self.high_issues += 1
        elif item.severity == Severity.MEDIUM:
            self.medium_issues += 1
        elif item.severity == Severity.LOW:
            self.low_issues += 1


@dataclass
class KPIScore:
    """Overall KPI score with category breakdowns."""
    total_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    project_path: str = ""
    
    # Category scores
    code_quality: CategoryScore = field(default_factory=lambda: CategoryScore(
        category=KPICategory.CODE_QUALITY,
        raw_score=50.0,
        weighted_score=12.5,
        issues_count=0
    ))
    architecture_quality: CategoryScore = field(default_factory=lambda: CategoryScore(
        category=KPICategory.ARCHITECTURE_QUALITY,
        raw_score=50.0,
        weighted_score=12.5,
        issues_count=0
    ))
    test_quality: CategoryScore = field(default_factory=lambda: CategoryScore(
        category=KPICategory.TEST_QUALITY,
        raw_score=50.0,
        weighted_score=12.5,
        issues_count=0
    ))
    security_quality: CategoryScore = field(default_factory=lambda: CategoryScore(
        category=KPICategory.SECURITY_QUALITY,
        raw_score=50.0,
        weighted_score=12.5,
        issues_count=0
    ))
    
    # Metadata
    execution_time: float = 0.0
    files_analyzed: int = 0
    total_issues: int = 0
    
    def get_category_scores(self) -> Dict[KPICategory, CategoryScore]:
        """Get all category scores as a dictionary."""
        return {
            KPICategory.CODE_QUALITY: self.code_quality,
            KPICategory.ARCHITECTURE_QUALITY: self.architecture_quality,
            KPICategory.TEST_QUALITY: self.test_quality,
            KPICategory.SECURITY_QUALITY: self.security_quality
        }
    
    def update_total_score(self):
        """Recalculate total score based on category scores."""
        self.total_score = (
            self.code_quality.weighted_score +
            self.architecture_quality.weighted_score +
            self.test_quality.weighted_score +
            self.security_quality.weighted_score
        )
        self.total_issues = (
            self.code_quality.issues_count +
            self.architecture_quality.issues_count +
            self.test_quality.issues_count +
            self.security_quality.issues_count
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "total_score": self.total_score,
            "timestamp": self.timestamp.isoformat(),
            "project_path": self.project_path,
            "categories": {
                "code_quality": {
                    "score": self.code_quality.weighted_score,
                    "issues": self.code_quality.issues_count,
                    "critical": self.code_quality.critical_issues,
                    "high": self.code_quality.high_issues,
                    "medium": self.code_quality.medium_issues,
                    "low": self.code_quality.low_issues
                },
                "architecture_quality": {
                    "score": self.architecture_quality.weighted_score,
                    "issues": self.architecture_quality.issues_count,
                    "critical": self.architecture_quality.critical_issues,
                    "high": self.architecture_quality.high_issues,
                    "medium": self.architecture_quality.medium_issues,
                    "low": self.architecture_quality.low_issues
                },
                "test_quality": {
                    "score": self.test_quality.weighted_score,
                    "issues": self.test_quality.issues_count,
                    "critical": self.test_quality.critical_issues,
                    "high": self.test_quality.high_issues,
                    "medium": self.test_quality.medium_issues,
                    "low": self.test_quality.low_issues
                },
                "security_quality": {
                    "score": self.security_quality.weighted_score,
                    "issues": self.security_quality.issues_count,
                    "critical": self.security_quality.critical_issues,
                    "high": self.security_quality.high_issues,
                    "medium": self.security_quality.medium_issues,
                    "low": self.security_quality.low_issues
                }
            },
            "metadata": {
                "execution_time": self.execution_time,
                "files_analyzed": self.files_analyzed,
                "total_issues": self.total_issues
            }
        }