from pathlib import Path
from typing import Optional, Set
from datetime import datetime
from src.infrastructure.module_info import ModuleInfo, ExportedSymbol
from src.operations.results.__init__ import ASTAnalyzer
class ModuleParser:

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ast_analyzer = ASTAnalyzer()

    def parse_module(self, file_path: Path) -> Optional[ModuleInfo]:
        if not file_path.exists() or not file_path.is_file():
            return None
        tree = self.ast_analyzer.parse_file(file_path)
        if not tree:
            return self._create_error_module_info(file_path, ['Failed to parse AST'])
        module_path = self._calculate_module_path(file_path)
        if not module_path:
            return None
        exported_symbols = self.ast_analyzer.extract_exported_symbols()
        imported_modules = self._extract_imported_modules()
        dependencies = self._extract_dependencies(imported_modules)
        stat = file_path.stat()
        last_modified = datetime.fromtimestamp(stat.st_mtime)
        return ModuleInfo(file_path=file_path, module_path=module_path, exported_symbols=exported_symbols, imported_modules=imported_modules, dependencies=dependencies, last_modified=last_modified, parse_errors=[], metadata={'file_size': stat.st_size, 'line_count': self._count_lines(file_path)})

    def _calculate_module_path(self, file_path: Path) -> Optional[str]:
        try:
            rel_path = file_path.relative_to(self.project_root)
            parts = list(rel_path.parts)
            if parts[-1] == '__init__.py':
                parts = parts[:-1]
            elif parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]
            else:
                return None
            return '.'.join(parts) if parts else None
        except ValueError:
            return None

    def _extract_imported_modules(self) -> Set[str]:
        imports = self.ast_analyzer.extract_imports()
        modules = set()
        for import_info in imports:
            if import_info.module:
                modules.add(import_info.module)
                root_module = import_info.module.split('.')[0]
                modules.add(root_module)
        return modules

    def _extract_dependencies(self, imported_modules: Set[str]) -> Set[Path]:
        dependencies = set()
        for module in imported_modules:
            module_file = self._find_module_file(module)
            if module_file and module_file.exists():
                dependencies.add(module_file)
        return dependencies

    def _find_module_file(self, module_name: str) -> Optional[Path]:
        parts = module_name.split('.')
        possible_paths = [self.project_root / Path(*parts[:-1]) / f'{parts[-1]}.py', self.project_root / Path(*parts) / '__init__.py']
        for path in possible_paths:
            if path.exists():
                return path
        return None

    def _create_error_module_info(self, file_path: Path, errors: list) -> ModuleInfo:
        module_path = self._calculate_module_path(file_path) or str(file_path)
        return ModuleInfo(file_path=file_path, module_path=module_path, exported_symbols=set(), imported_modules=set(), dependencies=set(), last_modified=datetime.now(), parse_errors=errors)

    def _count_lines(self, file_path: Path) -> int:
        try:
            return sum((1 for _ in file_path.open('r', encoding='utf-8')))
        except Exception:
            return 0