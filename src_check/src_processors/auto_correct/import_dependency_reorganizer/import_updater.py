"""
インポート文更新器
ファイル移動に伴うインポートパスの自動更新機能
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

class ImportUpdater:
    """
    ASTベースのインポート文更新器
    ファイル移動後のインポートパスを自動的に修正
    """
    
    def __init__(self, src_root: Path):
        self.src_root = src_root
        self.move_plan: Dict[Path, Path] = {}  # old_path -> new_path
        self.module_name_changes: Dict[str, str] = {}  # old_module -> new_module
        
    def set_move_plan(self, move_plan: Dict[Path, Path]) -> None:
        """移動計画を設定し、モジュール名の変更マップを生成"""
        self.move_plan = move_plan
        
        # モジュール名の変更マップを作成
        for old_path, new_path in move_plan.items():
            old_module = self._path_to_module_name(old_path)
            new_module = self._path_to_module_name(new_path)
            self.module_name_changes[old_module] = new_module
            
        print(f"移動計画を設定: {len(move_plan)}ファイル")
        
    def _path_to_module_name(self, file_path: Path) -> str:
        """ファイルパスをモジュール名に変換"""
        try:
            relative_path = file_path.relative_to(self.src_root)
            parts = list(relative_path.parts)
            
            # .pyファイルの場合は拡張子を除去
            if parts[-1].endswith('.py'):
                if parts[-1] == '__init__.py':
                    parts = parts[:-1]
                else:
                    parts[-1] = parts[-1][:-3]
            
            return '.'.join(parts) if parts else ''
        except ValueError:
            # src_root外のファイルの場合
            return str(file_path)
    
    def update_imports_in_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        指定ファイル内のインポート文を更新
        Returns: (成功フラグ, 更新後の内容 or エラーメッセージ)
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content, filename=str(file_path))
            
            # インポート文を更新
            transformer = ImportTransformer(self.module_name_changes, self._path_to_module_name(file_path))
            new_tree = transformer.visit(tree)
            
            # 更新があった場合のみ新しいコードを生成
            if transformer.modified:
                # ASTからコードを生成（ast.unparseはPython 3.9+）
                try:
                    new_content = ast.unparse(new_tree)
                except AttributeError:
                    # Python 3.8以下の場合は正規表現で置換
                    new_content = self._update_imports_with_regex(content, transformer.replacements)
                
                return True, new_content
            else:
                return True, content  # 変更なし
                
        except Exception as e:
            return False, f"エラー: {str(e)}"
    
    def _update_imports_with_regex(self, content: str, replacements: List[Tuple[str, str]]) -> str:
        """正規表現を使用してインポート文を更新（Python 3.8以下用）"""
        for old_import, new_import in replacements:
            # from ... import ...形式
            pattern1 = rf"from\s+{re.escape(old_import)}\s+import"
            content = re.sub(pattern1, f"from {new_import} import", content)
            
            # import ...形式
            pattern2 = rf"import\s+{re.escape(old_import)}(?:\s|$|,)"
            content = re.sub(pattern2, f"import {new_import}", content)
            
        return content
    
    def update_all_imports(self, dry_run: bool = True) -> Dict[Path, str]:
        """
        すべてのファイルのインポートを更新
        dry_run=Trueの場合は実際の変更は行わず、変更内容を返す
        """
        changes = {}
        
        # すべてのPythonファイルを処理
        for py_file in self.src_root.rglob("*.py"):
            success, result = self.update_imports_in_file(py_file)
            
            if success:
                original_content = py_file.read_text(encoding='utf-8')
                if result != original_content:
                    changes[py_file] = result
                    
                    if not dry_run:
                        py_file.write_text(result, encoding='utf-8')
            else:
                print(f"⚠️  {py_file}: {result}")
        
        return changes
    
    def validate_imports(self, file_path: Path, content: str) -> List[str]:
        """更新後のインポートが有効かどうかを検証"""
        errors = []
        
        try:
            tree = ast.parse(content, filename=str(file_path))
            
            # すべてのインポート文を抽出
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        # モジュールが存在するかチェック（簡易版）
                        if not self._module_exists(module_name):
                            errors.append(f"モジュール '{module_name}' が見つかりません")
                            
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    if not self._module_exists(module):
                        errors.append(f"モジュール '{module}' が見つかりません")
                        
        except SyntaxError as e:
            errors.append(f"構文エラー: {e}")
            
        return errors
    
    def _module_exists(self, module_name: str) -> bool:
        """モジュールが存在するかチェック（簡易版）"""
        if not module_name:
            return True
            
        # 標準ライブラリやサードパーティのモジュールは存在すると仮定
        if not module_name.startswith('.'):
            parts = module_name.split('.')
            if parts[0] not in ['src', 'test_src']:  # プロジェクト固有のルート
                return True
        
        # ローカルモジュールの場合はファイルが存在するかチェック
        module_path = self.src_root / module_name.replace('.', '/') 
        
        # ディレクトリ（__init__.py）またはファイル（.py）として存在するかチェック
        return (module_path.is_dir() and (module_path / '__init__.py').exists()) or \
               (module_path.with_suffix('.py')).exists()


class ImportTransformer(ast.NodeTransformer):
    """ASTノードトランスフォーマー：インポート文を更新"""
    
    def __init__(self, module_name_changes: Dict[str, str], current_module: str):
        self.module_name_changes = module_name_changes
        self.current_module = current_module
        self.modified = False
        self.replacements = []  # 正規表現置換用
    
    def visit_Import(self, node: ast.Import) -> ast.Import:
        """import文を処理"""
        new_names = []
        
        for alias in node.names:
            old_name = alias.name
            new_name = self._get_new_module_name(old_name)
            
            if new_name != old_name:
                self.modified = True
                self.replacements.append((old_name, new_name))
                new_alias = ast.alias(name=new_name, asname=alias.asname)
            else:
                new_alias = alias
                
            new_names.append(new_alias)
        
        node.names = new_names
        return node
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        """from ... import文を処理"""
        if node.module:
            old_module = node.module
            new_module = self._get_new_module_name(old_module)
            
            if new_module != old_module:
                self.modified = True
                self.replacements.append((old_module, new_module))
                node.module = new_module
        
        # 相対インポートの場合は特別な処理が必要
        elif node.level > 0:
            # 相対インポートを絶対インポートに変換する場合の処理
            # （必要に応じて実装）
            pass
        
        return node
    
    def _get_new_module_name(self, old_module: str) -> str:
        """古いモジュール名から新しいモジュール名を取得"""
        # 完全一致を優先
        if old_module in self.module_name_changes:
            return self.module_name_changes[old_module]
        
        # 部分一致をチェック（サブモジュールの場合）
        for old, new in self.module_name_changes.items():
            if old_module.startswith(old + '.'):
                # サブモジュールパスを更新
                suffix = old_module[len(old):]
                return new + suffix
        
        return old_module


def test_import_updater():
    """インポート更新器のテスト"""
    import tempfile
    import shutil
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        # テストファイルを作成
        (src_dir / "old_module.py").write_text("""
def old_function():
    return "old"
""")
        
        (src_dir / "user_module.py").write_text("""
from .old_module import old_function
import old_module

def use_old():
    return old_function()
""")
        
        # インポート更新器を設定
        updater = ImportUpdater(src_dir)
        move_plan = {
            src_dir / "old_module.py": src_dir / "new_location" / "new_module.py"
        }
        updater.set_move_plan(move_plan)
        
        # インポートを更新
        success, new_content = updater.update_imports_in_file(src_dir / "user_module.py")
        
        print("テスト結果:")
        print(f"成功: {success}")
        print(f"更新後のコンテンツ:\n{new_content}")
        
        # 期待される変更を確認
        assert "from .new_location.new_module import" in new_content or \
               "from new_location.new_module import" in new_content
        assert "import new_location.new_module" in new_content


if __name__ == "__main__":
    test_import_updater()