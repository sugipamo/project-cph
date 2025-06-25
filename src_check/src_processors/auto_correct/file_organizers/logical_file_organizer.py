import ast
import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import re

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from src_check.models.check_result import CheckResult, FailureLocation


@dataclass
class FileMove:
    source: Path
    destination: Path
    reason: str
    element_type: str  # 'function', 'class', 'module'
    element_name: str


@dataclass
class ImportUpdate:
    file_path: Path
    old_import: str
    new_import: str
    line_number: int


@dataclass
class RollbackInfo:
    timestamp: str
    moves: List[FileMove]
    import_updates: List[ImportUpdate]
    backup_dir: Path


class LogicalFileOrganizer:
    """論理的な構造に基づいてファイルを自動整理するツール"""
    
    # 論理的なカテゴリと対応するフォルダ名
    LOGICAL_CATEGORIES = {
        # データ層
        'models': ['model', 'entity', 'schema', 'dto'],
        'repositories': ['repository', 'repo', 'dao'],
        
        # ビジネスロジック層
        'services': ['service', 'business', 'logic'],
        'use_cases': ['usecase', 'use_case', 'interactor'],
        
        # プレゼンテーション層
        'controllers': ['controller', 'handler', 'endpoint'],
        'views': ['view', 'template', 'ui'],
        
        # インフラ層
        'infrastructure': ['infra', 'infrastructure', 'external'],
        'adapters': ['adapter', 'connector', 'client'],
        
        # ユーティリティ
        'utils': ['util', 'utils', 'helper', 'helpers'],
        'validators': ['validator', 'validation', 'check'],
        'formatters': ['formatter', 'format', 'serializer'],
        'parsers': ['parser', 'parse', 'reader'],
        
        # 設定・定数
        'config': ['config', 'configuration', 'settings'],
        'constants': ['constant', 'const', 'enum'],
        
        # テスト
        'tests': ['test', 'tests', 'spec'],
    }
    
    def __init__(self, src_dir: str, dry_run: bool = True):
        self.src_dir = Path(src_dir)
        self.dry_run = dry_run
        self.file_moves: List[FileMove] = []
        self.import_updates: List[ImportUpdate] = []
        self.rollback_info: Optional[RollbackInfo] = None
        
    def organize(self) -> Tuple[List[FileMove], List[ImportUpdate]]:
        """ファイルを論理的に整理"""
        print(f"🔍 ファイル整理を{'シミュレーション' if self.dry_run else '実行'}します: {self.src_dir}")
        
        # 1. 現在の構造を分析
        self._analyze_current_structure()
        
        # 2. 論理的な移動計画を作成
        self._create_move_plan()
        
        # 3. インポート更新計画を作成
        self._create_import_update_plan()
        
        # 4. 実行またはシミュレーション
        if not self.dry_run:
            self._execute_organization()
        else:
            self._show_simulation()
            
        return self.file_moves, self.import_updates
        
    def _analyze_current_structure(self) -> None:
        """現在のファイル構造を分析"""
        print("\n📊 現在の構造を分析中...")
        
        for py_file in self.src_dir.rglob("*.py"):
            if "__pycache__" in str(py_file) or "_test.py" in str(py_file):
                continue
                
            logical_category = self._determine_logical_category(py_file)
            if logical_category:
                ideal_path = self._get_ideal_path(py_file, logical_category)
                
                if ideal_path != py_file:
                    move = FileMove(
                        source=py_file,
                        destination=ideal_path,
                        reason=f"{logical_category}カテゴリに属するため",
                        element_type=self._get_element_type(py_file),
                        element_name=py_file.stem
                    )
                    self.file_moves.append(move)
                    
    def _determine_logical_category(self, file_path: Path) -> Optional[str]:
        """ファイルの論理的カテゴリを判定"""
        file_name = file_path.stem.lower()
        
        # ファイル名から判定
        for category, patterns in self.LOGICAL_CATEGORIES.items():
            for pattern in patterns:
                if pattern in file_name:
                    return category
                    
        # ファイル内容から判定
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_name = node.name.lower()
                    for category, patterns in self.LOGICAL_CATEGORIES.items():
                        for pattern in patterns:
                            if pattern in class_name:
                                return category
                                
        except Exception:
            pass
            
        return None
        
    def _get_ideal_path(self, current_path: Path, category: str) -> Path:
        """理想的なファイルパスを生成"""
        # カテゴリ別のディレクトリ構造
        category_dir = self.src_dir / category
        
        # サブカテゴリを判定（例: user_repository.py → repositories/user/）
        file_stem = current_path.stem
        
        # パターンを削除してエンティティ名を抽出
        entity_name = file_stem
        for _, patterns in self.LOGICAL_CATEGORIES.items():
            for pattern in patterns:
                entity_name = entity_name.replace(f"_{pattern}", "").replace(f"{pattern}_", "")
                
        # 特定のカテゴリではエンティティ別のサブフォルダを作成
        if category in ['repositories', 'services', 'controllers', 'models']:
            if entity_name and entity_name != file_stem:
                return category_dir / entity_name / current_path.name
                
        return category_dir / current_path.name
        
    def _get_element_type(self, file_path: Path) -> str:
        """ファイルの要素タイプを判定"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            has_classes = any(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
            has_functions = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
            
            if has_classes:
                return 'class'
            elif has_functions:
                return 'function'
            else:
                return 'module'
                
        except Exception:
            return 'module'
            
    def _create_move_plan(self) -> None:
        """移動計画を最適化"""
        # 依存関係を考慮して移動順序を決定
        self.file_moves.sort(key=lambda m: (
            # まずユーティリティやモデルなど基盤となるものを移動
            0 if m.destination.parts[-2] in ['utils', 'models', 'constants'] else 1,
            # 次にリポジトリやサービス
            0 if m.destination.parts[-2] in ['repositories', 'services'] else 1,
            # 最後にコントローラーなど上位層
            str(m.source)
        ))
        
    def _create_import_update_plan(self) -> None:
        """インポート更新計画を作成"""
        # 移動されるファイルのマッピングを作成
        move_mapping = {}
        for move in self.file_moves:
            old_module = self._path_to_module(move.source)
            new_module = self._path_to_module(move.destination)
            move_mapping[old_module] = new_module
            
        # 全ファイルのインポートをチェック
        for py_file in self.src_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for i, line in enumerate(lines):
                    for old_module, new_module in move_mapping.items():
                        if f"from {old_module}" in line or f"import {old_module}" in line:
                            new_line = line.replace(old_module, new_module)
                            
                            update = ImportUpdate(
                                file_path=py_file,
                                old_import=line.strip(),
                                new_import=new_line.strip(),
                                line_number=i + 1
                            )
                            self.import_updates.append(update)
                            
            except Exception as e:
                print(f"⚠️  {py_file}の解析中にエラー: {e}")
                
    def _path_to_module(self, path: Path) -> str:
        """パスをモジュール名に変換"""
        try:
            relative = path.relative_to(self.src_dir)
            parts = list(relative.parts)
            if parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]
            return '.'.join(parts)
        except ValueError:
            return str(path)
            
    def _execute_organization(self) -> None:
        """実際にファイルを移動"""
        print("\n🚀 ファイル整理を実行中...")
        
        # バックアップディレクトリを作成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.src_dir.parent / f".file_org_backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)
        
        # ロールバック情報を初期化
        self.rollback_info = RollbackInfo(
            timestamp=timestamp,
            moves=[],
            import_updates=[],
            backup_dir=backup_dir
        )
        
        # ファイルを移動
        for move in self.file_moves:
            try:
                # バックアップ
                backup_path = backup_dir / move.source.relative_to(self.src_dir)
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(move.source, backup_path)
                
                # 移動先ディレクトリを作成
                move.destination.parent.mkdir(parents=True, exist_ok=True)
                
                # ファイルを移動
                shutil.move(str(move.source), str(move.destination))
                self.rollback_info.moves.append(move)
                
                print(f"✅ 移動: {move.source} → {move.destination}")
                
                # 必要に応じて__init__.pyを作成
                self._ensure_init_files(move.destination.parent)
                
            except Exception as e:
                print(f"❌ 移動失敗: {move.source} - {e}")
                
        # インポートを更新
        self._update_imports()
        
        # ロールバック情報を保存
        self._save_rollback_info()
        
        # 空のディレクトリを削除
        self._cleanup_empty_dirs()
        
    def _ensure_init_files(self, directory: Path) -> None:
        """__init__.pyファイルを確保"""
        current = directory
        while current != self.src_dir and current != current.parent:
            init_file = current / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                print(f"📄 作成: {init_file}")
            current = current.parent
            
    def _update_imports(self) -> None:
        """インポート文を更新"""
        files_to_update = defaultdict(list)
        
        for update in self.import_updates:
            files_to_update[update.file_path].append(update)
            
        for file_path, updates in files_to_update.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # バックアップ
                if self.rollback_info:
                    backup_path = self.rollback_info.backup_dir / file_path.relative_to(self.src_dir)
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, backup_path)
                    
                # インポートを更新
                for update in updates:
                    content = content.replace(update.old_import, update.new_import)
                    
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                print(f"📝 インポート更新: {file_path} ({len(updates)}箇所)")
                
                if self.rollback_info:
                    self.rollback_info.import_updates.extend(updates)
                    
            except Exception as e:
                print(f"❌ インポート更新失敗: {file_path} - {e}")
                
    def _cleanup_empty_dirs(self) -> None:
        """空のディレクトリを削除"""
        for root, dirs, files in os.walk(self.src_dir, topdown=False):
            if not files and not dirs and root != str(self.src_dir):
                try:
                    Path(root).rmdir()
                    print(f"🗑️  空ディレクトリ削除: {root}")
                except Exception:
                    pass
                    
    def _save_rollback_info(self) -> None:
        """ロールバック情報を保存"""
        if self.rollback_info:
            rollback_file = self.src_dir.parent / f".rollback_{self.rollback_info.timestamp}.json"
            
            data = {
                'timestamp': self.rollback_info.timestamp,
                'backup_dir': str(self.rollback_info.backup_dir),
                'moves': [
                    {
                        'source': str(m.source),
                        'destination': str(m.destination),
                        'reason': m.reason
                    }
                    for m in self.rollback_info.moves
                ],
                'import_updates': [
                    {
                        'file_path': str(u.file_path),
                        'old_import': u.old_import,
                        'new_import': u.new_import,
                        'line_number': u.line_number
                    }
                    for u in self.rollback_info.import_updates
                ]
            }
            
            with open(rollback_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"\n💾 ロールバック情報を保存: {rollback_file}")
            
    def _show_simulation(self) -> None:
        """シミュレーション結果を表示"""
        print("\n📋 実行計画（Dry Run）:")
        
        if self.file_moves:
            print("\n🚚 ファイル移動:")
            
            # カテゴリ別にグループ化
            moves_by_category = defaultdict(list)
            for move in self.file_moves:
                category = move.destination.parts[-2] if len(move.destination.parts) > 1 else 'root'
                moves_by_category[category].append(move)
                
            for category, moves in sorted(moves_by_category.items()):
                print(f"\n  📁 {category}/")
                for move in moves:
                    print(f"    ├─ {move.source.name} ← {move.source.parent}")
                    print(f"    │  理由: {move.reason}")
                    
        if self.import_updates:
            print(f"\n📝 インポート更新: {len(self.import_updates)}箇所")
            
            # ファイル別にグループ化
            updates_by_file = defaultdict(int)
            for update in self.import_updates:
                updates_by_file[update.file_path] += 1
                
            for file_path, count in sorted(updates_by_file.items()):
                print(f"  - {file_path}: {count}箇所")
                
    def rollback(self, rollback_file: Path) -> bool:
        """整理をロールバック"""
        print(f"\n🔄 ロールバックを実行: {rollback_file}")
        
        try:
            with open(rollback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            backup_dir = Path(data['backup_dir'])
            
            # ファイルを元に戻す
            for move_data in reversed(data['moves']):
                src = Path(move_data['destination'])
                dst = Path(move_data['source'])
                
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                    print(f"✅ 復元: {dst}")
                    
            # バックアップから元のファイルを復元
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    backup_file = Path(root) / file
                    relative = backup_file.relative_to(backup_dir)
                    original = self.src_dir / relative
                    
                    original.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_file, original)
                    print(f"✅ 復元: {original}")
                    
            # バックアップディレクトリを削除
            shutil.rmtree(backup_dir)
            
            print("\n✅ ロールバック完了")
            return True
            
        except Exception as e:
            print(f"❌ ロールバック失敗: {e}")
            return False


def main() -> CheckResult:
    project_root = Path(__file__).parent.parent.parent.parent
    src_dir = project_root / 'src'
    
    print(f"🔍 論理的ファイル整理解析を開始: {src_dir}")
    
    # Dry runモードで実行
    organizer = LogicalFileOrganizer(str(src_dir), dry_run=True)
    file_moves, import_updates = organizer.organize()
    
    failure_locations = []
    
    # 移動が必要なファイルをfailure_locationsに追加
    for move in file_moves:
        failure_locations.append(FailureLocation(
            file_path=str(move.source),
            line_number=0
        ))
        
    if failure_locations:
        fix_policy = (
            f"{len(file_moves)}個のファイルを論理的なフォルダ構造に再配置します。\n"
            f"フォルダ名から機能が一目でわかる構造になります。\n"
            f"影響を受けるインポート: {len(import_updates)}箇所"
        )
        
        # カテゴリ別の移動数を集計
        category_counts = defaultdict(int)
        for move in file_moves:
            category = move.destination.parts[-2] if len(move.destination.parts) > 1 else 'root'
            category_counts[category] += 1
            
        fix_example = "# 整理後のフォルダ構造:\nsrc/\n"
        for category, count in sorted(category_counts.items()):
            fix_example += f"  {category}/  # {count}ファイル\n"
            
    else:
        fix_policy = "現在のファイル構造は既に論理的に整理されています。"
        fix_example = None
        
    return CheckResult(
        failure_locations=failure_locations,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )


if __name__ == "__main__":
    # テスト実行
    result = main(None)
    print(f"\nCheckResult: {len(result.failure_locations)} files need reorganization")