from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re

from src.domain.models import BrokenImport, Candidate


@dataclass
class ImportFix:
    broken_import: BrokenImport
    chosen_candidate: Candidate
    new_import_statement: str


@dataclass
class FixImportsRequest:
    fixes: List[ImportFix]
    dry_run: bool = False
    backup: bool = True


@dataclass
class FixImportsResponse:
    successful_fixes: List[ImportFix]
    failed_fixes: List[tuple]
    files_modified: List[Path]
    backup_files: List[Path]


class FixImportsUseCase:
    
    def execute(self, request: FixImportsRequest) -> FixImportsResponse:
        files_to_fix = self._group_fixes_by_file(request.fixes)
        
        successful_fixes = []
        failed_fixes = []
        files_modified = []
        backup_files = []
        
        for file_path, fixes in files_to_fix.items():
            try:
                if request.backup and not request.dry_run:
                    backup_path = self._create_backup(file_path)
                    backup_files.append(backup_path)
                
                modified_content = self._apply_fixes_to_file(file_path, fixes)
                
                if not request.dry_run:
                    file_path.write_text(modified_content, encoding='utf-8')
                    files_modified.append(file_path)
                
                successful_fixes.extend(fixes)
                
            except Exception as e:
                for fix in fixes:
                    failed_fixes.append((fix, str(e)))
        
        return FixImportsResponse(
            successful_fixes=successful_fixes,
            failed_fixes=failed_fixes,
            files_modified=files_modified,
            backup_files=backup_files
        )
    
    def _group_fixes_by_file(self, fixes: List[ImportFix]) -> Dict[Path, List[ImportFix]]:
        grouped = {}
        for fix in fixes:
            file_path = fix.broken_import.file_path
            if file_path not in grouped:
                grouped[file_path] = []
            grouped[file_path].append(fix)
        
        for file_path in grouped:
            grouped[file_path].sort(
                key=lambda f: f.broken_import.line_number,
                reverse=True
            )
        
        return grouped
    
    def _apply_fixes_to_file(self, file_path: Path, fixes: List[ImportFix]) -> str:
        content = file_path.read_text(encoding='utf-8')
        lines = content.splitlines(keepends=True)
        
        for fix in fixes:
            line_idx = fix.broken_import.line_number - 1
            
            if 0 <= line_idx < len(lines):
                original_line = lines[line_idx]
                indentation = self._get_indentation(original_line)
                new_line = indentation + fix.new_import_statement
                
                if not new_line.endswith('\n'):
                    new_line += '\n'
                
                lines[line_idx] = new_line
        
        return ''.join(lines)
    
    def _get_indentation(self, line: str) -> str:
        match = re.match(r'^(\s*)', line)
        return match.group(1) if match else ''
    
    def _create_backup(self, file_path: Path) -> Path:
        backup_path = file_path.with_suffix(file_path.suffix + '.bak')
        counter = 1
        
        while backup_path.exists():
            backup_path = file_path.with_suffix(f'{file_path.suffix}.bak{counter}')
            counter += 1
        
        content = file_path.read_text(encoding='utf-8')
        backup_path.write_text(content, encoding='utf-8')
        
        return backup_path