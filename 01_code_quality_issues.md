# コード品質関連の問題

## 概要
CLAUDE.mdのルール違反や命名規則の問題が検出されています。

## 検出された問題

### None引数初期値の使用（CLAUDE.mdルール違反）
- `operations/requests/base/base_request.py:42` - `execute_operation` メソッド
- `operations/results/shell_result.py:10` - `__init__` メソッド

### 命名規則の問題
- `infrastructure/providers/sqlite_provider.py:154` - 抽象的関数名 `execute`

## カバレッジが低いファイル（80%未満）
- `context/formatters/context_formatter.py`: 0%
- `infrastructure/drivers/docker/docker_driver_with_tracking.py`: 0%
- `operations/factories/request_factory.py`: 18%
- `infrastructure/persistence/sqlite/repositories/docker_image_repository.py`: 19%
- `infrastructure/result/result_factory.py`: 19%
- `infrastructure/persistence/sqlite/repositories/docker_container_repository.py`: 21%
- `infrastructure/drivers/unified/unified_driver.py`: 22%
- `infrastructure/result/error_converter.py`: 24%
- `operations/requests/docker/docker_request.py`: 31%
- `infrastructure/persistence/sqlite/repositories/operation_repository.py`: 33%
- `operations/requests/shell/shell_request.py`: 33%
- `infrastructure/persistence/sqlite/repositories/session_repository.py`: 34%
- `infrastructure/mock/mock_docker_driver.py`: 36%
- `operations/requests/composite/composite_request.py`: 36%
- `operations/requests/composite/composite_structure.py`: 37%

## 必要な対応
1. None引数初期値を削除し、呼び出し元で適切な値を用意
2. 抽象的関数名を具体的で分かりやすい名前に変更
3. カバレッジが低いファイルのテスト強化