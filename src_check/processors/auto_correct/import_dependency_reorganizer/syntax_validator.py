"""
構文検証器
移動後のPythonファイルの構文チェックとインポート検証
"""

import ast
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional

class SyntaxValidator:
    """
    Pythonファイルの構文検証とインポート可能性チェック
    """
    
    def __init__(self, src_root: Path):
        self.src_root = src_root
        self.errors: List[Dict] = []
        
    def validate_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        単一ファイルの構文を検証
        Returns: (成功フラグ, エラーメッセージ)
        """
        try:
            # ファイルを読み込み
            content = file_path.read_text(encoding='utf-8')
            
            # AST解析で構文チェック
            ast.parse(content, filename=str(file_path))
            
            # pyflakes/pylintなどの詳細チェック（オプション）
            if self._has_pyflakes():
                return self._validate_with_pyflakes(file_path)
            
            return True, None
            
        except SyntaxError as e:
            error_msg = f"構文エラー: {e.msg} (行{e.lineno})"
            return False, error_msg
        except Exception as e:
            return False, str(e)
    
    def validate_all_files(self, file_paths: Optional[List[Path]] = None) -> Dict[Path, str]:
        """
        複数ファイルの構文を検証
        Returns: エラーがあったファイルとエラーメッセージのマップ
        """
        if file_paths is None:
            file_paths = list(self.src_root.rglob("*.py"))
        
        errors = {}
        validated_count = 0
        
        print(f"📝 {len(file_paths)}ファイルの構文を検証中...")
        
        for file_path in file_paths:
            success, error_msg = self.validate_file(file_path)
            
            if not success:
                errors[file_path] = error_msg
            
            validated_count += 1
            if validated_count % 20 == 0:
                print(f"  ✓ {validated_count}ファイル検証済み...")
        
        if errors:
            print(f"\n❌ 構文エラー: {len(errors)}ファイル")
            for file_path, error in list(errors.items())[:5]:
                rel_path = file_path.relative_to(self.src_root)
                print(f"  - {rel_path}: {error}")
        else:
            print(f"\n✅ すべてのファイルの構文が正常です")
        
        return errors
    
    def validate_imports(self, file_path: Path) -> List[str]:
        """
        ファイルのインポートが解決可能かチェック
        Returns: 解決できないインポートのリスト
        """
        unresolved_imports = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content, filename=str(file_path))
            
            # インポート文を抽出
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not self._can_import(alias.name, file_path):
                            unresolved_imports.append(alias.name)
                            
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    if node.level > 0:
                        # 相対インポートの解決
                        base_path = file_path.parent
                        for _ in range(node.level - 1):
                            base_path = base_path.parent
                        
                        if module:
                            full_module = self._resolve_relative_import(base_path, module)
                        else:
                            full_module = self._path_to_module_name(base_path)
                    else:
                        full_module = module
                    
                    if not self._can_import(full_module, file_path):
                        unresolved_imports.append(f"from {module or '.'} (level={node.level})")
        
        except Exception as e:
            unresolved_imports.append(f"解析エラー: {str(e)}")
        
        return unresolved_imports
    
    def _can_import(self, module_name: str, from_file: Path) -> bool:
        """モジュールがインポート可能かチェック"""
        # 組み込みモジュールや標準ライブラリ
        if module_name in sys.builtin_module_names:
            return True
        
        # サードパーティモジュール（簡易チェック）
        parts = module_name.split('.')
        if parts[0] not in ['src', 'test_src', self.src_root.name]:
            # 実際にインポートを試みる
            try:
                __import__(module_name)
                return True
            except ImportError:
                pass
        
        # ローカルモジュール
        module_path = self._module_name_to_path(module_name)
        return module_path is not None
    
    def _module_name_to_path(self, module_name: str) -> Optional[Path]:
        """モジュール名から実際のファイルパスを解決"""
        parts = module_name.split('.')
        
        # プロジェクト内のモジュール
        path = self.src_root
        for part in parts:
            path = path / part
            
        # ファイルとして存在
        py_file = path.with_suffix('.py')
        if py_file.exists():
            return py_file
        
        # パッケージとして存在
        init_file = path / '__init__.py'
        if init_file.exists():
            return init_file
        
        return None
    
    def _path_to_module_name(self, path: Path) -> str:
        """パスをモジュール名に変換"""
        try:
            rel_path = path.relative_to(self.src_root)
            parts = list(rel_path.parts)
            if parts and parts[-1] == '__init__.py':
                parts = parts[:-1]
            elif parts and parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]
            return '.'.join(parts)
        except:
            return ''
    
    def _resolve_relative_import(self, base_path: Path, module: str) -> str:
        """相対インポートを絶対インポートに解決"""
        base_module = self._path_to_module_name(base_path)
        if base_module and module:
            return f"{base_module}.{module}"
        return base_module or module
    
    def _has_pyflakes(self) -> bool:
        """pyflakesがインストールされているかチェック"""
        try:
            subprocess.run(["pyflakes", "--version"], 
                         capture_output=True, check=True)
            return True
        except:
            return False
    
    def _validate_with_pyflakes(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """pyflakesを使用した詳細な検証"""
        try:
            result = subprocess.run(
                ["pyflakes", str(file_path)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, None
            else:
                # pyflakesの出力から最初のエラーを抽出
                error_lines = result.stdout.strip().split('\n')
                if error_lines and error_lines[0]:
                    return False, error_lines[0]
                return True, None
        except Exception as e:
            # pyflakesが失敗した場合は基本的な検証に戻る
            return True, None
    
    def check_circular_imports(self, file_paths: Optional[List[Path]] = None) -> List[List[str]]:
        """
        循環インポートをチェック
        Returns: 循環インポートのリスト
        """
        if file_paths is None:
            file_paths = list(self.src_root.rglob("*.py"))
        
        # 簡易的な循環インポートチェック
        # より詳細なチェックは dependency_calculator.py で実施
        cycles = []
        
        # インポートグラフを構築
        import_graph = {}
        for file_path in file_paths:
            module_name = self._path_to_module_name(file_path)
            imports = self._get_imports_from_file(file_path)
            import_graph[module_name] = imports
        
        # DFSで循環を検出（簡易版）
        visited = set()
        rec_stack = set()
        
        def dfs(module: str, path: List[str]) -> None:
            if module in rec_stack:
                cycle_start = path.index(module)
                cycle = path[cycle_start:] + [module]
                cycles.append(cycle)
                return
            
            if module in visited:
                return
            
            visited.add(module)
            rec_stack.add(module)
            
            for imported in import_graph.get(module, []):
                dfs(imported, path + [imported])
            
            rec_stack.remove(module)
        
        for module in import_graph:
            if module not in visited:
                dfs(module, [module])
        
        return cycles
    
    def _get_imports_from_file(self, file_path: Path) -> List[str]:
        """ファイルからインポートされているモジュールを抽出"""
        imports = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except:
            pass
        
        return imports


def test_syntax_validator():
    """構文検証器のテスト"""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        # 正常なファイル
        (src_dir / "valid.py").write_text("""
def hello():
    return "Hello, World!"
""")
        
        # 構文エラーのあるファイル
        (src_dir / "invalid.py").write_text("""
def broken(:
    return "Broken"
""")
        
        # インポートエラーのあるファイル
        (src_dir / "import_error.py").write_text("""
from non_existent_module import something

def use_something():
    return something()
""")
        
        # 検証を実行
        validator = SyntaxValidator(src_dir)
        
        print("構文検証テスト:")
        
        # 個別ファイルの検証
        success, error = validator.validate_file(src_dir / "valid.py")
        print(f"valid.py: {'成功' if success else f'失敗 - {error}'}")
        
        success, error = validator.validate_file(src_dir / "invalid.py")
        print(f"invalid.py: {'成功' if success else f'失敗 - {error}'}")
        
        # 全ファイルの検証
        errors = validator.validate_all_files()
        print(f"\n全体検証: {len(errors)}個のエラー")


if __name__ == "__main__":
    test_syntax_validator()