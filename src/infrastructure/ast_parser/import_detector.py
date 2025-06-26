import ast
import re
from pathlib import Path
from typing import List, Set, Optional

from src.domain.models import BrokenImport, ImportType
from .ast_analyzer import ASTAnalyzer, ImportInfo


class ImportDetector:
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ast_analyzer = ASTAnalyzer()
        self._available_modules: Optional[Set[str]] = None
        
    def detect_broken_imports(self, file_path: Path) -> List[BrokenImport]:
        tree = self.ast_analyzer.parse_file(file_path)
        if not tree:
            return self._fallback_import_detection(file_path)
        
        available_modules = self._get_available_modules()
        broken_imports = []
        
        for import_info, error_msg in self.ast_analyzer.find_broken_imports(available_modules):
            broken_import = self._create_broken_import(
                file_path, import_info, error_msg
            )
            if broken_import:
                broken_imports.append(broken_import)
        
        return broken_imports
    
    def _create_broken_import(self, file_path: Path, 
                            import_info: ImportInfo,
                            error_msg: str) -> Optional[BrokenImport]:
        import_type = self._determine_import_type(import_info)
        import_statement = self._reconstruct_import_statement(import_info)
        
        return BrokenImport(
            file_path=file_path,
            line_number=import_info.line_number,
            import_statement=import_statement,
            import_type=import_type,
            module_path=import_info.module,
            imported_names=import_info.names,
            relative_level=import_info.level,
            error_message=error_msg
        )
    
    def _determine_import_type(self, import_info: ImportInfo) -> ImportType:
        if import_info.level > 0:
            return ImportType.RELATIVE
        elif import_info.is_from_import:
            return ImportType.FROM_IMPORT
        else:
            return ImportType.IMPORT
    
    def _reconstruct_import_statement(self, import_info: ImportInfo) -> str:
        if import_info.is_from_import:
            dots = '.' * import_info.level
            module_part = f"{dots}{import_info.module}" if import_info.module else dots
            names_part = ', '.join(import_info.names) if import_info.names else '*'
            return f"from {module_part} import {names_part}"
        else:
            return f"import {import_info.module}"
    
    def _get_available_modules(self) -> Set[str]:
        if self._available_modules is None:
            self._available_modules = self._scan_project_modules()
        return self._available_modules
    
    def _scan_project_modules(self) -> Set[str]:
        modules = set()
        
        for py_file in self.project_root.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            try:
                rel_path = py_file.relative_to(self.project_root)
                module_path = self._path_to_module(rel_path)
                modules.add(module_path)
                
                parts = module_path.split('.')
                for i in range(1, len(parts)):
                    modules.add('.'.join(parts[:i]))
                    
            except ValueError:
                continue
        
        return modules
    
    def _path_to_module(self, rel_path: Path) -> str:
        parts = list(rel_path.parts)
        
        if parts[-1] == '__init__.py':
            parts = parts[:-1]
        elif parts[-1].endswith('.py'):
            parts[-1] = parts[-1][:-3]
        
        return '.'.join(parts)
    
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
            '*.egg-info'
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)
    
    def _fallback_import_detection(self, file_path: Path) -> List[BrokenImport]:
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return []
        
        broken_imports = []
        import_pattern = re.compile(
            r'^(from\s+([.\w]+)\s+import\s+([^#\n]+)|import\s+([^#\n]+))',
            re.MULTILINE
        )
        
        for line_num, line in enumerate(content.splitlines(), 1):
            match = import_pattern.match(line.strip())
            if match:
                if match.group(2):
                    module = match.group(2)
                    names = [n.strip() for n in match.group(3).split(',')]
                    import_type = ImportType.FROM_IMPORT
                    level = len(module) - len(module.lstrip('.'))
                else:
                    module = match.group(4).strip()
                    names = []
                    import_type = ImportType.IMPORT
                    level = 0
                
                if level > 0:
                    import_type = ImportType.RELATIVE
                
                broken_imports.append(BrokenImport(
                    file_path=file_path,
                    line_number=line_num,
                    import_statement=line.strip(),
                    import_type=import_type,
                    module_path=module.lstrip('.'),
                    imported_names=names,
                    relative_level=level,
                    error_message="Unable to verify import"
                ))
        
        return broken_imports