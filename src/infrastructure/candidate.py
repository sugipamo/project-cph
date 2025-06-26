from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime


@dataclass
class CandidateScore:
    symbol_match: float = 0.0
    path_similarity: float = 0.0
    directory_pattern: float = 0.0
    git_history: float = 0.0
    dependencies: float = 0.0
    total: float = 0.0
    
    def calculate_total(self, weights: Dict[str, float]) -> float:
        self.total = (
            self.symbol_match * weights.get('symbol_match', 1.0) +
            self.path_similarity * weights.get('path_similarity', 0.8) +
            self.directory_pattern * weights.get('directory_pattern', 0.6) +
            self.git_history * weights.get('git_history', 0.5) +
            self.dependencies * weights.get('dependencies', 0.7)
        )
        return self.total


@dataclass
class Candidate:
    module_path: str
    file_path: Path
    score: CandidateScore = field(default_factory=CandidateScore)
    strategy_source: str = ""
    matched_symbols: List[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.now)
    
    @property
    def import_statement(self) -> str:
        return self.module_path
    
    def __lt__(self, other: 'Candidate') -> bool:
        return self.score.total > other.score.total
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Candidate):
            return NotImplemented
        return self.module_path == other.module_path and self.file_path == other.file_path
    
    def __hash__(self) -> int:
        return hash((self.module_path, str(self.file_path)))