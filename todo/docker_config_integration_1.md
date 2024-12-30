# DockerConfig構造体とRunnerConfig構造体の統合

## 現状
- `RunnerConfig`と`DockerConfig`は同じフィールドを持つ重複した構造体として存在
- `RunnerConfig`はDockerRunnerの実行設定として使用
- `DockerConfig`は設定ファイルからの読み込み用として使用

## 問題点
1. 同じ目的の構造体が重複して存在
2. コードの保守性が低下
3. 設定の一貫性が保証されない可能性

## 解決方針
1. `DockerConfig`に`RunnerConfig`の機能を統合
   - `new()`と`default()`メソッドの追加
   - 既存の`from_yaml()`メソッドの維持
2. 全ての`RunnerConfig`の参照を`DockerConfig`に置き換え
3. `RunnerConfig`構造体の削除

## 影響範囲
- src/docker/config.rs
- src/docker/runner/mod.rs
- src/docker/runners/mod.rs
- その他の関連ファイル

## 実装手順
1. `DockerConfig`に必要なメソッドを追加
2. `RunnerConfig`の使用箇所を`DockerConfig`に置き換え
3. `RunnerConfig`構造体を削除

## リスク
- 既存のコードへの影響
- 設定ファイルの互換性
- テストの必要性

## タイムライン
1. コードの変更（約30分）
2. テスト（約15分）
3. レビュー（約15分）

## 次のステップ
1. `DockerConfig`の拡張
2. 既存コードの更新
3. テストの実行 