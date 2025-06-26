from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

from src.infrastructure.candidate import BrokenImport, Candidate
from src.domain.services import CandidateScorer
from src.core.services.search_coordinator import SearchCoordinator


@dataclass
class SearchImportCandidatesRequest:
    broken_import: BrokenImport
    project_root: Path
    strategies: List[str] = None
    max_candidates: int = 10


@dataclass
class SearchImportCandidatesResponse:
    candidates: List[Candidate]
    search_time: float
    strategies_used: List[str]
    metadata: Dict[str, Any]


class SearchImportCandidatesUseCase:
    
    def __init__(self):
        self._coordinator = SearchCoordinator()
        self._scorer = CandidateScorer()
    
    def execute(self, request: SearchImportCandidatesRequest) -> SearchImportCandidatesResponse:
        start_time = time.time()
        
        coordinated_result = self._coordinator.search(
            broken_import=request.broken_import,
            project_root=request.project_root,
            strategy_names=request.strategies
        )
        
        scored_candidates = self._scorer.score_candidates(
            coordinated_result.all_candidates, request.broken_import
        )
        
        top_candidates = scored_candidates[:request.max_candidates]
        
        search_time = time.time() - start_time
        
        return SearchImportCandidatesResponse(
            candidates=top_candidates,
            search_time=search_time,
            strategies_used=coordinated_result.metadata.get('strategies_used', []),
            metadata={
                'total_candidates_found': len(coordinated_result.all_candidates),
                'coordinator_metadata': coordinated_result.metadata,
                'strategy_results': {
                    name: {
                        'candidates_found': len(result.candidates),
                        'search_time': result.search_time,
                        'metadata': result.metadata
                    }
                    for name, result in coordinated_result.strategy_results.items()
                }
            }
        )
