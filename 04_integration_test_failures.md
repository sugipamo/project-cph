# 統合テスト関連のテスト失敗

## 概要
引数のデフォルト値禁止ルールに従った実装変更により、Docker命名ユーティリティとリトライデコレータのテストが失敗しています。

## 現在の失敗状況

### DockerNamingUtils関連 (4件失敗 / 19件中)
**失敗テスト:**
- `test_image_name_without_dockerfile` - `dockerfile_text`引数が必須
- `test_container_name_without_dockerfile` - `dockerfile_text`引数が必須
- `test_oj_image_name_without_dockerfile` - `oj_dockerfile_text`引数が必須
- `test_oj_container_name_without_dockerfile` - `oj_dockerfile_text`引数が必須

**エラー原因:** 実装が必須引数の明示を要求するが、テストが引数なしで呼び出している

### RetryDecorator関連 (4件失敗 / 7件中)
**失敗テスト:**
- `test_default_config` - 必須引数不足 (max_attempts, base_delay, max_delay, backoff_factor, logger)
- `test_custom_config` - 必須引数不足 (max_delay, backoff_factor, logger)
- `test_successful_operation` - 必須引数不足 (max_attempts, base_delay, max_delay, backoff_factor, logger)
- `test_execute_with_retry_success` - 必須引数不足 (max_attempts, base_delay, max_delay, backoff_factor, logger)

**エラー原因:** RetryConfigクラスが全引数を必須とするが、テストがデフォルト値を前提としている

### DataProcessors関連 (全17件通過)
現在のDataProcessorsは汎用的なユーティリティ関数のみ実装されており、全テストが通過している。

## 根本原因
**CLAUDE.mdルール適用:** 「引数にデフォルト値を指定するのを禁止する。呼び出し元で値を用意することを徹底する。」により、実装が厳格化されたが、テストが更新されていない。

## 修正計画

### 1. DockerNamingUtilsテスト修正
- `test_image_name_without_dockerfile` → `dockerfile_text=""`を明示的に渡す
- `test_container_name_without_dockerfile` → `dockerfile_text=""`を明示的に渡す
- `test_oj_image_name_without_dockerfile` → `oj_dockerfile_text=""`を明示的に渡す
- `test_oj_container_name_without_dockerfile` → `oj_dockerfile_text=""`を明示的に渡す

### 2. RetryDecoratorテスト修正
- 全RetryConfigインスタンス化で必須引数を明示的に指定
- テスト用のダミーLoggerインスタンスを作成
- 適切なデフォルト値を各テストで明示的に設定

### 3. 統合性確認
- 修正後の全テスト実行確認
- 実装とテストの整合性検証

## 影響範囲
- tests/unit/test_docker_naming_utils.py (4つのテストメソッド修正)
- tests/utils/test_retry_decorator.py (4つのテストメソッド修正)

## 修正優先度
**高優先度:** DockerNamingUtilsとRetryDecoratorの失敗テスト修正
**完了済み:** DataProcessorsテストは既に全て通過