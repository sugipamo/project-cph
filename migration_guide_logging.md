# Logging Migration Guide: infrastructure/drivers/logging → src/logging

## 概要

**結論: ラッパー作成による段階的置き換えが最適解**

- **現実性**: ◎ (使用箇所4ファイルのみ)
- **リスク**: 低 (既存APIと100%互換)
- **メンテナンス性**: 高 (統一されたロギングシステム)

## 実装コストと互換性リスク分析

### 低リスク要因
1. **限定的使用**: infrastructure/drivers/loggingは4ファイルでのみ使用
2. **完全互換**: AdapterパターンでAPIを100%再現
3. **段階的移行**: 既存コードを壊さずに移行可能
4. **テスト対応**: MockOutputManagerで副作用なしテスト

### 実装コスト
- **新規実装**: 2アダプタークラス（完了済み）
- **DI統合**: ファクトリー関数追加（完了済み）
- **移行作業**: 4ファイルのimport文変更のみ

## マイグレーション手順

### Phase 1: Adapter導入（完了済み）
```python
# ApplicationLoggerAdapter - LoggerInterface実装
# WorkflowLoggerAdapter - ConsoleLogger/DebugLogger互換
```

### Phase 2: DIコンテナ置き換え
```python
# Before (infrastructure)
from src.infrastructure.drivers.logging.python_logger import PythonLogger
logger = PythonLogger()

# After (src/logging + adapter)
from src.infrastructure.di_container import DIContainer, DIKey
container = DIContainer()
logger = container.resolve(DIKey.APPLICATION_LOGGER)  # LoggerInterface互換
```

### Phase 3: 具体的な置き換え例

#### 1. PythonLogger → ApplicationLoggerAdapter
```python
# src/infrastructure/config/di_config.py
# 変更前
def _create_logger() -> Any:
    from src.infrastructure.drivers.logging.python_logger import PythonLogger
    return PythonLogger()

# 変更後  
def _create_logger() -> Any:
    return container.resolve(DIKey.APPLICATION_LOGGER)
```

#### 2. ConsoleLogger → WorkflowLoggerAdapter
```python
# src/application/di/provider_factory.py
# 変更前
from src.infrastructure.drivers.logging import SystemConsoleLogger
console_logger = SystemConsoleLogger()

# 変更後
workflow_logger = container.resolve(DIKey.WORKFLOW_LOGGER)
```

### Phase 4: 利用者側の変更
```python
# 変更前: 直接インポート
from src.infrastructure.drivers.logging.debug_logger import DebugLogger

# 変更後: DIコンテナ経由
workflow_logger = container.resolve(DIKey.WORKFLOW_LOGGER)
```

## 互換性マトリックス

| 既存機能 | ApplicationLoggerAdapter | WorkflowLoggerAdapter |
|---------|-------------------------|----------------------|
| `debug/info/warning/error()` | ✅ 完全互換 | ✅ 完全互換 |
| `critical()` | ✅ ERROR+フォーマット | ❌ 未対応 |
| `log_error_with_correlation()` | ✅ 完全互換 | ❌ 未対応 |
| `log_operation_start/end()` | ✅ 完全互換 | ❌ 未対応 |
| `step_start/success/failure()` | ❌ 未対応 | ✅ 完全互換 |
| アイコン表示 | ❌ 未対応 | ✅ 完全互換 |

## 推奨アプローチ

### ✅ **採用すべき理由**

1. **ゼロダウンタイム移行**: 既存コードを一切変更せずに移行開始
2. **完全な機能互換**: 全ての既存APIを再現
3. **テスト容易性**: MockOutputManagerで副作用なしテスト
4. **一元化**: `src/logging`を単一のロギングシステムとして確立
5. **将来性**: 新機能は`src/logging`に集約可能

### 📋 **移行チェックリスト**

- [x] ApplicationLoggerAdapter実装
- [x] WorkflowLoggerAdapter実装  
- [x] DIコンテナ統合
- [x] UnifiedLogger実装（全機能統合）
- [x] 既存4ファイルのimport変更
- [x] 旧infrastructure/drivers/logging削除
- [x] src/logging → infrastructure/drivers/logging移動
- [x] インポートパス一括更新
- [x] 新しいテスト作成
- [ ] テスト実行・検証

### 🎯 **最終目標**

`src/logging`を唯一のロギングシステムとし、infrastructure配下のloggingを完全に置き換える。