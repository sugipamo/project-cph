from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
import time
import difflib
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.infrastructure.candidate import BrokenImport, Candidate, ImportType
from src.core.search_strategy import SearchStrategy, SearchResult


class PathBasedStrategy(SearchStrategy):
    
    def __init__(self):
        self._similarity_threshold = 0.6
        self._max_workers = 4
    
    @property
    def name(self) -> str:
        return "path_based"
    
    @property
    def cost_level(self) -> int:
        return 2
    
    def is_applicable(self, broken_import: BrokenImport) -> bool:
        return True
    
    def search(self, broken_import: BrokenImport, 
              project_root: Path,
              context: Optional[Dict[str, Any]] = None) -> SearchResult:
        start_time = time.time()
        candidates = []
        
        import_parts = self._get_import_parts(broken_import)
        if not import_parts:
            return SearchResult(candidates=[], search_time=time.time() - start_time, metadata={})
        
        python_files = list(project_root.rglob("*.py"))
        
        file_similarities = []
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_to_file = {
                executor.submit(self._calculate_path_similarity, file_path, import_parts, project_root): file_path
                for file_path in python_files
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    similarity, module_path = future.result()
                    if similarity >= self._similarity_threshold:
                        file_similarities.append((file_path, similarity, module_path))
                except Exception:
                    continue
        
        file_similarities.sort(key=lambda x: x[1], reverse=True)
        
        for file_path, similarity, module_path in file_similarities[:10]:
            candidate = self._create_candidate(
                module_path=module_path,
                file_path=file_path,
                matched_symbols=[]
            )
            candidate.raw_score = similarity
            candidates.append(candidate)
        
        search_time = time.time() - start_time
        return SearchResult(
            candidates=candidates,
            search_time=search_time,
            metadata={
                "files_scanned": len(python_files),
                "similarity_threshold": self._similarity_threshold
            }
        )
    
    def _get_import_parts(self, broken_import: BrokenImport) -> List[str]:
        if broken_import.module_path:
            parts = broken_import.module_path.split('.')
        else:
            parts = []
        
        if broken_import.import_type == ImportType.FROM_IMPORT and broken_import.imported_names:
            for name in broken_import.imported_names:
                if name != "*":
                    parts.append(name)
                    break
        
        return parts
    
    def _calculate_path_similarity(self, file_path: Path, import_parts: List[str], 
                                 project_root: Path) -> tuple[float, str]:
        relative_path = file_path.relative_to(project_root)
        path_parts = list(relative_path.parts)
        
        if path_parts[-1].endswith('.py'):
            path_parts[-1] = path_parts[-1][:-3]
        
        if path_parts[-1] == '__init__':
            path_parts = path_parts[:-1]
        
        if not import_parts or not path_parts:
            return 0.0, ""
        
        similarity_scores = []
        
        for i in range(len(path_parts)):
            current_parts = path_parts[i:]
            similarity = difflib.SequenceMatcher(None, import_parts, current_parts).ratio()
            similarity_scores.append(similarity)
        
        for i in range(1, len(import_parts) + 1):
            current_import_parts = import_parts[-i:]
            for j in range(len(path_parts)):
                current_path_parts = path_parts[j:j+i]
                if len(current_path_parts) == i:
                    similarity = difflib.SequenceMatcher(None, current_import_parts, current_path_parts).ratio()
                    similarity_scores.append(similarity)
        
        best_similarity = max(similarity_scores) if similarity_scores else 0.0
        
        module_path = ".".join(path_parts)
        
        return best_similarity, module_path