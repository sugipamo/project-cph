# フォールバック処理修正プロジェクト概要

## プロジェクト目標

CLAUDE.mdで禁止されているフォールバック処理を適切なエラーハンドリングまたは設定ベースの実装に置き換え、エラー隠蔽を防止してコードの信頼性を向上させる。

## 全体統計

- **総検出数**: 149件以上のフォールバック処理
- **表示済み**: 20件（詳細リスト化済み）
- **残り**: 129件以上（"他126件"として未詳細化）

## 分類別修正タスク

### 1. Docker関連 (4件) - `01_docker_fallbacks.md`
- **優先度**: 高
- **主要ファイル**: docker_driver.py, docker_command_builder.py, docker_utils.py
- **修正方法**: Docker設定の集約、明示的例外処理

### 2. ログ関連 (9件) - `02_logging_fallbacks.md`  
- **優先度**: 高
- **主要ファイル**: unified_logger.py, application_logger_adapter.py, workflow_logger_adapter.py
- **修正方法**: ログ設定の統一、アダプターパターン改善

### 3. ファイルシステム関連 (4件) - `03_filesystem_fallbacks.md`
- **優先度**: 高  
- **主要ファイル**: local_filesystem.py, path_operations.py
- **修正方法**: パス設定の明確化、セキュリティ強化

### 4. Python Utils関連 (2件) - `04_python_utils_fallbacks.md`
- **優先度**: 高
- **主要ファイル**: python_utils.py
- **修正方法**: Python環境設定、インタープリター検出改善

### 5. パターン関連 (1件) - `05_patterns_fallbacks.md`
- **優先度**: 中
- **主要ファイル**: retry_decorator.py  
- **修正方法**: 再試行ポリシーの設定化

### 6. 未分類 (129件以上)
- **優先度**: 分析後決定
- **状況**: まだ詳細リスト化されていない
- **対応**: 追加分析が必要

## 全体的な修正戦略

### 1. 設定システム統合
```json
// 各モジュール用の設定ファイル追加
config/system/
├── docker_config.json
├── logging_config.json  
├── filesystem_config.json
├── python_config.json
└── retry_config.json
```

### 2. 統一的なエラーハンドリング
- TypeSafeConfigNodeManagerによる設定管理
- 明示的な例外処理
- 適切なエラーメッセージ

### 3. 段階的な実装
1. **フェーズ1**: 高優先度20件の修正
2. **フェーズ2**: 残り129件の分析と分類
3. **フェーズ3**: 残り全件の修正

## 共通修正パターン

### Before (フォールバック)
```python
# or演算子フォールバック
value = config.get('key') or 'default'

# try-except フォールバック
try:
    result = risky_operation()
except Exception:
    result = fallback_value

# 条件式フォールバック  
result = value if condition else fallback_value
```

### After (設定ベース)
```python
# 設定からの明示的取得
try:
    value = self.config_manager.resolve_config(['module', 'key'], str)
except KeyError:
    raise ConfigurationError("Required configuration 'module.key' not found")

# 明示的例外処理
try:
    result = risky_operation()
except SpecificException as e:
    raise OperationError(f"Operation failed: {e}") from e

# 明示的条件処理
if not condition:
    raise ValueError("Required condition not met")
result = value
```

## プロジェクト進捗追跡

### 完了済み (4件)
- [x] environment_manager.py:20 (or演算子)
- [x] environment_manager.py:75 (or演算子) 
- [x] unified_driver.py:221 (条件式)
- [x] scripts/test.py (ruffエラー修正)

### 作業中
- [ ] Docker関連 (4件)
- [ ] ログ関連 (9件)  
- [ ] ファイルシステム関連 (4件)
- [ ] Python Utils関連 (2件)
- [ ] パターン関連 (1件)

### 未着手
- [ ] 残り129件の分析
- [ ] 分類作業
- [ ] 修正実装

## 成功指標

1. **機能面**
   - [ ] 全フォールバック処理の除去
   - [ ] テストの全通過
   - [ ] 機能性の維持

2. **品質面**  
   - [ ] Ruffチェックの全通過
   - [ ] エラーメッセージの改善
   - [ ] デバッグ可能性の向上

3. **保守性面**
   - [ ] 設定の集約化
   - [ ] コードの可読性向上
   - [ ] ドキュメント整備

## 注意事項

- **互換性維持**: 既存APIの変更は最小限に
- **副作用制限**: `src/infrastructure` と `tests/infrastructure` のみ
- **依存性注入**: `main.py`からの注入パターン維持
- **設定ユーザー編集**: 明示的指示がある場合のみ