from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.domain.models import BrokenImport, Candidate


@dataclass
class SearchResult:
    candidates: List[Candidate]
    search_time: float
    metadata: Dict[str, Any]


class SearchStrategy(ABC):
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def cost_level(self) -> int:
        pass
    
    @abstractmethod
    def is_applicable(self, broken_import: BrokenImport) -> bool:
        pass
    
    @abstractmethod
    def search(self, broken_import: BrokenImport, 
               project_root: Path,
               context: Optional[Dict[str, Any]] = None) -> SearchResult:
        pass
    
    def _create_candidate(self, module_path: str, file_path: Path,
                         matched_symbols: List[str] = None) -> Candidate:
        candidate = Candidate(
            module_path=module_path,
            file_path=file_path,
            strategy_source=self.name,
            matched_symbols=matched_symbols or []
        )
        return candidate