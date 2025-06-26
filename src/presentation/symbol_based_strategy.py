import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.domain.models import BrokenImport, Candidate, ModuleInfo
from src.domain.services.search_strategy import SearchStrategy, SearchResult
from src.infrastructure.ast_parser import ModuleParser


class SymbolBasedStrategy(SearchStrategy):
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._module_cache: Dict[Path, Optional[ModuleInfo]] = {}
    
    @property
    def name(self) -> str:
        return "symbol_based"
    
    @property
    def cost_level(self) -> int:
        return 1
    
    def is_applicable(self, broken_import: BrokenImport) -> bool:
        return bool(broken_import.imported_names) and broken_import.imported_names[0] != '*'
    
    def search(self, broken_import: BrokenImport,
               project_root: Path,
               context: Optional[Dict[str, Any]] = None) -> SearchResult:
        start_time = time.time()
        
        target_symbols = set(broken_import.imported_names)
        py_files = list(project_root.rglob("*.py"))
        
        py_files = [f for f in py_files if not self._should_skip_file(f)]
        
        candidates = self._parallel_symbol_search(
            py_files, target_symbols, project_root
        )
        
        candidates = self._rank_candidates_by_symbol_match(
            candidates, target_symbols
        )
        
        search_time = time.time() - start_time
        
        return SearchResult(
            candidates=candidates[:10],
            search_time=search_time,
            metadata={
                'files_searched': len(py_files),
                'target_symbols': list(target_symbols),
                'candidates_found': len(candidates)
            }
        )
    
    def _parallel_symbol_search(self, files: List[Path], 
                               target_symbols: Set[str],
                               project_root: Path) -> List[Candidate]:
        candidates = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(
                    self._search_file_for_symbols,
                    file_path,
                    target_symbols,
                    project_root
                ): file_path
                for file_path in files
            }
            
            for future in as_completed(future_to_file):
                try:
                    result = future.result(timeout=5.0)
                    if result:
                        candidates.extend(result)
                except Exception:
                    continue
        
        seen = set()
        unique_candidates = []
        for candidate in candidates:
            key = (candidate.module_path, str(candidate.file_path))
            if key not in seen:
                seen.add(key)
                unique_candidates.append(candidate)
        
        return unique_candidates
    
    def _search_file_for_symbols(self, file_path: Path,
                                target_symbols: Set[str],
                                project_root: Path) -> List[Candidate]:
        module_info = self._get_module_info(file_path, project_root)
        if not module_info or module_info.parse_errors:
            return []
        
        matched_symbols = target_symbols.intersection(module_info.exported_names)
        
        if not matched_symbols:
            return []
        
        candidate = self._create_candidate(
            module_path=module_info.module_path,
            file_path=file_path,
            matched_symbols=list(matched_symbols)
        )
        
        candidate.score.symbol_match = len(matched_symbols) / len(target_symbols)
        
        return [candidate]
    
    def _get_module_info(self, file_path: Path, project_root: Path) -> Optional[ModuleInfo]:
        if file_path in self._module_cache:
            return self._module_cache[file_path]
        
        parser = ModuleParser(project_root)
        module_info = parser.parse_module(file_path)
        
        self._module_cache[file_path] = module_info
        
        return module_info
    
    def _rank_candidates_by_symbol_match(self, candidates: List[Candidate],
                                       target_symbols: Set[str]) -> List[Candidate]:
        for candidate in candidates:
            match_ratio = len(candidate.matched_symbols) / len(target_symbols)
            candidate.score.symbol_match = match_ratio
            
            if match_ratio == 1.0:
                candidate.confidence = 0.9
            elif match_ratio >= 0.5:
                candidate.confidence = 0.7
            else:
                candidate.confidence = 0.5
        
        return sorted(candidates, key=lambda c: c.score.symbol_match, reverse=True)
    
    def _should_skip_file(self, file_path: Path) -> bool:
        skip_patterns = [
            '__pycache__',
            '.git',
            '.venv',
            'venv',
            'env',
            '.tox',
            'dist',
            'build',
            '.eggs',
            'test_',
            '_test.py',
            'tests/',
            'testing/'
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)