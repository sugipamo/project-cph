import ast
from pathlib import Path
from typing import Dict, List, Set, Optional
import time

class SimpleImportAnalyzer:
    """
    シンプルなインポート解析器
    既存コードに依存しない独立実装
    """
    
    def __init__(self, src_root: Path):
        self.src_root = src_root
        self.file_imports: Dict[Path, List[str]] = {}  # ファイル -> インポートモジュール一覧
        self.import_statements: Dict[Path, List[dict]] = {}  # 詳細情報
        self.parse_errors: List[str] = []
        
    def analyze_all_files(self) -> None:
        """すべてのPythonファイルを解析"""
        python_files = list(self.src_root.rglob("*.py"))
        
        print(f"解析対象ファイル: {len(python_files)}個")
        
        for i, py_file in enumerate(python_files):
            if i % 10 == 0 and i > 0:
                print(f"  進捗: {i}/{len(python_files)} ({i/len(python_files)*100:.1f}%)")
            
            try:
                self._analyze_single_file(py_file)
            except Exception as e:
                error_msg = f"解析エラー {py_file.relative_to(self.src_root)}: {e}"
                self.parse_errors.append(error_msg)
                print(f"  警告: {error_msg}")
                # エラーがあってもスキップして続行
                self.file_imports[py_file] = []
                self.import_statements[py_file] = []
        
        print(f"解析完了: {len(self.file_imports)}ファイル")
        if self.parse_errors:
            print(f"解析エラー: {len(self.parse_errors)}件")
    
    def _analyze_single_file(self, file_path: Path) -> None:
        """単一ファイルのインポート解析"""
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            raise Exception(f"構文エラー: {e}")
        
        imports = []
        detailed_imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    if self._is_project_module(module_name):
                        imports.append(module_name)
                        detailed_imports.append({
                            'type': 'import',
                            'module': module_name,
                            'line': node.lineno,
                            'alias': alias.asname
                        })
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module
                    # 相対インポートの処理
                    if node.level > 0:
                        module_name = self._resolve_relative_import(
                            node.module or '', node.level, file_path
                        )
                    
                    if module_name and self._is_project_module(module_name):
                        imports.append(module_name)
                        detailed_imports.append({
                            'type': 'from_import',
                            'module': module_name,
                            'line': node.lineno,
                            'names': [alias.name for alias in node.names],
                            'level': node.level
                        })
        
        self.file_imports[file_path] = imports
        self.import_statements[file_path] = detailed_imports
    
    def _is_project_module(self, module_name: str) -> bool:
        """プロジェクト内モジュールかどうか判定"""
        if not module_name:
            return False
        
        # src. で始まるもの、または相対パスで解決できるもの
        if module_name.startswith('src.'):
            return True
        
        # モジュール名からファイルパスを推測して存在確認
        return self._module_exists(module_name)
    
    def _module_exists(self, module_name: str) -> bool:
        """モジュールが実際に存在するかチェック"""
        # src.を除去
        if module_name.startswith('src.'):
            relative_module = module_name[4:]  # 'src.' を除去
        else:
            relative_module = module_name
        
        # パスに変換
        parts = relative_module.split('.')
        
        # ファイルとして存在するか
        file_path = self.src_root
        for part in parts[:-1]:
            file_path = file_path / part
        file_path = file_path / f"{parts[-1]}.py"
        
        if file_path.exists():
            return True
        
        # __init__.py として存在するか
        init_path = self.src_root
        for part in parts:
            init_path = init_path / part
        init_path = init_path / "__init__.py"
        
        return init_path.exists()
    
    def _resolve_relative_import(self, module: str, level: int, current_file: Path) -> str:
        """相対インポートを絶対パスに解決"""
        try:
            # 現在のファイルからの相対位置を計算
            current_module_path = current_file.relative_to(self.src_root).with_suffix('')
            current_parts = current_module_path.parts
            
            # level分だけ上位に移動
            if level >= len(current_parts):
                # 上位に移動しすぎる場合は空文字
                base_parts = []
            else:
                base_parts = current_parts[:-level] if level > 0 else current_parts
            
            # モジュール名を追加
            if module:
                final_parts = base_parts + tuple(module.split('.'))
            else:
                final_parts = base_parts
            
            # src.プレフィックスを追加
            if final_parts:
                return 'src.' + '.'.join(final_parts)
            else:
                return ''
                
        except Exception as e:
            print(f"相対インポート解決エラー: {e}")
            return ''
    
    def get_dependencies(self, file_path: Path) -> List[str]:
        """指定ファイルの依存モジュール一覧を取得"""
        return self.file_imports.get(file_path, [])
    
    def get_dependents(self, module_name: str) -> List[Path]:
        """指定モジュールに依存しているファイル一覧を取得"""
        dependents = []
        for file_path, imports in self.file_imports.items():
            if module_name in imports:
                dependents.append(file_path)
        return dependents
    
    def path_to_module_name(self, file_path: Path) -> str:
        """ファイルパスからモジュール名を生成"""
        try:
            relative_path = file_path.relative_to(self.src_root)
            
            if relative_path.name == "__init__.py":
                # __init__.pyの場合は親ディレクトリまで
                parts = relative_path.parent.parts
            else:
                # .pyファイルの場合は拡張子を除去
                parts = relative_path.with_suffix('').parts
            
            if parts:
                return 'src.' + '.'.join(parts)
            else:
                return 'src'
                
        except ValueError:
            # src_root配下にない場合
            return str(file_path)
    
    def get_analysis_summary(self) -> dict:
        """解析結果のサマリーを取得"""
        total_files = len(self.file_imports)
        total_imports = sum(len(imports) for imports in self.file_imports.values())
        files_with_imports = sum(1 for imports in self.file_imports.values() if imports)
        
        return {
            'total_files': total_files,
            'total_imports': total_imports,
            'files_with_imports': files_with_imports,
            'parse_errors': len(self.parse_errors),
            'error_details': self.parse_errors
        }
    
    def debug_print_imports(self, limit: int = 5) -> None:
        """デバッグ用: インポート情報を表示"""
        print(f"\nインポート情報（上位{limit}ファイル）:")
        
        count = 0
        for file_path, imports in self.file_imports.items():
            if count >= limit:
                break
            
            rel_path = file_path.relative_to(self.src_root)
            print(f"\n  {rel_path}:")
            
            if not imports:
                print(f"    インポートなし")
            else:
                for imp in imports:
                    print(f"    {imp}")
            
            count += 1