"""
第3版インポート文更新器
相対インポートを正しく絶対インポートに変換し、移動後のモジュール名にマッピング
"""

import ast
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

class ImportUpdaterV3:
    """
    最終版インポート更新器
    相対インポートの解決と移動後のパスマッピングを正確に実装
    """
    
    def __init__(self, src_root: Path):
        self.src_root = src_root
        self.move_plan: Dict[Path, Path] = {}
        self.module_mapping: Dict[str, str] = {}  # 元のモジュール名 -> 新しいモジュール名
        
    def set_move_plan(self, move_plan: Dict[Path, Path]) -> None:
        """移動計画を設定し、モジュールマッピングを構築"""
        self.move_plan = move_plan
        self.module_mapping = {}
        
        # すべてのモジュールの新旧マッピングを作成
        for old_path, new_path in move_plan.items():
            old_module = self._path_to_module(old_path)
            new_module = self._path_to_module(new_path)
            self.module_mapping[old_module] = new_module
            
        print(f"移動計画を設定: {len(move_plan)}ファイル")
        print("モジュールマッピング:")
        for old, new in self.module_mapping.items():
            print(f"  {old} -> {new}")
    
    def _path_to_module(self, path: Path) -> str:
        """ファイルパスをモジュール名に変換"""
        try:
            rel_path = path.relative_to(self.src_root)
            parts = list(rel_path.parts)
            
            if parts[-1] == '__init__.py':
                parts = parts[:-1]
            elif parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]
            
            return '.'.join(parts)
        except ValueError:
            return ''
    
    def update_file_imports(self, file_path: Path) -> Tuple[bool, str]:
        """
        ファイル内のインポートを更新
        Returns: (変更があったか, 新しい内容)
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # 現在のファイルの元のモジュール名を取得
            current_module = self._path_to_module(file_path)
            
            # ASTで解析
            tree = ast.parse(content)
            
            # インポート文を更新
            updater = ImportStatementUpdater(
                self.module_mapping,
                current_module,
                self.src_root
            )
            new_tree = updater.visit(tree)
            
            if updater.modified:
                # 更新されたASTからソースコードを生成
                new_content = ast.unparse(new_tree)
                return True, new_content
            else:
                return False, content
                
        except Exception as e:
            print(f"エラー ({file_path}): {e}")
            return False, content
    
    def update_all_files(self, dry_run: bool = True) -> Dict[Path, str]:
        """すべてのファイルのインポートを更新"""
        changes = {}
        all_files = list(self.src_root.rglob("*.py"))
        
        print(f"\n📝 {len(all_files)}ファイルのインポートを更新中...")
        
        for file_path in all_files:
            modified, new_content = self.update_file_imports(file_path)
            
            if modified:
                changes[file_path] = new_content
                if not dry_run:
                    file_path.write_text(new_content, encoding='utf-8')
        
        print(f"✅ {len(changes)}ファイルが更新{'予定' if dry_run else '完了'}")
        return changes


class ImportStatementUpdater(ast.NodeTransformer):
    """ASTを走査してインポート文を更新"""
    
    def __init__(self, module_mapping: Dict[str, str], current_module: str, src_root: Path):
        self.module_mapping = module_mapping
        self.current_module = current_module
        self.src_root = src_root
        self.modified = False
        
    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        """from ... import文を処理"""
        # 相対インポートの場合
        if node.level > 0:
            # 相対インポートを絶対インポートに変換
            absolute_module = self._resolve_relative_import(
                self.current_module,
                node.level,
                node.module
            )
            
            # from . import something の場合、正しく処理
            if not node.module and absolute_module:
                # インポート対象を個別に処理する必要がある
                # この場合は元の相対インポート形式を保持
                return node
            
            # 変換されたモジュールが移動対象かチェック
            new_module = self._map_module(absolute_module) if absolute_module else ''
            
            if new_module and new_module != absolute_module:
                # 絶対インポートに変換
                node.level = 0
                node.module = new_module
                self.modified = True
            elif absolute_module:
                # 移動対象でない場合も絶対インポートに変換
                node.level = 0
                node.module = absolute_module
                self.modified = True
        
        # 絶対インポートの場合
        elif node.module:
            new_module = self._map_module(node.module)
            if new_module != node.module:
                node.module = new_module
                self.modified = True
        
        return node
    
    def visit_Import(self, node: ast.Import) -> ast.Import:
        """import文を処理"""
        for alias in node.names:
            new_name = self._map_module(alias.name)
            if new_name != alias.name:
                alias.name = new_name
                self.modified = True
        
        return node
    
    def _resolve_relative_import(self, current_module: str, level: int, module: Optional[str]) -> str:
        """相対インポートを絶対インポートに解決"""
        # 現在のモジュールのパーツ
        parts = current_module.split('.')
        
        # ファイルモジュールの場合、最後の部分（ファイル名）を除去
        if parts:
            parts = parts[:-1]
        
        # レベル分だけ上に移動（level-1回上に移動）
        for _ in range(level - 1):
            if parts:
                parts = parts[:-1]
        
        # モジュール名を追加
        if module:
            parts.append(module)
        
        return '.'.join(parts) if parts else module or ''
    
    def _map_module(self, module_name: str) -> str:
        """モジュール名を新しい名前にマッピング"""
        # 完全一致を確認
        if module_name in self.module_mapping:
            return self.module_mapping[module_name]
        
        # 部分一致を確認（サブモジュール）
        for old_module, new_module in self.module_mapping.items():
            if module_name.startswith(old_module + '.'):
                # サブモジュール部分を保持
                suffix = module_name[len(old_module):]
                return new_module + suffix
        
        return module_name


def test_import_updater_v3():
    """第3版インポート更新器のテスト"""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        # テストファイル作成
        (src_dir / "__init__.py").write_text("")
        
        (src_dir / "constants.py").write_text("""
API_VERSION = "1.0"
""")
        
        (src_dir / "logger.py").write_text("""
from .constants import API_VERSION

class Logger:
    version = API_VERSION
""")
        
        (src_dir / "database.py").write_text("""
from .logger import Logger
from src_check.processors.auto_correct.import_dependency_reorganizer import constants

class Database:
    def __init__(self):
        self.logger = Logger()
        self.version = constants.API_VERSION
""")
        
        # 移動計画
        move_plan = {
            src_dir / "logger.py": src_dir / "core" / "logger" / "logger.py",
            src_dir / "database.py": src_dir / "services" / "db" / "database.py"
        }
        
        # テスト実行
        updater = ImportUpdaterV3(src_dir)
        updater.set_move_plan(move_plan)
        
        # 更新内容を確認
        changes = updater.update_all_files(dry_run=True)
        
        print("\n更新結果:")
        for file_path, new_content in changes.items():
            print(f"\n=== {file_path.name} ===")
            print(new_content)


if __name__ == "__main__":
    test_import_updater_v3()