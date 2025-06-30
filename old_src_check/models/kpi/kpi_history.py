"""KPI history model for tracking scores over time."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class KPIHistory:
    """A historical KPI score record."""
    id: Optional[int] = None
    timestamp: datetime = None
    project_path: str = ""
    total_score: float = 0.0
    code_quality_score: float = 0.0
    architecture_quality_score: float = 0.0
    test_quality_score: float = 0.0
    details: Dict[str, Any] = None
    
    # Metadata
    git_commit: Optional[str] = None
    branch: Optional[str] = None
    execution_time: float = 0.0
    files_analyzed: int = 0
    total_issues: int = 0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.details is None:
            self.details = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "project_path": self.project_path,
            "total_score": self.total_score,
            "code_quality_score": self.code_quality_score,
            "architecture_quality_score": self.architecture_quality_score,
            "test_quality_score": self.test_quality_score,
            "details": self.details,
            "git_commit": self.git_commit,
            "branch": self.branch,
            "execution_time": self.execution_time,
            "files_analyzed": self.files_analyzed,
            "total_issues": self.total_issues
        }
    
    @classmethod
    def from_kpi_score(cls, score: "KPIScore", git_info: Optional[Dict] = None) -> "KPIHistory":
        """Create history record from KPIScore."""
        history = cls(
            timestamp=score.timestamp,
            project_path=score.project_path,
            total_score=score.total_score,
            code_quality_score=score.code_quality.weighted_score,
            architecture_quality_score=score.architecture_quality.weighted_score,
            test_quality_score=score.test_quality.weighted_score,
            details=score.to_dict(),
            execution_time=score.execution_time,
            files_analyzed=score.files_analyzed,
            total_issues=score.total_issues
        )
        
        if git_info:
            history.git_commit = git_info.get("commit")
            history.branch = git_info.get("branch")
        
        return history