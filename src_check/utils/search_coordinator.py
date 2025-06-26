from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
import logging

from src.domain.models import BrokenImport, Candidate
from src.domain.services.search_strategy import SearchStrategy, SearchResult
from src.domain.services.symbol_based_strategy import SymbolBasedStrategy
from src.domain.services.path_based_strategy import PathBasedStrategy
from src.domain.services.directory_pattern_strategy import DirectoryPatternStrategy


logger = logging.getLogger(__name__)


@dataclass
class CoordinatedSearchResult:
    all_candidates: List[Candidate]
    strategy_results: Dict[str, SearchResult]
    total_search_time: float
    metadata: Dict[str, Any]


class SearchCoordinator:
    
    def __init__(self, strategies: Optional[List[SearchStrategy]] = None):
        if strategies is None:
            strategies = [
                SymbolBasedStrategy(),
                PathBasedStrategy(),
                DirectoryPatternStrategy()
            ]
        self.strategies = sorted(strategies, key=lambda s: s.cost_level)
        self._max_workers = 3
        self._enable_parallel = True
    
    def search(self, broken_import: BrokenImport, 
              project_root: Path,
              context: Optional[Dict[str, Any]] = None,
              strategy_names: Optional[List[str]] = None) -> CoordinatedSearchResult:
        
        start_time = time.time()
        applicable_strategies = self._get_applicable_strategies(broken_import, strategy_names)
        
        if not applicable_strategies:
            return CoordinatedSearchResult(
                all_candidates=[],
                strategy_results={},
                total_search_time=time.time() - start_time,
                metadata={"no_applicable_strategies": True}
            )
        
        strategy_results = {}
        
        if self._enable_parallel and len(applicable_strategies) > 1:
            strategy_results = self._parallel_search(applicable_strategies, broken_import, project_root, context)
        else:
            strategy_results = self._sequential_search(applicable_strategies, broken_import, project_root, context)
        
        all_candidates = self._merge_candidates(strategy_results)
        
        total_time = time.time() - start_time
        
        return CoordinatedSearchResult(
            all_candidates=all_candidates,
            strategy_results=strategy_results,
            total_search_time=total_time,
            metadata={
                "strategies_used": [s.name for s in applicable_strategies],
                "parallel_execution": self._enable_parallel and len(applicable_strategies) > 1
            }
        )
    
    def _get_applicable_strategies(self, broken_import: BrokenImport, 
                                  strategy_names: Optional[List[str]] = None) -> List[SearchStrategy]:
        applicable = []
        
        for strategy in self.strategies:
            if strategy_names and strategy.name not in strategy_names:
                continue
            
            if strategy.is_applicable(broken_import):
                applicable.append(strategy)
        
        return applicable
    
    def _parallel_search(self, strategies: List[SearchStrategy], 
                        broken_import: BrokenImport,
                        project_root: Path,
                        context: Optional[Dict[str, Any]]) -> Dict[str, SearchResult]:
        results = {}
        
        with ThreadPoolExecutor(max_workers=min(self._max_workers, len(strategies))) as executor:
            future_to_strategy = {
                executor.submit(self._execute_strategy, strategy, broken_import, project_root, context): strategy
                for strategy in strategies
            }
            
            for future in as_completed(future_to_strategy):
                strategy = future_to_strategy[future]
                try:
                    result = future.result()
                    results[strategy.name] = result
                    logger.info(f"Strategy {strategy.name} found {len(result.candidates)} candidates")
                except Exception as e:
                    logger.error(f"Strategy {strategy.name} failed: {e}")
                    results[strategy.name] = SearchResult(candidates=[], search_time=0, metadata={"error": str(e)})
        
        return results
    
    def _sequential_search(self, strategies: List[SearchStrategy], 
                          broken_import: BrokenImport,
                          project_root: Path,
                          context: Optional[Dict[str, Any]]) -> Dict[str, SearchResult]:
        results = {}
        
        for strategy in strategies:
            try:
                result = self._execute_strategy(strategy, broken_import, project_root, context)
                results[strategy.name] = result
                logger.info(f"Strategy {strategy.name} found {len(result.candidates)} candidates")
            except Exception as e:
                logger.error(f"Strategy {strategy.name} failed: {e}")
                results[strategy.name] = SearchResult(candidates=[], search_time=0, metadata={"error": str(e)})
        
        return results
    
    def _execute_strategy(self, strategy: SearchStrategy, 
                         broken_import: BrokenImport,
                         project_root: Path,
                         context: Optional[Dict[str, Any]]) -> SearchResult:
        return strategy.search(broken_import, project_root, context)
    
    def _merge_candidates(self, strategy_results: Dict[str, SearchResult]) -> List[Candidate]:
        seen_modules = set()
        unique_candidates = []
        
        all_candidates = []
        for strategy_name, result in strategy_results.items():
            for candidate in result.candidates:
                candidate.strategy_source = strategy_name
                all_candidates.append(candidate)
        
        all_candidates.sort(key=lambda c: c.raw_score if c.raw_score is not None else 0, reverse=True)
        
        for candidate in all_candidates:
            module_key = (candidate.module_path, tuple(sorted(candidate.matched_symbols)))
            if module_key not in seen_modules:
                seen_modules.add(module_key)
                unique_candidates.append(candidate)
        
        return unique_candidates[:20]