# src_check整理・動的インポート実装方針

## 概要
src_check配下の複雑化したモジュール群を動的インポートにより整理し、DFS探索によるmain.py発見・実行機能を実装する。

## 現状分析結果

### 発見されたmain.pyファイル（7個）
1. **`src_check/main.py`** - メインエントリーポイント
2. **`src_processors/auto_correct/argument_processors/main.py`** - 引数デフォルト値削除
3. **`src_processors/auto_correct/file_organizers/main.py`** - ファイル構造整理（4モード）
4. **`src_processors/auto_correct/import_dependency_reorganizer/main.py`** - 依存関係ベース整理
5. **`src_processors/auto_correct/import_fixers/main.py`** - インポート修正（実装不完全）
6. **`src_processors/auto_correct/remnant_cleaners/main.py`** - 残骸削除
7. **`src_processors/auto_correct/type_hints/main.py`** - 型ヒント追加

### 主要問題
- **122件の壊れたインポート** - 最優先解決事項
- **2件の循環インポート** - 構造的問題
- **実装不完全モジュール** - import_fixers等
- **設定管理分散** - 環境変数とJSON設定が混在

## 実装方針

### Phase 1: 基盤整備（最優先）

#### 1.1 依存関係修正
```
優先度: 最高
対象: 122件の壊れたインポート、2件の循環インポート
実装: 
- 自動修正ツールの実装
- インポートパス正規化
- 循環依存の解消
```

#### 1.2 統一インターフェース設計
```python
# src_check/interfaces/processor_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from models.check_result import CheckResult

class ProcessorInterface(ABC):
    @abstractmethod
    def get_name(self) -> str:
        """処理名を返す"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """処理説明を返す"""
        pass
    
    @abstractmethod
    def execute(self, config: Dict[str, Any]) -> CheckResult:
        """処理を実行する"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """実行可能かチェック"""
        pass
```

### Phase 2: 動的インポート基盤

#### 2.1 モジュール発見エンジン
```python
# src_check/core/module_explorer.py
class ModuleExplorer:
    def discover_main_modules(self, base_path: Path) -> List[ModuleInfo]:
        """DFS探索でmain.pyを発見"""
        # 辞書順降順でディレクトリをソート
        # 深度優先探索でmain.pyを発見
        # ModuleInfoオブジェクトを生成
        pass
    
    def validate_module(self, module_path: Path) -> bool:
        """モジュールの有効性チェック"""
        pass
```

#### 2.2 動的インポート管理
```python
# src_check/core/dynamic_importer.py
class DynamicImporter:
    def import_processor(self, module_path: Path) -> ProcessorInterface:
        """動的にプロセッサーをインポート"""
        # importlib.util.spec_from_file_location使用
        # ProcessorInterface準拠チェック
        # エラーハンドリング
        pass
    
    def get_processor_info(self, module_path: Path) -> ProcessorInfo:
        """プロセッサー情報を取得"""
        pass
```

#### 2.3 実行コーディネーター
```python
# src_check/core/execution_coordinator.py
class ExecutionCoordinator:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.explorer = ModuleExplorer()
        self.importer = DynamicImporter()
    
    def execute_all(self) -> List[CheckResult]:
        """全プロセッサーを実行"""
        pass
    
    def execute_selected(self, processor_names: List[str]) -> List[CheckResult]:
        """選択されたプロセッサーを実行"""
        pass
```

### Phase 3: 設定管理統一

#### 3.1 統一設定システム
```python
# src_check/core/config_manager.py
class ConfigManager:
    def __init__(self, config_file: str = "src_check_config.json"):
        self.config_file = config_file
        self.load_config()
    
    def get_processor_config(self, processor_name: str) -> Dict[str, Any]:
        """プロセッサー固有設定を取得"""
        pass
    
    def get_global_config(self) -> Dict[str, Any]:
        """グローバル設定を取得"""
        pass
```

#### 3.2 設定スキーマ
```json
{
  "global": {
    "dry_run": false,
    "project_root": "./project-cph",
    "src_path": "src",
    "log_level": "INFO"
  },
  "processors": {
    "argument_processors": {
      "enabled": true,
      "target_extensions": [".py"],
      "exclude_patterns": ["test_*", "*_test.py"]
    },
    "file_organizers": {
      "enabled": true,
      "mode": "logical",
      "backup_enabled": true
    },
    "import_dependency_reorganizer": {
      "enabled": true,
      "max_files": 250,
      "detect_cycles": true
    }
  }
}
```

### Phase 4: 新main.py実装

#### 4.1 エントリーポイント再設計
```python
# src_check/main.py
def main():
    """統合エントリーポイント"""
    # 1. 設定読み込み
    config_manager = ConfigManager()
    
    # 2. 実行コーディネーター初期化
    coordinator = ExecutionCoordinator(config_manager)
    
    # 3. プロセッサー発見
    processors = coordinator.discover_processors()
    
    # 4. 実行
    results = coordinator.execute_all()
    
    # 5. 結果統合・出力
    report_generator = ReportGenerator()
    report_generator.generate_report(results)
```

#### 4.2 CLI拡張
```python
# コマンドライン引数拡張
python3 src_check/main.py --list-processors
python3 src_check/main.py --run argument_processors,file_organizers
python3 src_check/main.py --config custom_config.json
python3 src_check/main.py --dry-run
```

## 実装順序

### Step 1: 緊急修正（即実施）
1. 壊れたインポートの修正
2. 循環インポートの解消
3. 実装不完全モジュールの完成

### Step 2: 基盤実装（1週間）
1. ProcessorInterface定義
2. ModuleExplorer実装
3. DynamicImporter実装
4. ConfigManager実装

### Step 3: 統合実装（1週間）
1. ExecutionCoordinator実装
2. 新main.py実装
3. 既存main.pyのProcessorInterface準拠化

### Step 4: 検証・最適化（数日）
1. 全機能テスト
2. パフォーマンス最適化
3. エラーハンドリング改善

## 制約事項の遵守

### CLAUDE.md制約
- ✅ デフォルト値使用禁止 → 全設定を明示的に指定
- ✅ フォールバック処理禁止 → エラー時は明確に失敗
- ✅ 副作用制限 → 読み取り専用操作を基本とする
- ✅ 設定ファイル統一 → JSON設定による一元管理

### 技術制約
- ✅ `cwd=./project-cph`での実行環境維持
- ✅ DFS探索アルゴリズム実装
- ✅ 辞書順降順ソート
- ✅ 既存CLI互換性維持

## 期待効果

### 短期効果
- src_check実行時のエラー解消
- 122件の壊れたインポート修正
- 循環インポート解消

### 中長期効果
- 処理の選択的実行
- 新機能追加の容易性
- 保守性・拡張性向上
- コードベース全体の品質向上

## リスク対策

### 実装リスク
- **既存機能の互換性** → 段階的移行とテスト強化
- **パフォーマンス低下** → ベンチマーク実施
- **設定管理の複雑化** → シンプルなスキーマ設計

### 運用リスク
- **学習コスト** → 詳細ドキュメント作成
- **設定ミス** → バリデーション強化
- **障害対応** → 詳細ログ出力とエラー分類