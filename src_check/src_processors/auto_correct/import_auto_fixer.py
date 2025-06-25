#!/usr/bin/env python3
"""
インポートエラー自動修正スクリプト

reorganize_report.jsonを基に、移動されたモジュールへのインポートを自動的に修正します。
"""

import ast
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime


class ImportAutoFixer:
    """インポート文を自動修正するクラス"""
    
    def __init__(self, reorganize_report_path: str, project_root: str = "."):
        """
        Args:
            reorganize_report_path: reorganize_report.jsonのパス
            project_root: プロジェクトのルートディレクトリ
        """
        self.project_root = Path(project_root).resolve()
        self.report = self._load_reorganize_report(reorganize_report_path)
        self.move_mapping = self._create_move_mapping()
        self.module_mapping = self._create_module_mapping()
        self.fixed_files = []
        self.errors = []
        
    def _load_reorganize_report(self, path: str) -> dict:
        """reorganize reportを読み込む"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def _create_move_mapping(self) -> Dict[str, str]:
        """ファイルパスのマッピングを作成"""
        mapping = {}
        for old_path, new_path in self.report.get('move_plan', {}).items():
            # 絶対パスを相対パスに変換
            old_rel = Path(old_path).relative_to(self.project_root)
            new_rel = Path(new_path).relative_to(self.project_root)
            mapping[str(old_rel)] = str(new_rel)
        return mapping
        
    def _create_module_mapping(self) -> Dict[str, str]:
        """モジュール名のマッピングを作成"""
        mapping = {}
        
        # ファイルパスからモジュール名への変換
        for old_path, new_path in self.move_mapping.items():
            # .pyを除去してモジュール名に変換
            old_module = old_path.replace('.py', '').replace('/', '.')
            new_module = new_path.replace('.py', '').replace('/', '.')
            
            # __init__.pyの場合はディレクトリ名までとする
            if old_module.endswith('.__init__'):
                old_module = old_module[:-9]
            if new_module.endswith('.__init__'):
                new_module = new_module[:-9]
                
            mapping[old_module] = new_module
            
            # ディレクトリレベルのマッピングも追加
            # 例: src.services.cli_app -> src.core.cli_app
            old_parts = old_module.split('.')
            new_parts = new_module.split('.')
            
            if len(old_parts) >= 3 and len(new_parts) >= 3:
                # src.services.xxx -> src.core.xxx のパターン
                old_prefix = '.'.join(old_parts[:3])
                new_prefix = '.'.join(new_parts[:3])
                if old_prefix not in mapping:
                    mapping[old_prefix] = new_prefix
                    
        return mapping
        
    def fix_imports_in_file(self, file_path: str) -> bool:
        """ファイル内のインポート文を修正"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            modified = False
            
            # import文のパターンを検索して修正
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                new_line = self._fix_import_line(line)
                if new_line != line:
                    modified = True
                new_lines.append(new_line)
                
            if modified:
                new_content = '\n'.join(new_lines)
                
                # ASTで構文チェック
                try:
                    ast.parse(new_content)
                except SyntaxError as e:
                    self.errors.append({
                        'file': file_path,
                        'error': f"Syntax error after fix: {e}",
                        'line': line
                    })
                    return False
                    
                # ファイルに書き込み
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                    
                self.fixed_files.append({
                    'file': file_path,
                    'changes': self._diff_changes(original_content, new_content)
                })
                return True
                
        except Exception as e:
            self.errors.append({
                'file': file_path,
                'error': str(e)
            })
            return False
            
        return False
        
    def _fix_import_line(self, line: str) -> str:
        """インポート行を修正"""
        # from ... import ... のパターン
        from_match = re.match(r'^(\s*from\s+)([\w\.]+)(\s+import\s+.+)$', line)
        if from_match:
            indent, module_name, import_part = from_match.groups()
            new_module = self._map_module_name(module_name)
            if new_module != module_name:
                return f"{indent}{new_module}{import_part}"
                
        # import ... のパターン
        import_match = re.match(r'^(\s*import\s+)([\w\.]+)(.*)$', line)
        if import_match:
            indent, module_name, rest = import_match.groups()
            new_module = self._map_module_name(module_name)
            if new_module != module_name:
                return f"{indent}{new_module}{rest}"
                
        return line
        
    def _map_module_name(self, module_name: str) -> str:
        """モジュール名をマッピング"""
        # 完全一致を試す
        if module_name in self.module_mapping:
            return self.module_mapping[module_name]
            
        # 部分一致を試す（プレフィックスマッチ）
        for old_module, new_module in self.module_mapping.items():
            if module_name.startswith(old_module + '.'):
                # 置換
                return module_name.replace(old_module, new_module, 1)
                
        # 特殊なケースの処理
        # src.cli.cli_app -> src.core.cli_app (cli_appがcoreに移動)
        if module_name == 'src.cli.cli_app':
            return 'src.core.cli_app'
            
        # src.workflow.xxx -> 確認が必要（一部はcoreに移動）
        if module_name.startswith('src.workflow.'):
            # workflow_execution_service と workflow_result はcoreに移動
            if 'workflow_execution_service' in module_name:
                return module_name.replace('src.workflow.', 'src.core.workflow_execution_svc.')
            elif 'workflow_result' in module_name:
                return module_name.replace('src.workflow.', 'src.core.workflow_result.')
                
        # src.configuration.xxx -> 確認が必要（一部はcoreに移動）
        if module_name.startswith('src.configuration.'):
            # config_resolver系はcoreに移動
            if 'resolver.config_resolver' in module_name:
                return module_name.replace('src.configuration.resolver.', 'src.core.configuration.')
            elif 'resolver.config_node' in module_name:
                return module_name.replace('src.configuration.resolver.', 'src.core.configuration.')
                
        # src.context.user_input_parser -> src.core.user_input_parser
        if module_name == 'src.context.user_input_parser.user_input_parser':
            return 'src.core.user_input_parser.user_input_parser'
            
        return module_name
        
    def _diff_changes(self, old_content: str, new_content: str) -> List[str]:
        """変更内容の差分を生成"""
        changes = []
        old_lines = old_content.split('\n')
        new_lines = new_content.split('\n')
        
        for i, (old, new) in enumerate(zip(old_lines, new_lines)):
            if old != new:
                changes.append(f"Line {i+1}: {old.strip()} -> {new.strip()}")
                
        return changes
        
    def fix_all_imports(self, target_dir: str = "src") -> Dict[str, any]:
        """指定ディレクトリ以下の全ファイルのインポートを修正"""
        target_path = self.project_root / target_dir
        
        # 全Pythonファイルを検索
        python_files = list(target_path.rglob("*.py"))
        
        fixed_count = 0
        for file_path in python_files:
            if self.fix_imports_in_file(str(file_path)):
                fixed_count += 1
                
        return {
            'total_files': len(python_files),
            'fixed_files': fixed_count,
            'fixed_details': self.fixed_files,
            'errors': self.errors
        }
        
    def generate_report(self, output_path: str):
        """修正レポートを生成"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_fixed': len(self.fixed_files),
                'total_errors': len(self.errors)
            },
            'fixed_files': self.fixed_files,
            'errors': self.errors,
            'module_mapping': self.module_mapping
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix import errors after file reorganization')
    parser.add_argument('--report', required=True, help='Path to reorganize_report.json')
    parser.add_argument('--target', default='src', help='Target directory to fix imports')
    parser.add_argument('--output', default='import_fix_report.json', help='Output report path')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    fixer = ImportAutoFixer(args.report)
    
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified")
        # TODO: ドライランモードの実装
    else:
        result = fixer.fix_all_imports(args.target)
        
        print(f"Fixed {result['fixed_files']} out of {result['total_files']} files")
        if result['errors']:
            print(f"Errors occurred in {len(result['errors'])} files")
            
        fixer.generate_report(args.output)
        print(f"Report saved to {args.output}")


if __name__ == '__main__':
    main()