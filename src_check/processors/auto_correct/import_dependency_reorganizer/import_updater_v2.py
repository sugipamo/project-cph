"""
改良版インポート文更新器
相対インポートを適切に処理し、ファイル移動後も正しく動作するように更新
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

class ImportUpdaterV2:
    """
    改良版インポート更新器
    相対インポートの正確な変換と移動後のパス解決を実装
    """
    
    def __init__(self, src_root: Path):
        self.src_root = src_root
        self.move_plan: Dict[Path, Path] = {}
        self.module_mapping: Dict[str, str] = {}  # old_module -> new_module
        
    def set_move_plan(self, move_plan: Dict[Path, Path]) -> None:
        """移動計画を設定"""
        self.move_plan = move_plan
        
        # モジュール名のマッピングを生成
        self.module_mapping = {}
        for old_path, new_path in move_plan.items():
            old_module = self._path_to_module(old_path)
            new_module = self._path_to_module(new_path)
            self.module_mapping[old_module] = new_module
        
        print(f"移動計画を設定: {len(move_plan)}ファイル")
    
    def _path_to_module(self, path: Path) -> str:
        """パスをモジュール名に変換"""
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
            lines = content.splitlines(keepends=True)
            
            # 現在のファイルの新しい場所を取得
            if file_path in self.move_plan:
                new_file_path = self.move_plan[file_path]
            else:
                new_file_path = file_path
            
            new_module = self._path_to_module(new_file_path)
            
            # ASTで解析
            tree = ast.parse(content)
            modified = False
            
            # インポート文の行番号と新しい内容を記録
            import_changes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    # 相対インポートの処理
                    if node.level > 0:
                        # 相対インポートを絶対インポートに変換
                        absolute_module = self._resolve_relative_import(
                            new_file_path, node.level, node.module
                        )
                        
                        if absolute_module:
                            # 移動したモジュールかチェック
                            final_module = self._get_new_module_name(absolute_module)
                            
                            # 新しいインポート文を生成
                            imported_names = [alias.name for alias in node.names]
                            asnames = [alias.asname for alias in node.names]
                            
                            new_import = self._create_import_statement(
                                final_module, imported_names, asnames
                            )
                            
                            import_changes.append((node.lineno - 1, new_import))
                            modified = True
                    
                    # 絶対インポートの処理
                    elif node.module:
                        new_module_name = self._get_new_module_name(node.module)
                        if new_module_name != node.module:
                            imported_names = [alias.name for alias in node.names]
                            asnames = [alias.asname for alias in node.names]
                            
                            new_import = self._create_import_statement(
                                new_module_name, imported_names, asnames
                            )
                            
                            import_changes.append((node.lineno - 1, new_import))
                            modified = True
                
                elif isinstance(node, ast.Import):
                    # import文の処理
                    for alias in node.names:
                        new_name = self._get_new_module_name(alias.name)
                        if new_name != alias.name:
                            new_import = f"import {new_name}"
                            if alias.asname:
                                new_import += f" as {alias.asname}"
                            new_import += "\n"
                            
                            import_changes.append((node.lineno - 1, new_import))
                            modified = True
            
            # 変更を適用
            if modified:
                # 行番号の大きい順にソート（後ろから変更）
                import_changes.sort(key=lambda x: x[0], reverse=True)
                
                for line_no, new_import in import_changes:
                    if 0 <= line_no < len(lines):
                        lines[line_no] = new_import
                
                return True, ''.join(lines)
            else:
                return False, content
                
        except Exception as e:
            print(f"エラー: {file_path}: {e}")
            return False, file_path.read_text(encoding='utf-8')
    
    def _resolve_relative_import(self, file_path: Path, level: int, module: Optional[str]) -> str:
        """相対インポートを絶対インポートに解決"""
        # ファイルの親ディレクトリから開始
        current_path = file_path.parent
        
        # レベル分だけ上に移動
        for _ in range(level - 1):
            current_path = current_path.parent
        
        # 基準モジュールを取得
        base_module = self._path_to_module(current_path)
        
        # モジュール名を結合
        if module:
            if base_module:
                return f"{base_module}.{module}"
            else:
                return module
        else:
            return base_module
    
    def _get_new_module_name(self, module_name: str) -> str:
        """モジュール名を新しい名前に変換"""
        # 完全一致をチェック
        if module_name in self.module_mapping:
            return self.module_mapping[module_name]
        
        # 部分一致をチェック（サブモジュール）
        for old_module, new_module in self.module_mapping.items():
            if module_name.startswith(old_module + '.'):
                suffix = module_name[len(old_module):]
                return new_module + suffix
        
        return module_name
    
    def _create_import_statement(self, module: str, names: List[str], asnames: List[str]) -> str:
        """インポート文を生成"""
        import_parts = []
        
        for i, name in enumerate(names):
            if asnames[i]:
                import_parts.append(f"{name} as {asnames[i]}")
            else:
                import_parts.append(name)
        
        return f"from {module} import {', '.join(import_parts)}\n"
    
    def update_all_files(self, dry_run: bool = True) -> Dict[Path, str]:
        """
        すべてのファイルのインポートを更新
        Returns: 変更されたファイルと新しい内容のマップ
        """
        changes = {}
        
        # すべてのPythonファイルを処理
        all_files = list(self.src_root.rglob("*.py"))
        
        print(f"📝 {len(all_files)}ファイルのインポートを更新中...")
        
        for file_path in all_files:
            modified, new_content = self.update_file_imports(file_path)
            
            if modified:
                if dry_run:
                    changes[file_path] = new_content
                else:
                    file_path.write_text(new_content, encoding='utf-8')
                    changes[file_path] = new_content
        
        print(f"✅ {len(changes)}ファイルが更新{'予定' if dry_run else '完了'}")
        
        return changes


def test_import_updater_v2():
    """改良版インポート更新器のテスト"""
    import tempfile
    import shutil
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        # テストプロジェクトを作成
        (src_dir / "__init__.py").write_text("")
        
        (src_dir / "base.py").write_text("""
def base_function():
    return "base"
""")
        
        (src_dir / "middle.py").write_text("""
from .base import base_function

def middle_function():
    return base_function() + "_middle"
""")
        
        (src_dir / "top.py").write_text("""
from .middle import middle_function
from . import base

def top_function():
    return middle_function() + "_top"
""")
        
        # 移動計画
        move_plan = {
            src_dir / "base.py": src_dir / "core" / "base" / "base.py",
            src_dir / "middle.py": src_dir / "services" / "middle" / "middle.py",
            src_dir / "top.py": src_dir / "app" / "top" / "top.py"
        }
        
        # インポート更新器をテスト
        updater = ImportUpdaterV2(src_dir)
        updater.set_move_plan(move_plan)
        
        # ドライランで確認
        changes = updater.update_all_files(dry_run=True)
        
        print("\nテスト結果:")
        for file_path, new_content in changes.items():
            print(f"\n{file_path.name}:")
            print(new_content)


if __name__ == "__main__":
    test_import_updater_v2()