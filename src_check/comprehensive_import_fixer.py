#!/usr/bin/env python3
"""
包括的なインポート修正ツール
すべてのインポートスタイルに対応し、正しいモジュールパスを動的に解決する
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field

from models.check_result import CheckResult, FailureLocation


@dataclass
class ImportInfo:
    """インポート情報"""
    line_number: int
    module: str
    names: List[str]  # import される名前のリスト
    is_from_import: bool
    level: int = 0  # 相対インポートのレベル


class ComprehensiveImportFixer:
    """包括的なインポート修正クラス"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_root = project_root / "src"
        self.module_cache: Dict[str, Path] = {}
        self.symbol_cache: Dict[str, Set[Path]] = {}
        self._fix_map: Dict[str, Tuple[str, str]] = {}
        
        # プロジェクト内部モジュールの接頭辞
        self.internal_prefixes = {
            'infrastructure', 'core', 'application', 'domain', 
            'utils', 'operations', 'presentation', 'repositories',
            'services', 'config', 'context', 'formatters', 'parsers',
            'validators', 'views', 'src', 'interfaces', 'data', 'logging',
            'configuration', 'persistence', 'models'
        }
        
        # キャッシュの構築
        self._build_caches()
    
    def _build_caches(self):
        """モジュールとシンボルのキャッシュを構築"""
        print("📊 プロジェクト構造を分析中...")
        
        for py_file in self.src_root.rglob("*.py"):
            if '__pycache__' in str(py_file):
                continue
                
            # モジュールパスをキャッシュ
            module_path = self._path_to_module(py_file)
            self.module_cache[module_path] = py_file
            
            # ファイル内のシンボルをキャッシュ
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                        symbol_name = node.name
                        if symbol_name not in self.symbol_cache:
                            self.symbol_cache[symbol_name] = set()
                        self.symbol_cache[symbol_name].add(py_file)
                        
            except Exception:
                pass
    
    def check_and_fix_imports(self, dry_run: bool = True) -> CheckResult:
        """すべてのPythonファイルのインポートをチェックして修正"""
        print("🔍 インポートをチェック中...")
        
        # 修正マップをクリア
        self._fix_map.clear()
        self.unresolved_imports = []  # 解決できなかったインポートを記録
        
        all_failures: List[FailureLocation] = []
        files_fixed = 0
        
        for py_file in self.src_root.rglob("*.py"):
            if '__pycache__' in str(py_file):
                continue
                
            failures = self._check_file_imports(py_file)
            if failures:
                all_failures.extend(failures)
                
                if not dry_run:
                    if self._fix_file_imports(py_file, failures):
                        files_fixed += 1
        
        # 解決できなかったインポートの詳細を作成
        unresolved_details = self._create_unresolved_details()
        
        if dry_run:
            return CheckResult(
                title="comprehensive_import_check",
                failure_locations=all_failures,
                fix_policy=f"{len(all_failures)}個の壊れたインポートを検出しました",
                fix_example_code=unresolved_details if self.unresolved_imports else None
            )
        else:
            return CheckResult(
                title="comprehensive_import_fix",
                failure_locations=[],
                fix_policy=f"{files_fixed}個のファイルで{len(all_failures)}個のインポートを修正しました",
                fix_example_code=unresolved_details if self.unresolved_imports else None
            )
    
    def _check_file_imports(self, file_path: Path) -> List[FailureLocation]:
        """ファイル内のインポートをチェック"""
        failures = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            imports = self._extract_imports(tree)
            
            for import_info in imports:
                # 内部モジュールのインポートのみチェック
                if import_info.module and not self._is_internal_import(import_info.module):
                    continue
                    
                # インポートが解決可能かチェック
                correct_module = self._resolve_import(import_info, file_path)
                
                if correct_module and correct_module != import_info.module:
                    failures.append(FailureLocation(
                        file_path=str(file_path),
                        line_number=import_info.line_number
                    ))
                    # 修正情報を別途保存
                    key = f"{file_path}:{import_info.line_number}"
                    self._fix_map[key] = (import_info.module, correct_module)
                elif correct_module is None and import_info.module:
                    # 解決できない場合
                    failures.append(FailureLocation(
                        file_path=str(file_path),
                        line_number=import_info.line_number
                    ))
                    # 解決できなかったインポートを記録
                    self.unresolved_imports.append({
                        'file': str(file_path),
                        'line': import_info.line_number,
                        'module': import_info.module,
                        'type': 'missing' if import_info.module.startswith('src.') else 'unknown'
                    })
                    
        except Exception as e:
            print(f"  ⚠️  {file_path} の解析エラー: {e}")
            
        return failures
    
    def _fix_file_imports(self, file_path: Path, failures: List[FailureLocation]) -> bool:
        """ファイル内のインポートを修正"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            modified = False
            
            # 修正マップから情報を取得
            for failure in failures:
                if failure.file_path == str(file_path):
                    key = f"{file_path}:{failure.line_number}"
                    if hasattr(self, '_fix_map') and key in self._fix_map:
                        old_module, new_module = self._fix_map[key]
                        line_idx = failure.line_number - 1
                        
                        if 0 <= line_idx < len(lines):
                            old_line = lines[line_idx]
                            
                            new_line = old_line.replace(f'from {old_module}', f'from {new_module}')
                            
                            if old_line != new_line:
                                lines[line_idx] = new_line
                                modified = True
            
            if modified:
                # 空行と重複インポートを削除
                cleaned_lines = []
                seen_imports = set()
                import_section_ended = False
                
                for i, line in enumerate(lines):
                    # 空行は削除（インポートセクション内のみ）
                    if line.strip() == '':
                        if not import_section_ended:
                            continue
                    
                    # インポート行でない場合、インポートセクション終了
                    if line.strip() and not line.strip().startswith(('import ', 'from ')):
                        import_section_ended = True
                    
                    # インポート行の重複チェック
                    if line.strip().startswith(('import ', 'from ')):
                        # インポート内容を抽出
                        import_content = line.strip()
                        
                        if import_content in seen_imports:
                            continue  # 重複は削除
                        seen_imports.add(import_content)
                    
                    cleaned_lines.append(line)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(cleaned_lines)
                print(f"  ✅ 修正: {file_path.relative_to(self.project_root)}")
                return True
                
        except Exception as e:
            print(f"  ❌ 修正エラー: {file_path} - {e}")
            
        return False
    
    def _extract_imports(self, tree: ast.AST) -> List[ImportInfo]:
        """ASTからインポート情報を抽出"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        line_number=node.lineno,
                        module=alias.name,
                        names=[],
                        is_from_import=False
                    ))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(ImportInfo(
                        line_number=node.lineno,
                        module=node.module,
                        names=[alias.name for alias in node.names],
                        is_from_import=True,
                        level=node.level
                    ))
                    
        return imports
    
    def _is_internal_import(self, module: Optional[str]) -> bool:
        """内部モジュールのインポートかチェック"""
        if not module:
            return False
        
        # 標準ライブラリのモジュール（一部）
        stdlib_modules = {
            'os', 'sys', 're', 'json', 'csv', 'contextlib', 'collections',
            'itertools', 'functools', 'pathlib', 'datetime', 'time', 'math',
            'random', 'string', 'typing', 'types', 'ast', 'inspect', 'io',
            'shutil', 'tempfile', 'subprocess', 'threading', 'multiprocessing',
            'urllib', 'http', 'email', 'html', 'xml', 'sqlite3', 'logging',
            'argparse', 'configparser', 'hashlib', 'uuid', 'copy', 'dataclasses',
            'enum', 'abc', 'warnings', 'traceback', 'importlib', 'pkgutil',
            'unittest', 'doctest', 'pdb', 'profile', 'timeit', 'dis', 'pickle',
            'glob', 'difflib', 'queue', 'shlex', 'struct', 'array', 'weakref',
            'gc', 'signal', 'atexit', 'builtins', 'errno', 'fcntl', 'resource'
        }
        
        # 外部ライブラリのモジュール（一般的なもの）
        external_modules = {
            'numpy', 'pandas', 'matplotlib', 'scipy', 'sklearn', 'torch',
            'tensorflow', 'keras', 'flask', 'django', 'fastapi', 'requests',
            'beautifulsoup4', 'selenium', 'pytest', 'tox', 'setuptools',
            'pip', 'wheel', 'virtualenv', 'jupyter', 'notebook', 'ipython'
        }
        
        # モジュールのトップレベルパッケージを取得
        top_level = module.split('.')[0]
        
        # 標準ライブラリまたは外部ライブラリの場合はFalse
        if top_level in stdlib_modules or top_level in external_modules:
            return False
            
        # 既知の内部モジュール接頭辞で始まるかチェック
        return any(module.startswith(prefix) for prefix in self.internal_prefixes)
    
    def _resolve_import(self, import_info: ImportInfo, from_file: Path) -> Optional[str]:
        """インポートを解決して正しいモジュールパスを返す"""
        module = import_info.module
        
        # 既にsrc.で始まっている場合はそのままチェック
        if module.startswith('src.'):
            if self._validate_module_exists(module):
                return module
            # src.を除いて再チェック
            module = module[4:]
        
        # 各種パターンを試す
        candidates = []
        
        # 1. src.を付けてみる
        src_module = f"src.{module}"
        if self._validate_module_exists(src_module):
            candidates.append(src_module)
        
        # 2. シンボル名から検索（from importの場合）
        if import_info.is_from_import and import_info.names:
            for name in import_info.names:
                if name in self.symbol_cache:
                    for path in self.symbol_cache[name]:
                        module_path = self._path_to_module(path)
                        if module_path:
                            candidates.append(module_path)
        
        # 3. モジュール名の一部から検索
        module_parts = module.split('.')
        if module_parts:
            # 最後の部分でファイル名を検索
            last_part = module_parts[-1]
            for cached_module, path in self.module_cache.items():
                if path.stem == last_part or last_part in cached_module:
                    candidates.append(cached_module)
        
        # 4. パスパターンマッチング
        # infrastructure.drivers.logging.format_info -> utils/format_info.py のようなケース
        if len(module_parts) > 2:
            # 最後の2つの部分で検索
            search_pattern = f"*{module_parts[-2]}*{module_parts[-1]}.py"
            for path in self.src_root.rglob(search_pattern):
                if '__pycache__' not in str(path):
                    module_path = self._path_to_module(path)
                    if module_path:
                        candidates.append(module_path)
        
        # 候補から最適なものを選択
        if candidates:
            # 元のモジュール名との類似度で並べ替え
            candidates = list(set(candidates))
            candidates.sort(key=lambda c: self._calculate_similarity(module, c), reverse=True)
            return candidates[0]
        
        return None
    
    def _validate_module_exists(self, module_path: str) -> bool:
        """モジュールパスが実在するかチェック"""
        return module_path in self.module_cache
    
    def _path_to_module(self, path: Path) -> str:
        """ファイルパスをモジュールパスに変換"""
        try:
            if path.suffix == '.py':
                path = path.with_suffix('')
            
            relative_path = path.relative_to(self.project_root)
            return str(relative_path).replace('/', '.')
        except ValueError:
            return ""
    
    def _calculate_similarity(self, original: str, candidate: str) -> float:
        """2つのモジュールパスの類似度を計算"""
        original_parts = set(original.split('.'))
        candidate_parts = set(candidate.split('.'))
        
        # 共通部分の割合
        common = original_parts.intersection(candidate_parts)
        if not original_parts:
            return 0.0
            
        return len(common) / len(original_parts)
    
    def _create_unresolved_details(self) -> Optional[str]:
        """解決できなかったインポートの詳細を作成"""
        if not self.unresolved_imports:
            return None
        
        details = ["解決できなかったインポート:"]
        details.append("-" * 60)
        
        # タイプ別に分類
        missing_modules = [imp for imp in self.unresolved_imports if imp['type'] == 'missing']
        unknown_modules = [imp for imp in self.unresolved_imports if imp['type'] == 'unknown']
        
        if missing_modules:
            details.append("\n削除されたモジュール:")
            for imp in missing_modules:
                details.append(f"  {imp['file']}:{imp['line']} - {imp['module']}")
        
        if unknown_modules:
            details.append("\n不明なモジュール:")
            for imp in unknown_modules:
                details.append(f"  {imp['file']}:{imp['line']} - {imp['module']}")
        
        details.append("\n対応方法:")
        details.append("  - 削除されたモジュール: コードを更新して別のモジュールを使用するか、機能を再実装してください")
        details.append("  - 不明なモジュール: 外部ライブラリの場合はインストールが必要です")
        
        return "\n".join(details)


def main() -> CheckResult:
    """メインエントリポイント"""
    project_root = Path(__file__).parent.parent
    fixer = ComprehensiveImportFixer(project_root)
    
    # まずチェックを実行
    check_result = fixer.check_and_fix_imports(dry_run=True)
    
    if check_result.failure_locations:
        print(f"\n⚠️  {len(check_result.failure_locations)}個の壊れたインポートを検出しました")
        print("\n修正を実行中...")
        
        # 修正を実行
        fix_result = fixer.check_and_fix_imports(dry_run=False)
        
        # 再チェック
        final_check = fixer.check_and_fix_imports(dry_run=True)
        if final_check.failure_locations:
            print(f"\n⚠️  まだ{len(final_check.failure_locations)}個のインポートが解決できません")
            return final_check
        else:
            print("\n✅ すべてのインポートを修正しました")
            return fix_result
    else:
        print("\n✅ すべてのインポートは正常です")
        return check_result


if __name__ == "__main__":
    result = main()
    print(f"\n結果: {result.fix_policy}")