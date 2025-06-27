import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set, Tuple

from src.infrastructure.module_info import ExportedSymbol


@dataclass
class ImportInfo:
    module: str
    names: List[str]
    level: int
    line_number: int
    is_from_import: bool


class ASTAnalyzer:
    
    def __init__(self):
        self._tree: Optional[ast.AST] = None
        self._source_code: Optional[str] = None
        
    def parse_file(self, file_path: Path) -> Optional[ast.AST]:
        try:
            self._source_code = file_path.read_text(encoding='utf-8')
            self._tree = ast.parse(self._source_code, str(file_path))
            return self._tree
        except (SyntaxError, UnicodeDecodeError) as e:
            return None
    
    def parse_source(self, source_code: str, filename: str = '<string>') -> Optional[ast.AST]:
        try:
            self._source_code = source_code
            self._tree = ast.parse(source_code, filename)
            return self._tree
        except SyntaxError:
            return None
    
    def extract_imports(self) -> List[ImportInfo]:
        if not self._tree:
            return []
        
        imports = []
        for node in ast.walk(self._tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        names=[],
                        level=0,
                        line_number=node.lineno,
                        is_from_import=False
                    ))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                names = [alias.name for alias in node.names]
                imports.append(ImportInfo(
                    module=module,
                    names=names,
                    level=node.level or 0,
                    line_number=node.lineno,
                    is_from_import=True
                ))
        
        return imports
    
    def extract_exported_symbols(self) -> Set[ExportedSymbol]:
        if not self._tree:
            return set()
        
        symbols = set()
        
        for node in ast.walk(self._tree):
            if isinstance(node, ast.ClassDef):
                symbols.add(ExportedSymbol(
                    name=node.name,
                    symbol_type='class',
                    line_number=node.lineno,
                    is_public=not node.name.startswith('_'),
                    docstring=ast.get_docstring(node)
                ))
            elif isinstance(node, ast.FunctionDef):
                symbols.add(ExportedSymbol(
                    name=node.name,
                    symbol_type='function',
                    line_number=node.lineno,
                    is_public=not node.name.startswith('_'),
                    docstring=ast.get_docstring(node)
                ))
            elif isinstance(node, ast.AsyncFunctionDef):
                symbols.add(ExportedSymbol(
                    name=node.name,
                    symbol_type='async_function',
                    line_number=node.lineno,
                    is_public=not node.name.startswith('_'),
                    docstring=ast.get_docstring(node)
                ))
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and isinstance(target.ctx, ast.Store):
                        if self._is_module_level_assignment(node):
                            symbols.add(ExportedSymbol(
                                name=target.id,
                                symbol_type='variable',
                                line_number=node.lineno,
                                is_public=not target.id.startswith('_')
                            ))
        
        if hasattr(self._tree, 'body'):
            for node in self._tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == '__all__':
                            all_names = self._extract_all_names(node.value)
                            if all_names:
                                symbols = {s for s in symbols if s.name in all_names or not s.is_public}
                                for name in all_names:
                                    existing = next((s for s in symbols if s.name == name), None)
                                    if not existing:
                                        symbols.add(ExportedSymbol(
                                            name=name,
                                            symbol_type='unknown',
                                            line_number=0,
                                            is_public=True
                                        ))
        
        return symbols
    
    def _is_module_level_assignment(self, node: ast.AST) -> bool:
        if not self._tree or not hasattr(self._tree, 'body'):
            return False
        return node in self._tree.body
    
    def _extract_all_names(self, node: ast.AST) -> Optional[Set[str]]:
        if isinstance(node, ast.List):
            names = set()
            for elt in node.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    names.add(elt.value)
                elif isinstance(elt, ast.Str):
                    names.add(elt.s)
            return names
        return None
    
    def find_broken_imports(self, available_modules: Set[str]) -> List[Tuple[ImportInfo, str]]:
        broken = []
        imports = self.extract_imports()
        
        for import_info in imports:
            module_parts = import_info.module.split('.') if import_info.module else []
            
            is_broken = True
            for i in range(len(module_parts)):
                partial_module = '.'.join(module_parts[:i+1])
                if partial_module in available_modules:
                    is_broken = False
                    break
            
            if is_broken and import_info.module:
                error_msg = f"Module '{import_info.module}' not found"
                broken.append((import_info, error_msg))
        
        return broken
