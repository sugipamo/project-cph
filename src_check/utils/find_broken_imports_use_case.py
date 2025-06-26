from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

from src.domain.models import BrokenImport
from src.domain.models.check_result import CheckResult
from src.domain.services.circular_import_detector import CircularImportDetector
from src.infrastructure.ast_parser import ImportDetector, ModuleParser


import logging
@dataclass
class FindBrokenImportsRequest:
    project_root: Path
    target_files: List[Path] = None
    exclude_patterns: List[str] = None
    check_circular_imports: bool = True


@dataclass 
class FindBrokenImportsResponse:
    broken_imports: List[BrokenImport]
    total_files_scanned: int
    files_with_errors: List[Path]
    metadata: Dict[str, Any]
    check_result: CheckResult


class FindBrokenImportsUseCase:
    
    def __init__(self):
        self._import_detector: ImportDetector = None
        self._module_parser: ModuleParser = None
        self._circular_import_detector: CircularImportDetector = None
        
    def execute(self, request: FindBrokenImportsRequest) -> FindBrokenImportsResponse:
        self._import_detector = ImportDetector(request.project_root)
        self._module_parser = ModuleParser(request.project_root)
        self._circular_import_detector = CircularImportDetector()
        
        files_to_scan = self._get_files_to_scan(request)
        broken_imports = []
        files_with_errors = []
        check_result = CheckResult()
        
        check_result.total_files = len(files_to_scan)
        check_result.total_imports = 0
        
        # スキャンとモジュール情報収集
        modules = []
        for file_path in files_to_scan:
            try:
                file_broken_imports = self._import_detector.detect_broken_imports(file_path)
                broken_imports.extend(file_broken_imports)
                
                # モジュール情報も収集
                module_info = self._module_parser.parse_module(file_path)
                if module_info:
                    modules.append(module_info)
                    check_result.total_imports += len(module_info.imported_modules)
                    
            except Exception as e:
                files_with_errors.append(file_path)
                check_result.add_error(file_path, str(e))
        
        broken_imports_by_file = {}
        for broken_import in broken_imports:
            file_key = str(broken_import.file_path)
            if file_key not in broken_imports_by_file:
                broken_imports_by_file[file_key] = []
            broken_imports_by_file[file_key].append(broken_import)
        
        check_result.broken_imports = len(broken_imports)
        check_result.files_with_issues = len(broken_imports_by_file)
        
        # 循環インポート検知
        if request.check_circular_imports and modules:
            self._circular_import_detector.build_import_graph(modules, broken_imports)
            circular_imports = self._circular_import_detector.detect_circular_imports()
            
            for cycle in circular_imports:
                check_result.add_circular_import(cycle)
                
        # 循環インポートが検出された場合はエラーとする
        if check_result.has_circular_imports:
            logger = logging.getLogger(__name__)
            logger.error(f"Circular imports detected: {len(check_result.circular_imports)} cycles found")
            
        return FindBrokenImportsResponse(
            broken_imports=broken_imports,
            total_files_scanned=len(files_to_scan),
            files_with_errors=files_with_errors,
            metadata={
                'broken_imports_count': len(broken_imports),
                'affected_files_count': len(broken_imports_by_file),
                'error_rate': len(files_with_errors) / len(files_to_scan) if files_to_scan else 0,
                'circular_imports_count': len(check_result.circular_imports)
            },
            check_result=check_result
        )
    
    def _get_files_to_scan(self, request: FindBrokenImportsRequest) -> List[Path]:
        if request.target_files:
            return [f for f in request.target_files if f.exists() and f.suffix == '.py']
        
        all_files = list(request.project_root.rglob("*.py"))
        
        if request.exclude_patterns:
            filtered_files = []
            for file_path in all_files:
                if not any(pattern in str(file_path) for pattern in request.exclude_patterns):
                    filtered_files.append(file_path)
            return filtered_files
        
        return all_files