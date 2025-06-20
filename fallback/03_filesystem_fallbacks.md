# ファイルシステム関連フォールバック処理修正タスク

## 概要
ファイルシステム操作関連で検出された4つのフォールバック処理を適切なエラーハンドリングまたは設定ベースの実装に置き換える。

## 対象ファイルと修正箇所

### 1. infrastructure/drivers/filesystem/local_filesystem.py:28
- **パターン**: try-except でのフォールバック return
- **優先度**: 高（コアファイル操作）
- **推定修正方法**: 明示的な例外処理とエラー報告

### 2. infrastructure/drivers/filesystem/path_operations.py:85
- **パターン**: None チェックでのフォールバック
- **優先度**: 高
- **推定修正方法**: 設定からデフォルトパスを取得

### 3. infrastructure/drivers/filesystem/path_operations.py:240
- **パターン**: try-except でのフォールバック代入
- **優先度**: 中
- **推定修正方法**: 明示的な例外処理

### 4. infrastructure/drivers/filesystem/path_operations.py:42
- **パターン**: 条件式でのフォールバック (else節)
- **優先度**: 中
- **推定修正方法**: 設定ベースのパス解決

## 関連設定ファイル

### 既存設定（参考）
- `contest_env/shared/env.json` - パス設定
  - `contest_current_path`
  - `contest_stock_path`
  - `local_workspace_path`

### 追加が必要な設定（想定）
```json
{
  "filesystem_config": {
    "default_paths": {
      "workspace": "./workspace",
      "temp": "./temp", 
      "cache": "./.cache"
    },
    "path_resolution": {
      "resolve_relative": true,
      "create_missing_dirs": false,
      "validate_permissions": true
    },
    "error_handling": {
      "missing_file_action": "error",
      "permission_denied_action": "error",
      "disk_full_action": "error"
    },
    "defaults": {
      "file_mode": "0644",
      "dir_mode": "0755",
      "encoding": "utf-8"
    }
  }
}
```

## 修正アプローチ

1. **パス解決の明確化**
   - 相対パス・絶対パスの処理を設定ベースに
   - デフォルトディレクトリの設定化

2. **エラーハンドリング強化**
   - ファイル不存在時の明示的エラー
   - 権限エラーの適切な処理
   - ディスク容量不足の検出

3. **設定統合**
   - TypeSafeConfigNodeManagerによる統一管理
   - パス設定の集約化

## 典型的な修正パターン

### Before (フォールバック)
```python
# None チェックでのフォールバック
if path is None:
    path = "./default"

# try-except でのフォールバック
try:
    result = operation()
except Exception:
    result = fallback_value
```

### After (設定ベース)
```python
# 設定からの明示的取得
if path is None:
    try:
        path = self.config_manager.resolve_config(['filesystem_config', 'default_paths', 'workspace'], str)
    except KeyError:
        raise ValueError("No default workspace path configured")

# 明示的な例外処理
try:
    result = operation()
except SpecificException as e:
    raise FileSystemError(f"Operation failed: {e}") from e
```

## セキュリティ考慮事項

- **パストラバーサル対策**: `../`による上位ディレクトリアクセス防止
- **権限チェック**: ファイル作成・削除前の権限確認
- **サンドボックス**: 許可されたディレクトリ内での操作制限

## テスト戦略

1. **正常ケース**
   - 各パス操作の成功パターン
   - 設定値の正常取得

2. **異常ケース**
   - ファイル不存在
   - 権限不足
   - ディスク容量不足
   - 設定値不正

3. **エッジケース**
   - 空のパス文字列
   - 非常に長いパス
   - 特殊文字を含むパス

## 完了条件

- [ ] 4つのフォールバック処理をすべて修正
- [ ] ファイル操作が正常に動作することを確認
- [ ] セキュリティテストが全て通過
- [ ] 関連テストが全て通過
- [ ] 設定ファイル`filesystem_config.json`が追加されている
- [ ] パストラバーサル攻撃に対する防御が確認されている