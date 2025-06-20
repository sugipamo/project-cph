# パターン/再試行関連フォールバック処理修正タスク

## 概要
リトライパターン実装で検出された1つのフォールバック処理を適切なエラーハンドリングに置き換える。

## 対象ファイルと修正箇所

### 1. infrastructure/patterns/retry_decorator.py:65
- **パターン**: try-except でのフォールバック代入
- **優先度**: 中
- **詳細**: `should_retry = False` のフォールバック代入
- **推定修正方法**: 明示的な再試行判定ロジック

## コンテキスト分析

このファイルは汎用的なリトライデコレータを実装しており、以下の責務を持つ：
- 例外に基づく再試行判定
- 再試行回数の制御
- 再試行間隔の制御
- 最終的な例外の報告

Line 65の `should_retry = False` は、再試行すべきかどうかの初期値設定に見えるが、フォールバック処理として検出されている可能性がある。

## 関連設定ファイル

### 既存設定（参考）
- `contest_env/shared/env.json` - retry_settings
  ```json
  "retry_settings": {
    "max_attempts": 3,
    "base_delay_seconds": 1.0,
    "max_delay_seconds": 30.0
  }
  ```

### 追加が必要な設定（想定）
```json
{
  "retry_config": {
    "default_policy": {
      "max_attempts": 3,
      "base_delay": 1.0,
      "max_delay": 30.0,
      "backoff_multiplier": 2.0,
      "jitter": true
    },
    "error_classification": {
      "retryable_exceptions": [
        "ConnectionError",
        "TimeoutError", 
        "TemporaryFailure"
      ],
      "non_retryable_exceptions": [
        "AuthenticationError",
        "PermissionError",
        "ValidationError"
      ]
    },
    "policies": {
      "network": {
        "max_attempts": 5,
        "base_delay": 0.5,
        "max_delay": 60.0
      },
      "file_io": {
        "max_attempts": 2,
        "base_delay": 0.1,
        "max_delay": 5.0
      },
      "database": {
        "max_attempts": 3,
        "base_delay": 1.0,
        "max_delay": 30.0
      }
    }
  }
}
```

## 修正アプローチ

1. **明示的な判定ロジック**
   - フォールバック代入を明示的な条件判定に変更
   - 設定ベースの再試行ポリシー適用

2. **例外分類の改善**
   - 再試行可能/不可能例外の明確な分類
   - 設定ファイルベースの例外マッピング

3. **設定統合**
   - TypeSafeConfigNodeManagerによる設定管理
   - ポリシーベースの再試行制御

## 修正パターン例

### Before (推定されるフォールバック)
```python
try:
    # 何かの判定処理
    should_retry = determine_retry_logic()
except Exception:
    should_retry = False  # フォールバック代入
```

### After (明示的処理)
```python
# 明示的な再試行判定
should_retry = self._determine_retry_eligibility(
    exception=e,
    attempt_count=attempt,
    policy=retry_policy
)

def _determine_retry_eligibility(self, exception, attempt_count, policy):
    """明示的な再試行判定ロジック"""
    # 最大試行回数チェック
    if attempt_count >= policy.max_attempts:
        return False
    
    # 例外タイプによる判定
    exception_name = type(exception).__name__
    
    # 設定から再試行可能例外を取得
    try:
        retryable_exceptions = self.config_manager.resolve_config(
            ['retry_config', 'error_classification', 'retryable_exceptions'], 
            list
        )
        return exception_name in retryable_exceptions
    except KeyError:
        raise ConfigurationError("Retry policy not properly configured") from None
```

## エラーハンドリング戦略

1. **段階的エラー処理**
   - 一時的エラー vs 永続的エラー
   - 復旧可能エラー vs 復旧不可能エラー

2. **コンテキスト保持**
   - 再試行履歴の記録
   - 各試行での例外情報保持

3. **リソース管理**
   - 長時間の再試行による無限ループ防止
   - メモリリーク防止

## テスト戦略

1. **再試行動作テスト**
   - 成功するまでの再試行
   - 最大試行回数での停止
   - 再試行間隔の確認

2. **例外分類テスト**
   - 再試行可能例外での動作
   - 再試行不可能例外での即時停止

3. **設定テスト**
   - 様々な再試行ポリシーでの動作
   - 設定不正時のエラーハンドリング

## 完了条件

- [x] フォールバック代入を明示的判定ロジックに置き換え
- [x] 設定ベースの再試行ポリシー実装
- [x] 例外分類システムの実装
- [x] 再試行動作のテストが全て通過
- [x] 設定ファイル`retry_config.json`が追加されている
- [x] 無限ループ防止機能が動作することを確認

## 実装完了報告

**修正日時**: 2025-06-20
**担当者**: Claude Code

### 実装内容

1. **フォールバック代入の除去**
   - `src/infrastructure/patterns/retry_decorator.py:65`の`should_retry = False`を削除
   - 明示的な判定ロジック`_determine_retry_eligibility()`関数を実装

2. **設定ファイルの追加**
   - `config/system/retry_config.json`を作成
   - 汎用的なリトライポリシーと例外分類を定義

3. **エラーハンドリングの改善**
   - 設定の妥当性検証を追加
   - 不正な設定に対する適切な例外処理

4. **テスト検証**
   - 既存の13個のテストが全て通過
   - 新しい明示的判定ロジックの動作確認完了

### 技術的改善点

- **フォールバック処理の根絶**: 意図しない値の代入を防止
- **明示的なエラーハンドリング**: 設定不備時の適切な例外発生
- **型安全性の向上**: 設定検証による実行時エラーの防止

### 互換性維持

既存のAPIに変更なし、すべての既存コードがそのまま動作します。