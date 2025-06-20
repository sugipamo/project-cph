# Docker関連フォールバック処理修正タスク

## 概要
Docker関連ドライバーで検出されたフォールバック処理を適切なエラーハンドリングまたは設定ベースの実装に置き換える。

## 対象ファイルと修正箇所

### 1. infrastructure/drivers/docker/docker_driver.py:151
- **パターン**: or演算子でのフォールバック
- **優先度**: 高
- **推定修正方法**: 設定ファイルからデフォルト値を取得

### 2. infrastructure/drivers/docker/utils/docker_command_builder.py:30
- **パターン**: try-except でのフォールバック return
- **優先度**: 高  
- **推定修正方法**: 明示的な例外処理とエラー報告

### 3. infrastructure/drivers/docker/utils/docker_utils.py:73
- **パターン**: or演算子でのフォールバック
- **優先度**: 中
- **推定修正方法**: 設定システムからの値取得

### 4. infrastructure/drivers/docker/utils/docker_utils.py:67
- **パターン**: 条件式でのフォールバック (else節)
- **優先度**: 中
- **推定修正方法**: 明示的な条件チェックと例外処理

## 関連設定ファイル

### 既存設定
- `config/system/docker_defaults.json` - Docker関連のデフォルト設定
- `config/system/docker_security.json` - Dockerセキュリティ設定

### 追加が必要な設定（想定）
```json
{
  "docker_fallback_config": {
    "default_timeout": 300,
    "default_memory_limit": "1g",
    "default_working_dir": "/workspace",
    "error_handling": {
      "retry_attempts": 3,
      "retry_delay": 1.0
    }
  }
}
```

## 修正アプローチ

1. **設定システム統合**
   - TypeSafeConfigNodeManagerを使用
   - 必要な設定値を設定ファイルから取得

2. **エラーハンドリング強化**  
   - 明示的な例外処理
   - 適切なエラーメッセージ
   - ログ出力の改善

3. **テスト対応**
   - 既存テストの修正
   - 新しいエラーケースのテスト追加

## 注意事項

- `main.py`からの依存性注入パターンを維持
- Docker関連の設定は既存の`docker_defaults.json`を拡張
- 互換性維持のためのコメント追加を忘れずに
- 副作用は`src/infrastructure`内のみに限定

## 完了条件

- [ ] 4つのフォールバック処理をすべて修正
- [ ] 関連テストが全て通過
- [ ] Ruffのコード品質チェックが通過
- [ ] 設定ファイルが適切に追加/更新されている