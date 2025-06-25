#!/usr/bin/env python3
"""
インポート自動修正スクリプト - 最終版
基本的なパターンは自動修正し、複雑なケースは警告を表示
"""
import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
import sys
from dataclasses import dataclass
from enum import Enum

class FixType(Enum):
    """修正タイプの分類"""
    SIMPLE_MOVE = "単純な移動"
    DIRECTORY_STRUCTURE = "ディレクトリ構造の変更"
    PARTIAL_MOVE = "部分的な移動"
    COMPLEX = "複雑なパターン"

@dataclass
class ImportFix:
    """インポート修正情報"""
    file_path: Path
    line_num: int
    original: str
    fixed: str
    fix_type: FixType
    confidence: float  # 0.0 - 1.0

@dataclass
class ImportWarning:
    """インポート警告情報"""
    file_path: Path
    line_num: int
    original: str
    issue: str
    suggestion: Optional[str] = None

class SmartImportFixer:
    def __init__(self):
        self.fixes: List[ImportFix] = []
        self.warnings: List[ImportWarning] = []
        self.errors: List[str] = []
        self.mappings = self._build_comprehensive_mappings()
        
    def _build_comprehensive_mappings(self) -> Dict[str, Dict]:
        """包括的なマッピングを構築"""
        mappings = {}
        
        # 1. coreディレクトリの構造を分析
        core_mappings = self._analyze_core_structure()
        
        # 2. 既知の移動パターンを追加
        known_patterns = {
            # 基本的な移動パターン
            'src.cli': {'new': 'src.core.cli_app', 'type': FixType.SIMPLE_MOVE},
            'src.workflow.workflow_execution_service': {'new': 'src.core.workflow_execution_svc.workflow_execution_service', 'type': FixType.SIMPLE_MOVE},
            'src.workflow.step': {'new': 'src.core.workflow.workflow.step', 'type': FixType.DIRECTORY_STRUCTURE},
            'src.configuration.resolver': {'new': 'src.core.configuration', 'type': FixType.PARTIAL_MOVE},
        }
        
        # マッピングを統合
        mappings.update(core_mappings)
        mappings.update(known_patterns)
        
        return mappings
    
    def _analyze_core_structure(self) -> Dict[str, Dict]:
        """coreディレクトリの構造を詳細に分析"""
        mappings = {}
        core_dir = Path("src/core")
        
        if not core_dir.exists():
            return mappings
            
        for py_file in core_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            rel_path = py_file.relative_to("src")
            parent_name = py_file.parent.name
            file_stem = py_file.stem
            
            # ディレクトリとファイル名が同じケース
            if parent_name == file_stem:
                # 複数の可能な元パスを生成
                possible_origins = [
                    f"src.{file_stem}",
                    f"src.cli.{file_stem}",
                    f"src.services.{file_stem}",
                    f"src.handlers.{file_stem}",
                    f"src.controllers.{file_stem}",
                    f"src.app.{file_stem}",
                    f"src.workflow.{file_stem}",
                ]
                
                new_path = str(rel_path.with_suffix('')).replace('/', '.')
                
                for origin in possible_origins:
                    mappings[origin] = {
                        'new': f"src.{new_path}",
                        'type': FixType.DIRECTORY_STRUCTURE,
                        'confidence': 0.9
                    }
                    
        return mappings
    
    def _analyze_import_line(self, line: str, file_path: Path, line_num: int) -> Tuple[Optional[str], Optional[ImportWarning]]:
        """インポート行を分析し、修正案または警告を返す"""
        
        # from ... import パターン
        from_match = re.match(r'^(\s*)from\s+(\S+)\s+import\s+(.+)$', line)
        if from_match:
            indent, module_path, imports = from_match.groups()
            return self._process_from_import(indent, module_path, imports, line, file_path, line_num)
        
        # import ... パターン
        import_match = re.match(r'^(\s*)import\s+(\S+)(.*)$', line)
        if import_match:
            indent, module_path, rest = import_match.groups()
            return self._process_import(indent, module_path, rest, line, file_path, line_num)
        
        return None, None
    
    def _process_from_import(self, indent: str, module_path: str, imports: str, 
                           original_line: str, file_path: Path, line_num: int) -> Tuple[Optional[str], Optional[ImportWarning]]:
        """from ... import 文を処理"""
        
        # 1. 完全一致のマッピングを確認
        if module_path in self.mappings:
            mapping = self.mappings[module_path]
            new_module = mapping['new']
            fixed_line = f"{indent}from {new_module} import {imports}\n"
            
            self.fixes.append(ImportFix(
                file_path=file_path,
                line_num=line_num,
                original=original_line.strip(),
                fixed=fixed_line.strip(),
                fix_type=mapping['type'],
                confidence=mapping.get('confidence', 1.0)
            ))
            return fixed_line, None
        
        # 2. 部分マッチを試す
        for old_path, mapping in self.mappings.items():
            if module_path.startswith(old_path + "."):
                suffix = module_path[len(old_path):]
                new_module = mapping['new'] + suffix
                fixed_line = f"{indent}from {new_module} import {imports}\n"
                
                self.fixes.append(ImportFix(
                    file_path=file_path,
                    line_num=line_num,
                    original=original_line.strip(),
                    fixed=fixed_line.strip(),
                    fix_type=FixType.PARTIAL_MOVE,
                    confidence=0.8
                ))
                return fixed_line, None
        
        # 3. 警告が必要なケースを検出
        warning = self._check_import_issues(module_path, imports, file_path, line_num, original_line)
        return None, warning
    
    def _process_import(self, indent: str, module_path: str, rest: str, 
                       original_line: str, file_path: Path, line_num: int) -> Tuple[Optional[str], Optional[ImportWarning]]:
        """import 文を処理"""
        
        if module_path in self.mappings:
            mapping = self.mappings[module_path]
            new_module = mapping['new']
            fixed_line = f"{indent}import {new_module}{rest}\n"
            
            self.fixes.append(ImportFix(
                file_path=file_path,
                line_num=line_num,
                original=original_line.strip(),
                fixed=fixed_line.strip(),
                fix_type=mapping['type'],
                confidence=mapping.get('confidence', 1.0)
            ))
            return fixed_line, None
        
        warning = self._check_import_issues(module_path, "", file_path, line_num, original_line)
        return None, warning
    
    def _check_import_issues(self, module_path: str, imports: str, 
                            file_path: Path, line_num: int, original_line: str) -> Optional[ImportWarning]:
        """インポートの問題をチェックし、警告を生成"""
        
        # infrastructure関連の警告
        if 'infrastructure' in module_path and 'core' in str(file_path):
            return ImportWarning(
                file_path=file_path,
                line_num=line_num,
                original=original_line.strip(),
                issue="coreモジュールからinfrastructureへの依存",
                suggestion="依存性注入パターンの使用を検討してください"
            )
        
        # 相対インポートの検出
        if module_path.startswith('.'):
            return ImportWarning(
                file_path=file_path,
                line_num=line_num,
                original=original_line.strip(),
                issue="相対インポートが使用されています",
                suggestion="絶対インポートへの変更を検討してください"
            )
        
        # 移動された可能性があるモジュール
        if any(old in module_path for old in ['services', 'handlers', 'controllers', 'app']):
            return ImportWarning(
                file_path=file_path,
                line_num=line_num,
                original=original_line.strip(),
                issue="移動された可能性があるモジュールへの参照",
                suggestion=f"src.core内を確認してください"
            )
        
        return None
    
    def fix_file(self, file_path: Path) -> Tuple[bool, int]:
        """ファイルを修正し、修正数と警告数を返す"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            modified = False
            new_lines = []
            fix_count = 0
            warning_count = 0
            
            for i, line in enumerate(lines):
                if re.match(r'^\s*(from|import)\s+', line):
                    fixed_line, warning = self._analyze_import_line(line, file_path, i + 1)
                    
                    if fixed_line:
                        new_lines.append(fixed_line)
                        modified = True
                        fix_count += 1
                    else:
                        new_lines.append(line)
                        if warning:
                            self.warnings.append(warning)
                            warning_count += 1
                else:
                    new_lines.append(line)
            
            if modified:
                # 構文チェック
                try:
                    ast.parse(''.join(new_lines))
                    
                    # ファイルに書き込み
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                        
                    return True, fix_count
                except SyntaxError as e:
                    self.errors.append(f"{file_path}: 構文エラー - {e}")
                    return False, 0
                    
        except Exception as e:
            self.errors.append(f"{file_path}: {e}")
            
        return False, 0
    
    def run(self, target_dir: Path, dry_run: bool = False) -> Dict:
        """ディレクトリ内のPythonファイルを処理"""
        python_files = list(target_dir.rglob("*.py"))
        
        print(f"🔍 {len(python_files)}個のPythonファイルを検査中...")
        print(f"📦 {len(self.mappings)}個のマッピングルールを使用\n")
        
        total_fixes = 0
        total_warnings = 0
        modified_files = 0
        
        for py_file in python_files:
            success, fix_count = self.fix_file(py_file)
            if success and fix_count > 0:
                modified_files += 1
                total_fixes += fix_count
                print(f"  ✓ {py_file.relative_to(target_dir)} ({fix_count}箇所修正)")
        
        total_warnings = len(self.warnings)
        
        return {
            'total_files': len(python_files),
            'modified_files': modified_files,
            'total_fixes': total_fixes,
            'total_warnings': total_warnings,
            'fixes': self.fixes,
            'warnings': self.warnings,
            'errors': self.errors
        }
    
    def generate_report(self, result: Dict) -> str:
        """詳細なレポートを生成"""
        report = ["# インポート自動修正レポート\n"]
        
        # サマリー
        report.append("## 📊 サマリー")
        report.append(f"- 検査ファイル数: {result['total_files']}")
        report.append(f"- 修正ファイル数: {result['modified_files']}")
        report.append(f"- 修正箇所数: {result['total_fixes']}")
        report.append(f"- 警告数: {result['total_warnings']}")
        report.append(f"- エラー数: {len(result['errors'])}\n")
        
        # 修正内容
        if result['fixes']:
            report.append("## ✅ 自動修正内容")
            
            # タイプ別に分類
            fixes_by_type = {}
            for fix in result['fixes']:
                if fix.fix_type not in fixes_by_type:
                    fixes_by_type[fix.fix_type] = []
                fixes_by_type[fix.fix_type].append(fix)
            
            for fix_type, fixes in fixes_by_type.items():
                report.append(f"\n### {fix_type.value} ({len(fixes)}件)")
                for fix in fixes[:5]:  # 最初の5件のみ表示
                    report.append(f"- `{fix.file_path.name}:{fix.line_num}`")
                    report.append(f"  - 修正前: `{fix.original}`")
                    report.append(f"  - 修正後: `{fix.fixed}`")
                    report.append(f"  - 信頼度: {fix.confidence:.0%}")
                if len(fixes) > 5:
                    report.append(f"  ... 他 {len(fixes) - 5}件")
        
        # 警告
        if result['warnings']:
            report.append("\n## ⚠️ 警告 (手動確認が必要)")
            
            # 問題別に分類
            warnings_by_issue = {}
            for warning in result['warnings']:
                if warning.issue not in warnings_by_issue:
                    warnings_by_issue[warning.issue] = []
                warnings_by_issue[warning.issue].append(warning)
            
            for issue, warnings in warnings_by_issue.items():
                report.append(f"\n### {issue} ({len(warnings)}件)")
                for warning in warnings[:3]:  # 最初の3件のみ表示
                    report.append(f"- `{warning.file_path.name}:{warning.line_num}`")
                    report.append(f"  - 行: `{warning.original}`")
                    if warning.suggestion:
                        report.append(f"  - 提案: {warning.suggestion}")
                if len(warnings) > 3:
                    report.append(f"  ... 他 {len(warnings) - 3}件")
        
        # エラー
        if result['errors']:
            report.append("\n## ❌ エラー")
            for error in result['errors']:
                report.append(f"- {error}")
        
        # 推奨アクション
        report.append("\n## 📋 推奨アクション")
        if result['total_warnings'] > 0:
            report.append("1. 警告が出ているインポートを手動で確認してください")
            report.append("2. 特にinfrastructure層への依存は設計を見直す必要があります")
        if result['total_fixes'] > 0:
            report.append("3. 修正されたファイルのテストを実行してください")
            report.append("4. `python3 -m py_compile src/**/*.py` で構文チェックを実行してください")
        
        return '\n'.join(report)


def main():
    """メイン処理"""
    print("🔧 スマートインポート修正ツール\n")
    
    # コマンドライン引数の処理
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("🔍 ドライランモード: 変更をプレビューします\n")
    
    fixer = SmartImportFixer()
    
    # src/ディレクトリを処理
    src_dir = Path("src")
    result = fixer.run(src_dir, dry_run=dry_run)
    
    # レポートを生成・保存
    report = fixer.generate_report(result)
    report_path = Path("import_fix_report_final.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 詳細レポート: {report_path}")
    
    # サマリーを表示
    print(f"\n✅ 完了サマリー:")
    print(f"  - {result['total_fixes']}箇所を自動修正")
    print(f"  - {result['total_warnings']}件の警告 (手動確認が必要)")
    
    if result['errors']:
        print(f"  - {len(result['errors'])}件のエラー")
        sys.exit(1)
    
    if result['total_warnings'] > 0:
        print(f"\n⚠️  警告の詳細はレポートを確認してください")


if __name__ == "__main__":
    main()