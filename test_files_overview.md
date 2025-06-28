# プロジェクト内テストファイル一覧

## 概要
- **総テストファイル数**: 52ファイル
- **テストファイルの配置**: すべて`tests/`ディレクトリ配下に配置
- **src/配下のテストファイル**: なし（テストとソースコードが適切に分離されている）

## ディレクトリ別テストファイル数

| ディレクトリ | ファイル数 |
|------------|-----------|
| infrastructure | 9 |
| domain | 9 |
| operations | 8 |
| application | 7 |
| configuration | 6 |
| data | 3 |
| utils | 2 |
| presentation | 2 |
| logging | 2 |
| ルート | 4 |

## 詳細なテストファイル一覧とテスト対象

### 1. application層のテスト (7ファイル)
- `tests/application/services/test_config_loader_service.py` - ConfigLoaderServiceのテスト
- `tests/application/test_config_manager.py` - TypeSafeConfigNodeManagerのテスト
- `tests/application/test_contest_manager.py` - ContestManagerのテスト
- `tests/application/test_fast_sqlite_manager.py` - FastSQLiteManagerのテスト
- `tests/application/test_mock_output_manager.py` - MockOutputManagerのテスト
- `tests/application/test_output_manager.py` - OutputManagerのテスト
- `tests/application/test_pure_config_manager.py` - PureConfigManagerのテスト

### 2. configuration層のテスト (6ファイル)
- `tests/configuration/test_config_resolver.py` - ConfigResolverのテスト
- `tests/configuration/test_di_config.py` - DI設定のテスト
- `tests/configuration/test_di_config_simple.py` - シンプルなDI設定のテスト
- `tests/configuration/test_system_config_loader.py` - SystemConfigLoaderのテスト
- `tests/configuration/test_system_config_repository.py` - SystemConfigRepositoryのテスト
- `tests/configuration/test_system_config_repository_sqlite.py` - SQLite版SystemConfigRepositoryのテスト

### 3. data層のテスト (3ファイル)
- `tests/data/docker_container/test_docker_container_repository.py` - DockerContainerRepositoryのテスト
- `tests/data/docker_image/test_docker_image_repository.py` - DockerImageRepositoryのテスト
- `tests/data/test_sqlite_state_repository.py` - SQLiteStateRepositoryのテスト

### 4. domain層のテスト (9ファイル)
- `tests/domain/test_composite_step_failure.py` - CompositeStepの失敗ケーステスト
- `tests/domain/test_composite_step_failure_extended.py` - CompositeStepの拡張失敗ケーステスト
- `tests/domain/test_config_node.py` - ConfigNodeのテスト
- `tests/domain/test_config_node_logic.py` - ConfigNodeのロジックテスト
- `tests/domain/test_dependency.py` - Dependencyのテスト
- `tests/domain/test_step_runner.py` - StepRunnerのテスト（ステップ実行とテンプレート展開）
- `tests/domain/test_step_runner_extended.py` - StepRunnerの拡張テスト
- `tests/domain/test_workflow.py` - Workflowのテスト
- `tests/domain/test_workflow_execution_service.py` - WorkflowExecutionServiceのテスト

### 5. infrastructure層のテスト (9ファイル)
- `tests/infrastructure/drivers/generic/test_persistence_driver.py` - PersistenceDriverのテスト
- `tests/infrastructure/drivers/generic/test_unified_driver.py` - UnifiedDriverのテスト
- `tests/infrastructure/drivers/test_base_driver.py` - BaseDriverのテスト
- `tests/infrastructure/drivers/test_docker_driver.py` - DockerDriverのテスト
- `tests/infrastructure/drivers/test_file_driver.py` - FileDriverのテスト
- `tests/infrastructure/providers/test_json_provider.py` - JSONProviderのテスト
- `tests/infrastructure/providers/test_os_provider.py` - OSProviderのテスト
- `tests/infrastructure/test_ast_analyzer.py` - ASTAnalyzerのテスト
- `tests/infrastructure/test_di_container.py` - DIContainerのテスト（依存性注入コンテナ）

### 6. logging層のテスト (2ファイル)
- `tests/logging/test_log_types.py` - ログ型のテスト
- `tests/logging/test_unified_logger.py` - UnifiedLoggerのテスト

### 7. operations層のテスト (8ファイル)
- `tests/operations/interfaces/test_interfaces.py` - インターフェースのテスト
- `tests/operations/requests/test_execution_requests.py` - ExecutionRequestsのテスト
- `tests/operations/requests/test_file_request_simple.py` - シンプルなFileRequestのテスト
- `tests/operations/requests/test_request_factory.py` - RequestFactoryのテスト
- `tests/operations/results/test_result_factory.py` - ResultFactoryのテスト
- `tests/operations/test_base_command.py` - BaseCommandのテスト
- `tests/operations/test_error_converter.py` - ErrorConverterのテスト
- `tests/operations/test_path_types.py` - パス型のテスト

### 8. presentation層のテスト (2ファイル)
- `tests/presentation/test_formatters.py` - Formattersのテスト
- `tests/presentation/test_user_input_parser.py` - UserInputParserのテスト

### 9. utils層のテスト (2ファイル)
- `tests/utils/test_time_adapter.py` - TimeAdapterのテスト
- `tests/utils/test_types.py` - 型定義のテスト

### 10. ルートレベルのテスト (4ファイル)
- `tests/test_debug_service.py` - DebugServiceのテスト
- `tests/test_execution_requests.py` - ExecutionRequestsのテスト
- `tests/test_step_generation_service.py` - StepGenerationServiceのテスト
- `tests/test_validation_service.py` - ValidationServiceのテスト

## 観察結果

1. **適切な分離**: テストファイルはすべて`tests/`ディレクトリに配置され、本番コード(`src/`)とは明確に分離されている

2. **ディレクトリ構造の一致**: テストディレクトリの構造が本番コードのディレクトリ構造と一致しており、対応するモジュールを見つけやすい

3. **命名規則**: すべてのテストファイルが`test_`プレフィックスを使用している（`*_test.py`形式のファイルは存在しない）

4. **カバレッジの偏り**: 
   - infrastructure層とdomain層が最も多くのテストを持つ（各9ファイル）
   - utils層とpresentation層のテストが比較的少ない（各2ファイル）

5. **統合テストの存在**: ルートレベルに配置された4つのテストファイルは、サービス全体の統合テストと推測される