# 品質チェッカーリファクタリング計画

## 概要

現在の品質チェッカーは以下の問題を抱えており、CLAUDE.mdの指針に沿った改善が必要です：

- ハードコードされたパス指定（`src/**/*.py`）
- ProgressSpinnerクラスの重複定義
- 設定管理の非統一
- 拡張性の欠如（scriptsディレクトリ等への対応困難）

## 現状分析

### 問題のあるファイル一覧
- `scripts/quality_checks/dependency_injection_checker.py`
- `scripts/quality_checks/dict_get_checker.py`
- `scripts/quality_checks/fallback_checker.py`
- `scripts/quality_checks/getattr_checker.py`
- `scripts/quality_checks/infrastructure_duplication_checker.py`
- `scripts/quality_checks/naming_checker.py`
- `scripts/quality_checks/none_default_checker.py`
- `scripts/quality_checks/print_usage_checker.py`
- `scripts/quality_checks/syntax_checker.py`
- `scripts/quality_checks/type_checker.py`
- `scripts/quality_checks/ruff_checker.py`

### 共通問題
1. **ハードコードされたパス**: 全てのファイルで`glob.glob('src/**/*.py', recursive=True)`
2. **ProgressSpinner重複**: 各ファイルで同一クラスを重複定義
3. **除外パターンの非統一**: ファイルごとに異なる除外ロジック
4. **設定管理の欠如**: フォールバック処理による設定値の隠蔽

## リファクタリング方針

### CLAUDE.md準拠事項
- デフォルト値の使用をグローバルに禁止
- 設定取得方法は`src/configuration/readme.md`を参照
- 存在しない設定は`{setting}.json`に追加して対応
- フォールバック処理は禁止
- 副作用は`src/infrastructure`、`tests/infrastructure`のみ
- 互換性維持に必要なものは必ず互換性維持のコメントを追記

## 実装計画

### フェーズ1: 設定基盤の構築

#### 1.1 設定ファイル作成
**ファイル**: `src/configuration/quality_checks.json`

```json
{
  "target_directories": ["src", "scripts"],
  "file_patterns": ["**/*.py"],
  "excluded_directories": {
    "infrastructure": ["src/infrastructure/", "tests/infrastructure/"],
    "logging": ["/logging/"],
    "tests": ["/tests/", "test_results/"]
  },
  "excluded_files": ["main.py"],
  "script_paths": {
    "dict_get_converter": "scripts/quality/convert_dict_get.py",
    "generic_name_checker": "scripts/quality/check_generic_names.py",
    "practical_quality_checker": "scripts/quality/practical_quality_check.py",
    "functional_quality_checker": "scripts/quality/functional_quality_check.py",
    "architecture_quality_checker": "scripts/quality/architecture_quality_check.py"
  },
  "allowed_directories": {
    "dependency_injection": ["src/infrastructure/", "tests/infrastructure/"]
  }
}
```

#### 1.2 設定読み込みユーティリティ作成
**ファイル**: `scripts/quality_checks/config/quality_config_loader.py`

```python
from typing import List, Dict, Any
from pathlib import Path
import json

class QualityConfigLoader:
    def __init__(self, config_path: str):
        self._config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        if not self._config_path.exists():
            raise FileNotFoundError(f"設定ファイルが存在しません: {self._config_path}")
        
        with open(self._config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_target_directories(self) -> List[str]:
        return self._config["target_directories"]
    
    def get_file_patterns(self) -> List[str]:
        return self._config["file_patterns"]
    
    def get_excluded_directories(self, category: str) -> List[str]:
        return self._config["excluded_directories"].get(category, [])
    
    def get_excluded_files(self) -> List[str]:
        return self._config["excluded_files"]
    
    def get_script_path(self, script_name: str) -> str:
        script_path = self._config["script_paths"].get(script_name)
        if not script_path:
            raise KeyError(f"スクリプトパスが設定されていません: {script_name}")
        return script_path
    
    def get_allowed_directories(self, category: str) -> List[str]:
        return self._config["allowed_directories"].get(category, [])
```

### フェーズ2: 共通基底クラスの構築

#### 2.1 共通基底クラス作成
**ファイル**: `scripts/quality_checks/base/base_quality_checker.py`

```python
import glob
from abc import ABC, abstractmethod
from typing import List, Set
from pathlib import Path

from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger
from .quality_config_loader import QualityConfigLoader
from .progress_spinner import ProgressSpinner

class BaseQualityChecker(ABC):
    def __init__(self, file_handler: FileHandler, logger: Logger, issues: List[str], verbose: bool = False):
        self.file_handler = file_handler
        self.logger = logger
        self.issues = issues
        self.verbose = verbose
        
        # 設定読み込み
        config_path = Path(__file__).parent.parent.parent.parent / "src" / "configuration" / "quality_checks.json"
        self.config = QualityConfigLoader(str(config_path))
    
    def get_target_files(self, excluded_categories: List[str] = None) -> List[str]:
        """設定に基づいてチェック対象ファイルを取得"""
        target_files = []
        excluded_categories = excluded_categories or []
        
        # 除外ディレクトリの収集
        excluded_dirs = set()
        for category in excluded_categories:
            excluded_dirs.update(self.config.get_excluded_directories(category))
        
        # 除外ファイルの収集
        excluded_files = set(self.config.get_excluded_files())
        
        # ファイル検索
        for target_dir in self.config.get_target_directories():
            for pattern in self.config.get_file_patterns():
                search_pattern = f"{target_dir}/{pattern}"
                for file_path in glob.glob(search_pattern, recursive=True):
                    if self._should_exclude_file(file_path, excluded_dirs, excluded_files):
                        continue
                    target_files.append(file_path)
        
        return sorted(target_files)
    
    def _should_exclude_file(self, file_path: str, excluded_dirs: Set[str], excluded_files: Set[str]) -> bool:
        """ファイルが除外対象かどうかを判定"""
        # 除外ディレクトリのチェック
        for excluded_dir in excluded_dirs:
            if excluded_dir in file_path:
                return True
        
        # 除外ファイルのチェック
        file_name = Path(file_path).name
        if file_name in excluded_files:
            return True
        
        return False
    
    def get_relative_path(self, file_path: str) -> str:
        """相対パスを取得"""
        # 互換性維持: 既存のsrc/プレフィックス除去動作を維持
        if file_path.startswith('src/'):
            return file_path.replace('src/', '')
        return file_path
    
    def create_progress_spinner(self, message: str) -> ProgressSpinner:
        """プログレススピナーを作成"""
        return ProgressSpinner(message, self.logger)
    
    @abstractmethod
    def check(self) -> bool:
        """品質チェックを実行（各チェッカーで実装）"""
        pass
```

#### 2.2 ProgressSpinnerの共通化
**ファイル**: `scripts/quality_checks/base/progress_spinner.py`

```python
from infrastructure.logger import Logger

class ProgressSpinner:
    def __init__(self, message: str, logger: Logger):
        self.message = message
        self.logger = logger

    def start(self):
        pass  # チェック中表示は不要

    def stop(self, success: bool = True):
        self.logger.info(f"{'✅' if success else '❌'} {self.message}")
```

### フェーズ3: 各チェッカーのリファクタリング

#### 3.1 リファクタリング対象の優先順位
1. **高優先度**: `syntax_checker.py`, `type_checker.py`, `ruff_checker.py`
2. **中優先度**: `naming_checker.py`, `print_usage_checker.py`
3. **低優先度**: その他の特定用途チェッカー

#### 3.2 リファクタリング例（syntax_checker.py）

**変更前**:
```python
def check_syntax(self):
    for file_path in glob.glob('src/**/*.py', recursive=True):
        # チェック処理
```

**変更後**:
```python
def check(self) -> bool:
    spinner = self.create_progress_spinner("構文チェック")
    spinner.start()
    
    target_files = self.get_target_files(excluded_categories=["tests"])
    success = True
    
    for file_path in target_files:
        if not self._check_single_file(file_path):
            success = False
    
    spinner.stop(success)
    return success
```

### フェーズ4: テストと統合

#### 4.1 互換性テスト
- 既存のテストスイートで動作確認
- `scripts/test.py`での統合テスト

#### 4.2 設定の動的変更テスト
- scriptsディレクトリの追加/削除
- 除外パターンの変更

## 実装スケジュール

### Week 1: 設定基盤構築
- [ ] `src/configuration/quality_checks.json`作成
- [ ] `QualityConfigLoader`実装
- [ ] 設定読み込みテスト

### Week 2: 共通基底クラス構築
- [ ] `BaseQualityChecker`実装
- [ ] `ProgressSpinner`共通化
- [ ] 基底クラステスト

### Week 3: 高優先度チェッカーリファクタリング
- [ ] `syntax_checker.py`リファクタリング
- [ ] `type_checker.py`リファクタリング
- [ ] `ruff_checker.py`リファクタリング

### Week 4: 残りのチェッカーリファクタリング
- [ ] 中優先度チェッカー対応
- [ ] 低優先度チェッカー対応
- [ ] 統合テスト

## リスク管理

### 既知のリスク
1. **互換性の破綻**: 既存のAPIや動作の変更
2. **設定ファイルの不備**: 必要な設定項目の不足
3. **パフォーマンス劣化**: ファイル検索の最適化不足

### 軽減策
1. **段階的移行**: 一度に全てを変更せず、フェーズごとに確認
2. **互換性テスト**: 各フェーズで既存機能の動作確認
3. **ロールバック計画**: 問題発生時の復旧手順明文化

## 完了基準

- [ ] 全品質チェッカーがscriptsディレクトリを検証対象に含められる
- [ ] ハードコードされたパス指定が全て除去される
- [ ] 設定ファイルで柔軟な設定変更が可能になる
- [ ] ProgressSpinnerの重複が解消される
- [ ] CLAUDE.mdの指針に完全準拠する
- [ ] 既存テストが全て通過する
- [ ] パフォーマンスが劣化しない

## 注意事項

- 設定ファイルの編集は明示された場合のみ許可（CLAUDE.md準拠）
- フォールバック処理は禁止、必要なエラーを見逃さない
- 互換性維持のコメントを必ず追記
- デフォルト値の使用は厳禁