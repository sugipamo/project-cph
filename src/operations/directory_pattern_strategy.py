from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.infrastructure.candidate import BrokenImport, Candidate
from src.core.search_strategy import SearchStrategy, SearchResult


class DirectoryPatternStrategy(SearchStrategy):
    
    def __init__(self):
        self._common_patterns = {
            'models': ['model', 'entity', 'schema', 'dto'],
            'views': ['view', 'ui', 'presentation', 'page'],
            'controllers': ['controller', 'handler', 'endpoint', 'route'],
            'services': ['service', 'manager', 'provider'],
            'utils': ['util', 'helper', 'tool', 'utility'],
            'config': ['config', 'setting', 'configuration'],
            'tests': ['test', 'spec', 'tests'],
            'api': ['api', 'rest', 'graphql', 'endpoint'],
            'db': ['database', 'db', 'repository', 'dao'],
            'auth': ['auth', 'authentication', 'authorization'],
            'middleware': ['middleware', 'interceptor', 'filter'],
            'validators': ['validator', 'validation', 'rule'],
            'serializers': ['serializer', 'marshaller', 'formatter'],
            'exceptions': ['exception', 'error', 'fault'],
            'constants': ['constant', 'const', 'enum'],
        }
        self._max_workers = 4
        self._pattern_cache = {}
    
    @property
    def name(self) -> str:
        return "directory_pattern"
    
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
        
        import_patterns = self._extract_patterns(broken_import)
        if not import_patterns:
            return SearchResult(candidates=[], search_time=time.time() - start_time, metadata={})
        
        pattern_directories = self._find_pattern_directories(project_root)
        
        python_files = []
        for pattern in import_patterns:
            if pattern in pattern_directories:
                for directory in pattern_directories[pattern]:
                    python_files.extend(directory.rglob("*.py"))
        
        python_files = list(set(python_files))
        
        file_scores = []
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_to_file = {
                executor.submit(self._score_file, file_path, import_patterns, broken_import, project_root): file_path
                for file_path in python_files
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    score, module_path = future.result()
                    if score > 0:
                        file_scores.append((file_path, score, module_path))
                except Exception:
                    continue
        
        file_scores.sort(key=lambda x: x[1], reverse=True)
        
        for file_path, score, module_path in file_scores[:10]:
            candidate = self._create_candidate(
                module_path=module_path,
                file_path=file_path,
                matched_symbols=[]
            )
            candidate.raw_score = score
            candidates.append(candidate)
        
        search_time = time.time() - start_time
        return SearchResult(
            candidates=candidates,
            search_time=search_time,
            metadata={
                "patterns_found": list(import_patterns),
                "directories_scanned": sum(len(dirs) for dirs in pattern_directories.values()),
                "files_scanned": len(python_files)
            }
        )
    
    def _extract_patterns(self, broken_import: BrokenImport) -> Set[str]:
        patterns = set()
        
        if broken_import.module_path:
            parts = broken_import.module_path.split('.')
            for part in parts:
                for category, keywords in self._common_patterns.items():
                    if any(keyword in part.lower() for keyword in keywords):
                        patterns.add(category)
                
                for pattern_name in self._common_patterns.keys():
                    if pattern_name in part.lower():
                        patterns.add(pattern_name)
        
        if broken_import.imported_names:
            for name in broken_import.imported_names:
                if name != "*":
                    name_lower = name.lower()
                    for category, keywords in self._common_patterns.items():
                        if any(keyword in name_lower for keyword in keywords):
                            patterns.add(category)
        
        return patterns
    
    def _find_pattern_directories(self, project_root: Path) -> Dict[str, List[Path]]:
        pattern_dirs = {pattern: [] for pattern in self._common_patterns.keys()}
        
        for path in project_root.rglob("*"):
            if path.is_dir() and not any(part.startswith('.') for part in path.parts):
                dir_name_lower = path.name.lower()
                for pattern, keywords in self._common_patterns.items():
                    if any(keyword in dir_name_lower for keyword in keywords):
                        pattern_dirs[pattern].append(path)
        
        return pattern_dirs
    
    def _score_file(self, file_path: Path, import_patterns: Set[str], 
                   broken_import: BrokenImport, project_root: Path) -> tuple[float, str]:
        score = 0.0
        
        file_name_lower = file_path.stem.lower()
        directory_path_lower = str(file_path.parent).lower()
        
        for pattern in import_patterns:
            keywords = self._common_patterns.get(pattern, [])
            
            for keyword in keywords:
                if keyword in file_name_lower:
                    score += 2.0
                if keyword in directory_path_lower:
                    score += 1.0
        
        if broken_import.module_path:
            module_parts = broken_import.module_path.split('.')
            for part in module_parts:
                if part.lower() in file_name_lower:
                    score += 3.0
        
        if broken_import.imported_names:
            for name in broken_import.imported_names:
                if name != "*" and name.lower() in file_name_lower:
                    score += 2.5
        
        relative_path = file_path.relative_to(project_root)
        path_parts = list(relative_path.parts)
        if path_parts[-1].endswith('.py'):
            path_parts[-1] = path_parts[-1][:-3]
        if path_parts[-1] == '__init__':
            path_parts = path_parts[:-1]
        
        module_path = ".".join(path_parts)
        
        return score, module_path