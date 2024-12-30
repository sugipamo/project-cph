# メモリ制限の問題点と確認事項

## 設定ファイル関連
1. `src/config/docker.yaml`
   - デフォルトのメモリ制限が512MBに設定されている
   - テスト時の値との整合性を確認する必要あり

## Docker設定関連
1. `src/docker/runner/container.rs`の設定
   ```rust
   memory: Some(self.config.memory_limit_mb * 1024 * 1024),
   memory_swap: Some(self.config.memory_limit_mb * 1024 * 1024),
   memory_swappiness: Some(0),
   kernel_memory: Some(self.config.memory_limit_mb * 1024 * 1024),
   ```
   - `memory_swap`が`memory`と同じ値に設定されている（スワップ領域が実質無効になっていない）
   - `kernel_memory`の設定が必要かどうか検討（非推奨の可能性あり）
   - メモリ制限の単位変換（MB→バイト）の処理が複数箇所に散在

2. `src/docker/runner/command.rs`の設定
   ```rust
   .arg(format!("-m={}m", memory_limit))
   ```
   - Dockerコマンドでのメモリ制限の設定方法を確認

## テスト関連
1. `tests/docker/runner_test.rs`のメモリ制限テスト
   - Pythonのメモリ確保処理が適切か確認
   - `MemoryError`の捕捉が適切か確認
   - 終了コード137（OOM Killer）の検出が適切か確認

## 改善案
1. メモリ制限の設定を一元化
   - 単位変換の処理を1箇所にまとめる
   - 設定値の検証を追加

2. Dockerのメモリ制限設定の見直し
   - `memory_swap`を0または-1に設定してスワップを完全に無効化
   - 非推奨のオプションを削除または更新

3. テストケースの改善
   - より確実なメモリ制限テストの実装
   - エラー検出条件の明確化 