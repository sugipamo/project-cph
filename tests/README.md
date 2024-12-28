# テストの実行方法

## 基本的なテストコマンド

1. すべてのテストを実行（Docker関連のテストを除く）：
```bash
cargo test
```

2. Docker関連のテストを含むすべてのテストを実行：
```bash
cargo test --features docker_test
```

3. Docker関連のテストのみを実行：
```bash
cargo test --features docker_test docker::
```

4. 特定のテストを実行：
```bash
# 設定テスト
cargo test --features docker_test docker::config_test::

# ランナーテスト
cargo test --features docker_test docker::runner_test::

# コンテナテスト
cargo test --features docker_test docker::container_test::

# 入出力テスト
cargo test --features docker_test docker::io_test::
```

## オプション

- テスト出力を詳細に表示（--nocapture）：
```bash
cargo test --features docker_test -- --nocapture
```

- 特定のテストのみを実行（テスト名を指定）：
```bash
cargo test --features docker_test docker::config_test::test_load_config
```

- テストを並列実行しない（--test-threads=1）：
```bash
cargo test --features docker_test -- --test-threads=1
```

## 注意事項

1. Docker関連のテストを実行する場合は、以下の条件が必要です：
   - Dockerデーモンが実行されていること
   - 必要なDockerイメージがプルされていること（初回実行時は時間がかかります）
   - 十分なディスク容量があること

2. メモリ制限のテストは、システムリソースに影響を与える可能性があります。

3. タイムアウトテストは、設定された時間（デフォルト5秒）の待機が必要です。 