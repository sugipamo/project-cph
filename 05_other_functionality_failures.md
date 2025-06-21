# その他の機能テスト失敗 - 現状と修正計画

## テスト状況サマリー（2025年6月21日時点）

### ❌ 修正必要

#### Docker Naming Utils関連 - 4テスト失敗
**失敗原因**: CLAUDE.mdルール（デフォルト値禁止）によりメソッドシグネチャが変更
- `tests/unit/test_docker_naming_utils.py::TestGetDockerImageName::test_image_name_without_dockerfile`
- `tests/unit/test_docker_naming_utils.py::TestGetDockerContainerName::test_container_name_without_dockerfile`
- `tests/unit/test_docker_naming_utils.py::TestGetOjImageName::test_oj_image_name_without_dockerfile`
- `tests/unit/test_docker_naming_utils.py::TestGetOjContainerName::test_oj_container_name_without_dockerfile`

#### Retry Decorator関連 - 4テスト失敗
**失敗原因**: CLAUDE.mdルール（デフォルト値禁止）により `RetryConfig` の初期化引数が必須化
- `tests/utils/test_retry_decorator.py::TestRetryConfig::test_default_config`
- `tests/utils/test_retry_decorator.py::TestRetryConfig::test_custom_config`
- `tests/utils/test_retry_decorator.py::TestRetryDecorator::test_successful_operation`
- `tests/utils/test_retry_decorator.py::TestRetryableOperation::test_execute_with_retry_success`

### ✅ 正常動作
#### Docker Naming Utils関連 - 15テスト通過
#### Retry Decorator関連 - 3テスト通過

## 問題の分析

この分類のテストは個別の機能モジュールで発生している問題です：

1. **Docker Naming Utils**: Docker関連の命名ユーティリティ機能
   - `get_docker_image_name()`関数の`dockerfile_text`引数が必須化された（src/infrastructure/drivers/docker/utils/docker_naming.py:22）
   - テストコードが古い仕様（引数1つ）で呼び出しているため失敗

2. **Retry Decorator**: リトライ機能のデコレーター
   - `RetryConfig`クラスの全引数が必須化された（src/infrastructure/patterns/retry_decorator.py:13-17）
   - テストコードがデフォルト値の存在を前提とした古い仕様で記述されているため失敗

これらの失敗は、CLAUDE.mdルールの「デフォルト値の使用をグローバルに禁止」や「引数にデフォルト値を指定するのを禁止する」といった制約に準拠するための実装変更が完了している一方で、テストコードの更新が未完了であることが原因です。

## 修正計画

### Docker Naming Utils修正
- tests/unit/test_docker_naming_utils.py:57の`get_docker_image_name("python")`を`get_docker_image_name("python", "")`に修正
- 同様に他のテストケースも第2引数を明示的に指定

### Retry Decorator修正
- tests/utils/test_retry_decorator.py:23のRetryConfig呼び出しに必須引数を追加
- テスト用のloggerインスタンスを作成し、全引数を明示的に指定