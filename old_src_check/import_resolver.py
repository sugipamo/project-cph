"""
インポート解決モジュール - 実行前後のインポート修正
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
import ast
import re
from dataclasses import dataclass

from src_check.models.check_result import CheckResult, FailureLocation
from src_check.utils.broken_import import BrokenImport, ImportType


class ImportResolver:
    """インポートの検証と修正を行うクラス"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_root = project_root / "src"
        self.broken_imports: List[Dict[str, any]] = []
        self.fixed_imports: List[Dict[str, any]] = []
    
    def check_imports(self, target_dir: Path = None) -> CheckResult:
        """指定ディレクトリのインポートをチェック"""
        if target_dir is None:
            target_dir = self.src_root
        
        print(f"🔍 インポートチェック開始: {target_dir}")
        
        self.broken_imports.clear()
        python_files = list(target_dir.rglob("*.py"))
        
        for py_file in python_files:
            try:
                self._check_file_imports(py_file)
            except Exception as e:
                print(f"  ⚠️  {py_file.relative_to(self.project_root)}: {e}")
        
        # 結果をCheckResult形式で返す
        failure_locations = []
        for broken in self.broken_imports:
            failure_locations.append(FailureLocation(
                file_path=str(broken['file'].relative_to(self.project_root)),
                line_number=broken['line']
            ))
        
        if failure_locations:
            fix_policy = (
                f"{len(self.broken_imports)}個の壊れたインポートが検出されました。\n"
                "- 相対インポートを絶対インポートに変換\n"
                "- 移動されたモジュールのパスを更新"
            )
        else:
            fix_policy = "すべてのインポートは正常です。"
        
        return CheckResult(
            title="import_check",
            failure_locations=failure_locations,
            fix_policy=fix_policy,
            fix_example_code=None
        )
    
    def _check_file_imports(self, file_path: Path):
        """ファイル内のインポートをチェック"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return  # 構文エラーのファイルはスキップ
        
        lines = content.splitlines()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not self._validate_import(alias.name, file_path):
                        self.broken_imports.append({
                            'file': file_path,
                            'line': node.lineno,
                            'import': lines[node.lineno - 1].strip() if node.lineno <= len(lines) else f"import {alias.name}",
                            'module': alias.name,
                            'type': 'import',
                            'ast_node': node
                        })
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                level = node.level
                import_names = [alias.name for alias in node.names]
                
                # 相対インポートの場合
                if level > 0:
                    abs_module = self._resolve_relative_import(
                        file_path, module, level
                    )
                    if abs_module and not self._validate_import(abs_module, file_path):
                        self.broken_imports.append({
                            'file': file_path,
                            'line': node.lineno,
                            'import': lines[node.lineno - 1].strip() if node.lineno <= len(lines) else f"from {'.' * level}{module} import {', '.join(import_names)}",
                            'module': module,
                            'import_names': import_names,
                            'type': 'relative',
                            'level': level,
                            'resolved': abs_module,
                            'ast_node': node
                        })
                else:
                    # 絶対インポート
                    if module and module.startswith('src.') and not self._validate_import(module, file_path):
                        # 正しいモジュールを探す
                        correct_module = self._find_correct_module(module, import_names)
                        self.broken_imports.append({
                            'file': file_path,
                            'line': node.lineno,
                            'import': lines[node.lineno - 1].strip() if node.lineno <= len(lines) else f"from {module} import {', '.join(import_names)}",
                            'module': module,
                            'import_names': import_names,
                            'type': 'from',
                            'correct_module': correct_module,
                            'ast_node': node
                        })
    
    def _validate_import(self, module_name: str, from_file: Path) -> bool:
        """インポートが有効かチェック"""
        if not module_name or not module_name.startswith('src'):
            return True  # 標準ライブラリや外部パッケージは対象外
        
        # モジュールパスをファイルパスに変換
        parts = module_name.split('.')
        
        # ファイルとして存在するかチェック
        py_file = self.project_root / Path(*parts).with_suffix('.py')
        if py_file.exists():
            return True
        
        # ディレクトリ（パッケージ）として存在するかチェック
        pkg_dir = self.project_root / Path(*parts)
        if pkg_dir.is_dir() and (pkg_dir / '__init__.py').exists():
            return True
        
        return False
    
    def _resolve_relative_import(self, file_path: Path, module: str, level: int) -> Optional[str]:
        """相対インポートを絶対インポートに解決"""
        try:
            # ファイルの親ディレクトリから上に遡る
            current = file_path.parent
            for _ in range(level - 1):
                current = current.parent
            
            # srcディレクトリからの相対パスを取得
            rel_path = current.relative_to(self.project_root)
            
            # モジュール名を構築
            parts = list(rel_path.parts)
            if module:
                parts.extend(module.split('.'))
            
            return '.'.join(parts)
        except ValueError:
            return None
    
    def fix_imports(self, dry_run: bool = True) -> CheckResult:
        """壊れたインポートを修正"""
        if not self.broken_imports:
            return CheckResult(
                title="import_fix",
                failure_locations=[],
                fix_policy="修正が必要なインポートはありません。",
                fix_example_code=None
            )
        
        print(f"🔧 インポート修正{'（ドライラン）' if dry_run else ''}を開始...")
        
        self.fixed_imports.clear()
        files_to_update: Dict[Path, List[Tuple[int, str, str]]] = {}
        
        for broken in self.broken_imports:
            file_path = broken['file']
            line_no = broken['line']
            old_import = broken['import']
            
            # 修正案を生成
            new_import = self._generate_fix(broken)
            if new_import and new_import != old_import:
                if file_path not in files_to_update:
                    files_to_update[file_path] = []
                files_to_update[file_path].append((line_no, old_import, new_import))
                self.fixed_imports.append({
                    'file': file_path,
                    'line': line_no,
                    'old': old_import,
                    'new': new_import
                })
        
        # 実際の修正を実行
        if not dry_run:
            for file_path, updates in files_to_update.items():
                self._update_file_imports(file_path, updates)
        
        # 結果を返す
        return CheckResult(
            title="import_fix",
            failure_locations=[],
            fix_policy=f"{len(self.fixed_imports)}個のインポートを{'修正しました' if not dry_run else '修正可能です'}。",
            fix_example_code=self._generate_fix_examples()
        )
    
    def _find_correct_module(self, wrong_module: str, import_names: List[str]) -> Optional[str]:
        """動的に正しいモジュールパスを探す"""
        # シンボル名から動的に検索
        if import_names:
            for name in import_names:
                # 完全一致でファイル名を検索
                exact_files = list(self.src_root.rglob(f"**/{name}.py"))
                if exact_files:
                    # 最も適切なファイルを選択
                    best_match = self._select_best_match(exact_files, wrong_module, name)
                    if best_match:
                        return self._path_to_module(best_match)
                
                # snake_case変換して検索
                snake_name = self._camel_to_snake(name)
                if snake_name != name.lower():  # CamelCaseの場合のみ
                    snake_files = list(self.src_root.rglob(f"**/{snake_name}.py"))
                    if snake_files:
                        best_match = self._select_best_match(snake_files, wrong_module, name)
                        if best_match:
                            return self._path_to_module(best_match)
                
                # クラス名としてファイル内を検索
                class_matches = self._search_class_in_files(name)
                if class_matches:
                    best_match = self._select_best_match(class_matches, wrong_module, name)
                    if best_match:
                        return self._path_to_module(best_match)
        
        # モジュール名の最後の部分からファイルを探す
        module_parts = wrong_module.split('.')
        if len(module_parts) > 2:  # src.xxx.yyyの形式
            last_part = module_parts[-1]
            possible_files = list(self.src_root.rglob(f"**/{last_part}.py"))
            if possible_files:
                best_match = self._select_best_match(possible_files, wrong_module, last_part)
                if best_match:
                    return self._path_to_module(best_match)
        
        return None
    
    def _search_class_in_files(self, class_name: str) -> List[Path]:
        """ファイル内に指定されたクラスが定義されているか検索"""
        matches = []
        pattern = f"class {class_name}"
        
        for py_file in self.src_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if pattern in content:
                        # ASTで確認
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef) and node.name == class_name:
                                matches.append(py_file)
                                break
            except:
                continue
        
        return matches
    
    def _select_best_match(self, candidates: List[Path], original_module: str, symbol_name: str) -> Optional[Path]:
        """複数の候補から最適なファイルを選択"""
        if not candidates:
            return None
        
        if len(candidates) == 1:
            return candidates[0]
        
        # スコアリングで最適な候補を選択
        scored_candidates = []
        
        for candidate in candidates:
            score = 0
            rel_path = candidate.relative_to(self.src_root)
            path_parts = list(rel_path.parts)
            
            # 元のモジュールパスとの類似度
            original_parts = original_module.split('.')[1:]  # src.を除く
            for part in original_parts:
                if part in path_parts:
                    score += 10
            
            # ファイル名がシンボル名と一致
            if candidate.stem == symbol_name.lower() or candidate.stem == self._camel_to_snake(symbol_name):
                score += 20
            
            # ディレクトリ深度（浅いほど優先）
            score -= len(path_parts)
            
            # __init__.pyは優先度を下げる
            if candidate.name == '__init__.py':
                score -= 5
            
            scored_candidates.append((score, candidate))
        
        # スコアが最も高い候補を選択
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return scored_candidates[0][1]
    
    def _camel_to_snake(self, name: str) -> str:
        """CamelCaseをsnake_caseに変換"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _path_to_module(self, file_path: Path) -> str:
        """ファイルパスをモジュールパスに変換"""
        try:
            rel_path = file_path.relative_to(self.project_root)
            parts = list(rel_path.parts)
            if parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]
            return '.'.join(parts)
        except ValueError:
            return ''
    
    def _generate_fix(self, broken_import: Dict) -> Optional[str]:
        """インポートの修正案を生成"""
        import_type = broken_import['type']
        
        if import_type == 'relative' and 'resolved' in broken_import:
            # 相対インポートを絶対インポートに
            module = broken_import['resolved']
            if 'import_names' in broken_import:
                return f"from {module} import {', '.join(broken_import['import_names'])}"
            else:
                return f"import {module}"
        
        elif import_type == 'from' and 'correct_module' in broken_import and broken_import['correct_module']:
            # 間違ったモジュールを正しいものに修正
            correct = broken_import['correct_module']
            if 'import_names' in broken_import:
                return f"from {correct} import {', '.join(broken_import['import_names'])}"
        
        elif import_type == 'import' and 'correct_module' in broken_import and broken_import['correct_module']:
            # importの修正
            return f"import {broken_import['correct_module']}"
        
        return None
    
    def _update_file_imports(self, file_path: Path, updates: List[Tuple[int, str, str]]):
        """ファイル内のインポートを更新"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 行番号でソート（降順）して、後ろから更新
            updates_sorted = sorted(updates, key=lambda x: x[0], reverse=True)
            
            for line_no, old_import, new_import in updates_sorted:
                if 0 < line_no <= len(lines):
                    # 行を置換
                    line_idx = line_no - 1
                    original_line = lines[line_idx]
                    
                    # インポート文を含む行を新しいインポート文で置換
                    # インデントを保持
                    indent = len(original_line) - len(original_line.lstrip())
                    new_line = ' ' * indent + new_import + '\n'
                    lines[line_idx] = new_line
            
            # ファイルに書き戻す
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print(f"  ✓ {file_path.relative_to(self.project_root)}: {len(updates)}個のインポートを修正")
            
        except Exception as e:
            print(f"  ✗ {file_path.relative_to(self.project_root)}: 修正失敗 - {e}")
    
    def _generate_fix_examples(self) -> Optional[str]:
        """修正例を生成"""
        if not self.fixed_imports:
            return None
        
        examples = []
        for fix in self.fixed_imports[:3]:  # 最初の3つ
            examples.append(f"# {fix['file'].name}:{fix['line']}\n{fix['old']}\n↓\n{fix['new']}")
        
        return "\n\n".join(examples)