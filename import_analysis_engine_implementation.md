# インポート解析エンジン実装詳細（src_check用）

## 1. 概要

既存の`structure_organizer.py`を拡張し、ASTベースでインポート関係を解析してファイル移動に伴うインポートパス更新を自動化する。src_check配下では副作用許可のため、直接的なファイル操作で実装コストを抑える。

## 2. src_check統合アーキテクチャ

```
src_check/src_processors/auto_correct/import_dependency_reorganizer/
├── main.py                    # src_check/main.pyから呼ばれるエントリーポイント
├── config.py                  # 設定管理（モジュール内で完結）
├── import_analysis_engine.py  # メインエンジン（直接ファイル操作）
├── dependency_analyzer.py     # 既存structure_organizerとの統合
└── import_updater.py          # インポートパス更新

src_check配下の特徴:
- 副作用許可（直接ファイル操作可能）
- モジュール内で閉じた設定管理
- 実装コスト重視のシンプル構成
```

## 3. エントリーポイント実装

### 3.1 main.py (src_check統合用)
```python
import sys
import os
from pathlib import Path

# プロジェクトルートをsys.pathに追加（既存パターン）
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from models.check_result import CheckResult, FailureLocation
from .config import Config
from .import_analysis_engine import ImportAnalysisEngine

def main() -> CheckResult:
    """
    src_check/main.pyから呼ばれるエントリーポイント
    依存関係ベースフォルダ構造整理の結果を返す
    """
    try:
        # 設定取得（モジュール内で完結）
        config = Config()
        
        # エンジン初期化
        engine = ImportAnalysisEngine(
            src_root=config.src_root,
            max_depth=config.max_depth,
            backup_enabled=config.backup_enabled
        )
        
        if config.simulation_mode:
            # シミュレーション実行
            simulation_result = engine.simulate_reorganization()
            
            if not simulation_result.success:
                failures = []
                for error in simulation_result.errors:
                    failures.append(FailureLocation(
                        file_path=error.get('file_path', 'unknown'),
                        line_number=error.get('line_number', 0)
                    ))
                
                return CheckResult(
                    failure_locations=failures,
                    fix_policy="依存関係解析でエラーが検出されました",
                    fix_example_code=None
                )
            
            print(f"シミュレーション完了: {len(simulation_result.planned_moves)}ファイルの移動を計画")
            return CheckResult(
                failure_locations=[],
                fix_policy=f"シミュレーション成功: {len(simulation_result.planned_moves)}ファイルの移動を計画",
                fix_example_code=None
            )
        else:
            # 実際の整理実行
            execution_result = engine.execute_reorganization()
            
            if execution_result.success:
                print(f"整理完了: {len(execution_result.moved_files)}ファイルを移動")
                return CheckResult(
                    failure_locations=[],
                    fix_policy=f"ファイル移動完了: {len(execution_result.moved_files)}ファイルを移動",
                    fix_example_code=None
                )
            else:
                return CheckResult(
                    failure_locations=[FailureLocation(file_path="system", line_number=0)],
                    fix_policy=f"ファイル移動失敗: {execution_result.error}",
                    fix_example_code=None
                )
                
    except Exception as e:
        return CheckResult(
            failure_locations=[FailureLocation(file_path="system", line_number=0)],
            fix_policy=f"エラー: {str(e)}",
            fix_example_code=None
        )
```

### 3.2 config.py（モジュール内で閉じた設定管理）
```python
import json
from pathlib import Path
from typing import Optional

class Config:
    """
    インポート解析エンジンの設定管理
    モジュール内で完結し、他のファイルとの相互作用を最小限にする
    """
    
    def __init__(self, config_file: Optional[Path] = None):
        # デフォルト設定（src_check配下では実装コスト重視でデフォルト値許可）
        self.src_root = Path("src")
        self.max_depth = 4
        self.simulation_mode = True
        self.backup_enabled = True
        self.exclude_patterns = ["__pycache__", "*.pyc", "test_*.py", "*_test.py"]
        self.circular_dependency_action = "stop"  # "stop" | "warn" | "skip"
        
        # 設定ファイルが指定されていれば読み込み
        if config_file and config_file.exists():
            self._load_from_file(config_file)
        else:
            # デフォルトの設定ファイルパスを試行
            default_config = Path(__file__).parent / "config.json"
            if default_config.exists():
                self._load_from_file(default_config)
    
    def _load_from_file(self, config_file: Path):
        """設定ファイルから設定を読み込み"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 設定値を上書き
            if 'src_root' in config_data:
                self.src_root = Path(config_data['src_root'])
            if 'max_depth' in config_data:
                self.max_depth = config_data['max_depth']
            if 'simulation_mode' in config_data:
                self.simulation_mode = config_data['simulation_mode']
            if 'backup_enabled' in config_data:
                self.backup_enabled = config_data['backup_enabled']
            if 'exclude_patterns' in config_data:
                self.exclude_patterns = config_data['exclude_patterns']
            if 'circular_dependency_action' in config_data:
                self.circular_dependency_action = config_data['circular_dependency_action']
                
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
            print("デフォルト設定を使用します")
    
    def save_default_config(self, config_file: Optional[Path] = None):
        """デフォルト設定ファイルを生成"""
        if config_file is None:
            config_file = Path(__file__).parent / "config.json"
        
        config_data = {
            "src_root": str(self.src_root),
            "max_depth": self.max_depth,
            "simulation_mode": self.simulation_mode,
            "backup_enabled": self.backup_enabled,
            "exclude_patterns": self.exclude_patterns,
            "circular_dependency_action": self.circular_dependency_action
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
```

### 3.3 データクラス定義
```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Set
from pathlib import Path
from enum import Enum

class ImportType(Enum):
    ABSOLUTE = "absolute"
    RELATIVE = "relative"
    FROM_IMPORT = "from_import"

@dataclass(frozen=True)
class ImportStatement:
    """単一のインポート文を表現"""
    line_number: int
    raw_statement: str
    import_type: ImportType
    module_path: str
    imported_names: List[str]
    alias: Optional[str]
    level: int

@dataclass
class SimulationResult:
    """シミュレーション結果"""
    success: bool
    errors: List[Dict[str, any]]
    warnings: List[str]
    planned_moves: Dict[Path, Path]

@dataclass
class ExecutionResult:
    """実行結果"""
    success: bool
    moved_files: Dict[Path, Path]
    updated_files: Set[Path]
    error: Optional[str] = None
```

### 3.4 import_analysis_engine.py（メインエンジン）
```python
import ast
import shutil
from pathlib import Path
from typing import Dict, List, Set, Optional
from .config import Config
from .dependency_analyzer import DependencyAnalyzer
from .import_updater import ImportUpdater

class ImportAnalysisEngine:
    """
    インポート解析とファイル移動を実行するメインエンジン
    src_check配下なので直接ファイル操作を許可
    """
    
    def __init__(self, src_root: Path, max_depth: int, backup_enabled: bool = True):
        self.src_root = src_root
        self.max_depth = max_depth
        self.backup_enabled = backup_enabled
        self.backup_dir = Path("backup/import_reorganization")
        
        # 依存関係解析器とインポート更新器を初期化
        self.dependency_analyzer = DependencyAnalyzer(src_root)
        self.import_updater = ImportUpdater(src_root)
    
    def simulate_reorganization(self) -> SimulationResult:
        """
        ファイル移動のシミュレーション実行
        実際のファイル操作は行わない
        """
        try:
            print("依存関係を解析中...")
            
            # 1. 依存関係解析
            import_graph = self.dependency_analyzer.build_import_graph()
            
            # 2. 循環参照チェック
            circular_refs = self.dependency_analyzer.detect_circular_references(import_graph)
            if circular_refs:
                return SimulationResult(
                    success=False,
                    errors=[{"message": f"循環参照が検出されました: {circular_refs}"}],
                    warnings=[],
                    planned_moves={}
                )
            
            # 3. 依存深度計算
            print("依存深度を計算中...")
            depth_map = self.dependency_analyzer.calculate_dependency_depths(import_graph, self.max_depth)
            
            # 4. 移動計画作成
            print("ファイル移動計画を作成中...")
            planned_moves = self._create_move_plan(depth_map)
            
            # 5. インポート更新可能性をチェック
            print("インポート更新を検証中...")
            import_issues = self._validate_import_updates(planned_moves)
            
            if import_issues:
                return SimulationResult(
                    success=False,
                    errors=import_issues,
                    warnings=[],
                    planned_moves=planned_moves
                )
            
            return SimulationResult(
                success=True,
                errors=[],
                warnings=[],
                planned_moves=planned_moves
            )
            
        except Exception as e:
            return SimulationResult(
                success=False,
                errors=[{"message": f"シミュレーションエラー: {str(e)}"}],
                warnings=[],
                planned_moves={}
            )
    
    def execute_reorganization(self) -> ExecutionResult:
        """
        実際のファイル移動とインポート更新を実行
        """
        # まずシミュレーション実行
        simulation = self.simulate_reorganization()
        if not simulation.success:
            return ExecutionResult(
                success=False,
                moved_files={},
                updated_files=set(),
                error=f"シミュレーション失敗: {simulation.errors}"
            )
        
        try:
            moved_files = {}
            updated_files = set()
            backup_info = {}
            
            # バックアップ作成
            if self.backup_enabled:
                print("バックアップを作成中...")
                backup_info = self._create_backup(list(simulation.planned_moves.keys()))
            
            # ファイル移動実行
            print("ファイルを移動中...")
            for old_path, new_path in simulation.planned_moves.items():
                # ディレクトリ作成
                new_path.parent.mkdir(parents=True, exist_ok=True)
                
                # ファイル移動
                shutil.move(str(old_path), str(new_path))
                moved_files[old_path] = new_path
                print(f"移動: {old_path} -> {new_path}")
            
            # インポート更新実行
            print("インポート文を更新中...")
            updated_files = self.import_updater.update_all_imports(simulation.planned_moves)
            
            # 更新後の構文チェック
            print("構文チェック中...")
            syntax_errors = self._validate_syntax(updated_files)
            if syntax_errors:
                # エラーがあればロールバック
                print("構文エラーが検出されました。ロールバック中...")
                self._rollback(backup_info, moved_files)
                return ExecutionResult(
                    success=False,
                    moved_files={},
                    updated_files=set(),
                    error=f"構文エラー: {syntax_errors}"
                )
            
            # バックアップファイル削除
            if self.backup_enabled:
                self._cleanup_backup(backup_info)
            
            return ExecutionResult(
                success=True,
                moved_files=moved_files,
                updated_files=updated_files,
                error=None
            )
            
        except Exception as e:
            # エラー時のロールバック
            if backup_info:
                self._rollback(backup_info, moved_files)
            
            return ExecutionResult(
                success=False,
                moved_files={},
                updated_files=set(),
                error=f"実行エラー: {str(e)}"
            )
    
    def _create_move_plan(self, depth_map: Dict[Path, int]) -> Dict[Path, Path]:
        """深度に基づいてファイル移動計画を作成"""
        move_plan = {}
        
        for file_path, depth in depth_map.items():
            if depth == 0:
                # 深度0はsrc直下
                new_path = self.src_root / file_path.name
            else:
                # 深度に応じた階層に配置
                folder_name = file_path.stem
                new_path = self.src_root
                
                # 深度分だけフォルダを作成
                for i in range(depth):
                    new_path = new_path / f"level_{i+1}"
                
                new_path = new_path / folder_name / file_path.name
            
            if new_path != file_path:
                move_plan[file_path] = new_path
        
        return move_plan
    
    def _validate_import_updates(self, planned_moves: Dict[Path, Path]) -> List[Dict[str, any]]:
        """インポート更新の妥当性を事前チェック"""
        issues = []
        
        for old_path, new_path in planned_moves.items():
            try:
                # 移動対象ファイルを参照している他のファイルを検索
                referencing_files = self.import_updater.find_referencing_files(old_path)
                
                for ref_file in referencing_files:
                    # インポート更新が可能かチェック
                    can_update = self.import_updater.can_update_imports(ref_file, {old_path: new_path})
                    if not can_update:
                        issues.append({
                            "file_path": str(ref_file),
                            "line_number": 0,
                            "message": f"インポート更新が困難: {old_path} -> {new_path}"
                        })
                        
            except Exception as e:
                issues.append({
                    "file_path": str(old_path),
                    "line_number": 0,
                    "message": f"検証エラー: {e}"
                })
        
        return issues
    
    def _create_backup(self, files: List[Path]) -> Dict[Path, Path]:
        """バックアップファイル作成"""
        backup_mapping = {}
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in files:
            backup_path = self.backup_dir / f"{file_path.name}.backup"
            shutil.copy2(file_path, backup_path)
            backup_mapping[file_path] = backup_path
        
        return backup_mapping
    
    def _validate_syntax(self, files: Set[Path]) -> List[str]:
        """構文チェック実行"""
        errors = []
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                ast.parse(source)
            except SyntaxError as e:
                errors.append(f"{file_path}:{e.lineno}: {e.msg}")
            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")
        
        return errors
    
    def _rollback(self, backup_info: Dict[Path, Path], moved_files: Dict[Path, Path]):
        """ロールバック実行"""
        print("ロールバックを実行中...")
        
        # 移動したファイルを元に戻す
        for old_path, new_path in moved_files.items():
            if new_path.exists():
                shutil.move(str(new_path), str(old_path))
        
        # バックアップから復元
        for original_path, backup_path in backup_info.items():
            if backup_path.exists() and original_path.exists():
                shutil.copy2(backup_path, original_path)
    
    def _cleanup_backup(self, backup_info: Dict[Path, Path]):
        """バックアップファイルのクリーンアップ"""
        for backup_path in backup_info.values():
            if backup_path.exists():
                backup_path.unlink()
        
        if self.backup_dir.exists() and not any(self.backup_dir.iterdir()):
            self.backup_dir.rmdir()
```

## 4. 設定ファイル例

### 4.1 config.json（モジュール内設定）
```json
{
  "src_root": "src",
  "max_depth": 4,
  "simulation_mode": true,
  "backup_enabled": true,
  "exclude_patterns": ["__pycache__", "*.pyc", "test_*.py", "*_test.py"],
  "circular_dependency_action": "stop"
}
```

## 5. 実装順序（src_check用シンプル版）

### 5.1 Phase 1: 基盤実装
1. **config.py**: モジュール内設定管理
2. **基本的なmain.py**: CheckResult返却のみ
3. **dependency_analyzer.py**: 既存structure_organizerとの統合
4. **単体テスト**: 各コンポーネントの動作確認

### 5.2 Phase 2: コア機能実装
1. **import_updater.py**: インポート文の更新ロジック
2. **import_analysis_engine.py**: メインエンジン
3. **ファイル操作機能**: バックアップ・移動・復元
4. **シミュレーション機能**: dry-run実装

### 5.3 Phase 3: 統合と最適化
1. **エラーハンドリング**: ロールバック機能
2. **構文チェック**: AST解析による検証
3. **パフォーマンス最適化**
4. **統合テスト**: 実際のプロジェクトでの検証

## 6. src_check/main.pyとの統合

### 6.1 呼び出しパターン
```bash
# シミュレーションモードで実行（デフォルト）
cd /home/cphelper/project-cph
python -m src_check.main --verbose

# 実際の整理実行
# config.jsonでsimulation_mode: falseに変更後実行
python -m src_check.main
```

### 6.2 出力例
```
実行されたルール数: 15
■ ルール: src_processors_auto_correct_import_dependency_reorganizer_main
  失敗件数: 0

  修正方針:
    シミュレーション成功: 23ファイルの移動を計画

  詳細はsrc_check_result/src_processors_auto_correct_import_dependency_reorganizer_main.txtを参照してください
```

この実装により、src_check配下での副作用許可とモジュール内閉じた設定管理により、実装コストを抑えつつ確実に動作するインポート解析エンジンが構築できます。