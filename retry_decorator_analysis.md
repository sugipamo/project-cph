# retry_decorator.py 修正作業の状況まとめ

## 作業概要
scripts/test.py の失敗テストの分析と修正を行い、特に retry_decorator.py に関連する問題を解決する作業を実施。

## 実施した修正内容

### 1. CLAUDE.mdルール準拠の修正
- **デフォルト値の削除**: `RetryConfig`、`retry_on_failure_with_result`、`retry_on_failure`、`RetryableOperation` のデフォルト値を削除
- **必須パラメータ化**: 呼び出し元で適切な値を用意することを徹底

### 2. Ruffコード品質チェックの修正
- **SIM103エラー**: `_determine_retry_eligibility`関数で条件を直接返すように修正
- **到達不可能コード**: 不要なバリデーションコードを削除

### 3. try文禁止への対応試行
- **最初のアプローチ**: sys.excepthookを使った複雑な実装を試行したが、過度に複雑
- **第二のアプローチ**: Result型ベースの実装に変更し、互換性を維持
- **現在の状況**: 例外を投げる既存テストとの互換性問題が発生

## 現在の問題

### テスト失敗の原因
`retry_on_failure`デコレータのテストで、Mock関数が例外を投げるテストケースが失敗：
```python
mock_func.side_effect = [ConnectionError("fail"), ConnectionError("fail"), "success"]
```

### try文禁止の制約
- CLAUDE.mdで「フォールバック処理は禁止」「try文を一律禁止」の方針
- しかし、例外を投げる関数のリトライ機能は例外処理が不可欠
- infrastructureレイヤーでは必要な例外処理の許可が必要

## 技術的ジレンマ

### 矛盾する要求
1. **互換性維持**: 既存の例外ベースAPIとの互換性を保つ必要
2. **try文禁止**: 例外処理を使わない実装を求められる
3. **テスト合格**: 例外を投げるテストケースを通す必要

### 現在の実装の問題点
```python
@retry_on_failure(config)
def test_func():
    return mock_func()  # これが例外を投げる
```
- mock_func()がConnectionErrorを投げるため、Result型でのラップが困難
- try-except文なしに例外をキャッチしてResultに変換する方法が必要

## 検討された解決策

### 1. 完全廃止案
- `retry_on_failure`を削除し、`retry_on_failure_with_result`のみ使用
- **問題**: 既存テストとの互換性が失われる

### 2. 関数契約変更案
- デコレート対象の関数がResult型を返すよう要求
- **問題**: 既存のテストコードが例外ベースで実装されている

### 3. infrastructureレイヤー例外許可案
- CLAUDE.mdの「副作用はsrc/infrastructure のみ」ルールを活用
- infrastructureレイヤーでのみ必要最小限の例外処理を許可
- **利点**: 実用性と方針の両立が可能

## 推奨される次のステップ

### 短期的解決策
1. infrastructureレイヤーでの例外処理を明示的に許可
2. 例外処理箇所に明確なコメントを追加
3. テストの互換性を維持

### 長期的方針
1. 新規コードは`retry_on_failure_with_result`を使用
2. `retry_on_failure`をDEPRECATEDとしてマーク
3. 段階的に例外ベースAPIからResult型APIへ移行

## 現在のコード状態
- retry_decorator.pyの修正は部分的に完了
- Ruffチェックは合格
- retry_decoratorのテストは一部失敗（例外処理関連）
- CLAUDE.mdルール違反（None引数初期値）は解決済み

## 結論
try文の完全禁止は理想的だが、既存の例外ベースAPIとの互換性維持のため、infrastructureレイヤーでの制限された例外処理が現実的な解決策となる。