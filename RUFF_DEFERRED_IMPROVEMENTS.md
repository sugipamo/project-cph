# Ruff品質改善 - 保留項目

開発効率に影響する可能性があるため、一旦保留とするruff警告の改善項目をまとめます。

## 修正完了項目

### ✅ フェーズ1完了済み
- **E722**: bare except → Exception
- **E741**: 曖昧な変数名の修正
- **F821**: 未定義名の修正
- **B027**: 抽象メソッドデコレータ → 設定で無効化（適切な判断）

## 保留項目一覧

### 1. B904: Exception Chaining Issues
**影響度**: 中程度 - 例外処理のベストプラクティス改善

#### 対象ファイル
- `src/context/utils/validation_utils.py:79`
- `src/domain/requests/file/file_request.py:117`
- `src/utils/path_operations.py:165,204,266,310,410,461`
- `src/workflow/step/core.py:57`
- その他複数ファイル

#### 修正例
```python
# 現在
except Exception as e:
    raise ValueError(f"Error: {e}")

# 推奨
except Exception as e:
    raise ValueError(f"Error: {e}") from e
```

#### 保留理由
- 既存のエラーハンドリングロジックへの影響が大きい
- テストケースの見直しが必要
- 段階的な移行が必要

### 2. SIM102/SIM117: Conditional Simplification
**影響度**: 低 - コード簡素化の提案

#### 対象例
```python
# SIM102: Nested if statements
if condition1:
    if condition2:
        do_something()

# 推奨
if condition1 and condition2:
    do_something()
```

#### 保留理由
- 可読性に関わる主観的な判断
- 既存のロジック構造を変更するリスク
- 機能に影響しない

### 3. B027: Abstract Base Class Issues
**影響度**: 中程度 - 抽象クラス設計の改善

#### 対象ファイル
- `src/infrastructure/drivers/base/base_driver.py:32,35`

#### 修正例
```python
# 現在
def initialize(self) -> None:
    """Initialize the driver. Override if needed."""

# 推奨
@abstractmethod
def initialize(self) -> None:
    """Initialize the driver. Override if needed."""
```

#### 保留理由
- 継承クラスの実装確認が必要
- インターフェース変更の影響調査が必要

### 4. B017: Assert Exception Type
**影響度**: 低 - テストコードの品質改善

#### 対象ファイル
- 複数のテストファイル

#### 修正例
```python
# 現在
with pytest.raises(Exception):
    some_function()

# 推奨
with pytest.raises(SpecificException):
    some_function()
```

#### 保留理由
- テストの意図を正確に把握する必要
- 例外型の仕様確認が必要

### 5. F403: Star Import Issues
**影響度**: 中程度 - インポート構造の改善

#### 対象ファイル
- `src/infrastructure/drivers/docker/utils/__init__.py:39`

#### 修正例
```python
# 現在
from .docker_utils import *

# 推奨
from .docker_utils import specific_function1, specific_function2
```

#### 保留理由
- 公開APIの整理が必要
- 下位互換性への影響確認が必要

## 改善計画

### フェーズ1: 簡単な修正（完了済み）
- ✅ E722: bare except → Exception
- ✅ E741: 曖昧な変数名の修正
- ✅ F821: 未定義名の修正

### フェーズ2: 中程度の修正（今後）
- B904: Exception chaining
- B027: Abstract method decorators
- F403: Star imports

### フェーズ3: 複雑な修正（リファクタリング時）
- SIM102/SIM117: Code simplification
- B017: Test exception types

## 注意事項

1. **開発効率優先**: 機能開発を優先し、品質改善は段階的に実施
2. **テスト必須**: 修正時は必ず関連テストを実行
3. **影響範囲確認**: 変更による副作用を慎重に確認
4. **文書更新**: 修正後はこの文書を更新

## 設定調整の検討

必要に応じて以下のルールを一時的に無視することも検討：

```toml
# pyproject.toml
ignore = [
    # ... 既存設定 ...
    "B904",    # Exception chaining (段階的導入)
    "SIM102",  # Nested if simplification (可読性優先)
    "SIM117",  # Nested with simplification (可読性優先)
    "B017",    # Assert exception type in tests (テスト改善時)
]
```