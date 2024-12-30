# エラー調査報告

## 発生しているエラー
- ファイル: `tests/docker/runner_test.rs` の135行目
- エラー内容: `RunnerConfig::new()` 関数に必要な引数が不足している
- エラーコード: E0061

## 原因
1. `RunnerConfig::new()` 関数は3つの引数を必要とします：
   - timeout: u64
   - memory_limit: u64
   - mount_point: String

2. テストコードでは2つの引数のみを渡しています：
   ```rust
   RunnerConfig::new(docker_config.timeout_seconds, docker_config.memory_limit_mb)
   ```

3. 必須の第3引数 `mount_point: String` が欠落しています。

## 解決方法
以下のいずれかの方法で解決可能です：

1. `RunnerConfig::new()` の呼び出し時に `mount_point` パラメータを追加する
   ```rust
   RunnerConfig::new(docker_config.timeout_seconds, docker_config.memory_limit_mb, mount_point)
   ```

2. `DockerConfig` 構造体に `mount_point` フィールドを追加し、設定ファイルから読み込むようにする

## 次のステップ
1. `DockerConfig` の構造を確認し、`mount_point` の追加が必要かどうかを検討
2. テストケースの修正
3. 他のテストケースでも同様の問題が発生していないか確認
