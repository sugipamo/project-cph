# ログ関連フォールバック処理修正タスク

## 概要
ログシステム関連で検出された9つのフォールバック処理を適切なエラーハンドリングまたは設定ベースの実装に置き換える。

## 対象ファイルと修正箇所

### 1. infrastructure/drivers/logging/unified_logger.py
- **Line 43**: or演算子でのフォールバック
- **Line 156**: 条件式でのフォールバック (else節)
- **Line 162**: 条件式でのフォールバック (else節)  
- **Line 258**: 条件式でのフォールバック (else節)
- **優先度**: 高（コアログシステム）

### 2. infrastructure/drivers/logging/adapters/application_logger_adapter.py
- **Line 105**: 条件式でのフォールバック (else節)
- **Line 111**: 条件式でのフォールバック (else節)
- **優先度**: 中

### 3. infrastructure/drivers/logging/adapters/workflow_logger_adapter.py
- **Line 34**: or演算子でのフォールバック
- **Line 167**: 条件式でのフォールバック (else節)
- **優先度**: 中

### 4. infrastructure/drivers/logging/mock_output_manager.py
- **Line 36**: 条件式でのフォールバック (else節)
- **優先度**: 低（テスト用）

## 関連設定ファイル

### 既存設定（参考）
- `config/system/dev_config.json` - デバッグ設定
- `contest_env/shared/env.json` - 出力フォーマット設定

### 追加が必要な設定（想定）
```json
{
  "logging_config": {
    "default_level": "INFO",
    "default_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "default_handlers": ["console"],
    "fallback_behavior": {
      "unknown_level": "INFO",
      "missing_formatter": "simple",
      "missing_handler": "console"
    },
    "adapters": {
      "application": {
        "default_prefix": "[APP]",
        "default_context": "main"
      },
      "workflow": {
        "default_prefix": "[WORKFLOW]",
        "default_context": "execution"
      }
    }
  }
}
```

## 修正アプローチ

1. **ログ設定の統一**
   - 中央集約型のログ設定システム
   - TypeSafeConfigNodeManagerによる設定管理

2. **アダプターパターンの改善**
   - 明示的なデフォルト値の設定取得
   - フォールバック処理の除去

3. **エラーハンドリング強化**
   - ログレベル不正値の適切な処理
   - フォーマッター不在時の明示的エラー

4. **モック対応**
   - テスト用モックでも設定ベースの動作

## 技術的考慮事項

- **パフォーマンス**: ログは頻繁に呼ばれるため設定キャッシュが重要
- **循環依存**: ログシステムが設定システムに依存する場合の注意
- **初期化順序**: DIコンテナでの適切な初期化順序の確保

## 修正パターン例

### Before (フォールバック)
```python
log_level = config.get('level') or 'INFO'
formatter = self.formatter if self.formatter else default_formatter
```

### After (設定ベース)
```python
try:
    log_level = self.config_manager.resolve_config(['logging_config', 'default_level'], str)
except KeyError:
    raise ValueError("Log level not configured")

if not hasattr(self, 'formatter') or self.formatter is None:
    raise ValueError("Formatter not properly initialized")
```

## 完了条件

- [ ] 9つのフォールバック処理をすべて修正
- [ ] ログ出力が正常に動作することを確認
- [ ] 関連テストが全て通過
- [ ] パフォーマンステストでリグレッションがない
- [ ] 設定ファイル`logging_config.json`が追加されている