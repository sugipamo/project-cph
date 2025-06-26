from dataclasses import dataclass, field
from typing import List, Set, Dict, Tuple
from pathlib import Path


@dataclass
class CircularImport:
    """循環インポートの情報を保持するクラス"""
    cycle_path: List[Path]
    involved_modules: Set[str]
    
    def __str__(self) -> str:
        cycle_str = " -> ".join(str(p) for p in self.cycle_path)
        return f"Circular import detected: {cycle_str}"


@dataclass
class CheckResult:
    """インポートチェックの結果を保持するクラス"""
    total_files: int = 0
    files_with_issues: int = 0
    total_imports: int = 0
    broken_imports: int = 0
    circular_imports: List[CircularImport] = field(default_factory=list)
    errors: Dict[Path, str] = field(default_factory=dict)
    
    @property
    def has_circular_imports(self) -> bool:
        return len(self.circular_imports) > 0
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0 or self.has_circular_imports
    
    def add_circular_import(self, cycle_path: List[Path]) -> None:
        """循環インポートを追加"""
        involved_modules = {str(p) for p in cycle_path}
        circular_import = CircularImport(cycle_path, involved_modules)
        self.circular_imports.append(circular_import)
    
    def add_error(self, file_path: Path, error_message: str) -> None:
        """エラーを追加"""
        self.errors[file_path] = error_message