# 機能別構造への移行計画

## 目標構造

```
src/
├── main.py
├── core/
│   ├── models.py      # BaseRequest + OperationResult統合
│   ├── types.py       # OperationType + ExecutionTypes統合
│   └── exceptions.py
├── execution/
│   ├── controller.py
│   ├── service.py
│   ├── drivers/
│   │   ├── docker.py
│   │   ├── file.py
│   │   ├── python.py
│   │   └── shell.py
│   └── formatters.py
├── context/
│   ├── parser.py
│   ├── resolver.py
│   ├── validator.py
│   └── formatter.py
├── workflow/
│   ├── builder.py
│   ├── executor.py
│   ├── graph.py
│   └── steps.py
├── data/
│   ├── repositories.py
│   ├── database.py
│   └── migrations/
└── shared/
    ├── utils.py
    ├── config.py
    └── logger.py
```

## 移行手順

### 1. 新ディレクトリの作成

```bash
mkdir -p src/core
mkdir -p src/execution/drivers
mkdir -p src/data/migrations
mkdir -p src/shared
```

### 2. 単純ファイル移動（28コマンド）

#### context関連（4コマンド）
```bash
mv src/context/user_input_parser.py src/context/parser.py
mv src/context/resolver/config_resolver.py src/context/resolver.py
mv src/context/context_validator.py src/context/validator.py
mv src/context/formatters/context_formatter.py src/context/formatter.py
```

#### execution関連（10コマンド）
```bash
mv src/application/orchestration/execution_controller.py src/execution/controller.py
mv src/workflow_execution_service.py src/execution/service.py
mv src/application/orchestration/output_formatters.py src/execution/formatters.py
mv src/infrastructure/drivers/docker/docker_driver.py src/execution/drivers/docker.py
mv src/infrastructure/drivers/file/local_file_driver.py src/execution/drivers/file.py
mv src/infrastructure/drivers/python/python_driver.py src/execution/drivers/python.py
mv src/infrastructure/drivers/shell/local_shell_driver.py src/execution/drivers/shell.py
mv src/infrastructure/drivers/file/file_driver.py src/execution/drivers/file_interface.py
mv src/infrastructure/drivers/shell/shell_driver.py src/execution/drivers/shell_interface.py
mv src/infrastructure/drivers/base/base_driver.py src/execution/drivers/base.py
```

#### workflow関連（4コマンド）
```bash
mv src/workflow/workflow/graph_based_workflow_builder.py src/workflow/builder.py
mv src/workflow/workflow/request_execution_graph.py src/workflow/graph.py
mv src/workflow/step/workflow.py src/workflow/executor.py
mv src/workflow/step/step.py src/workflow/steps.py
```

#### data関連（3コマンド）
```bash
mv src/infrastructure/persistence/sqlite/sqlite_manager.py src/data/database.py
mv src/infrastructure/persistence/sqlite/migrations src/data/migrations
mv src/utils/debug_logger.py src/shared/logger.py
```

#### その他（7コマンド）
```bash
mv src/domain/constants/operation_type.py src/core/operation_type.py
mv src/domain/types/execution_types.py src/core/execution_types.py
mv src/domain/exceptions/composite_step_failure.py src/core/exceptions.py
mv src/domain/requests/base/base_request.py src/core/base_request.py
mv src/domain/results/result.py src/core/result.py
mv src/infrastructure/config/di_config.py src/shared/di_config.py
mv src/infrastructure/di_container.py src/shared/config.py
```

### 3. 手動統合作業（6箇所）

#### core/types.py
```bash
# 統合対象:
# - src/core/operation_type.py
# - src/core/execution_types.py
# → src/core/types.py として統合
```

#### core/models.py
```bash
# 統合対象:
# - src/core/base_request.py
# - src/core/result.py
# → src/core/models.py として統合
```

#### data/repositories.py
```bash
# 統合対象:
# - src/infrastructure/persistence/sqlite/repositories/operation_repository.py
# - src/infrastructure/persistence/sqlite/repositories/session_repository.py
# → src/data/repositories.py として統合
```

#### shared/utils.py
```bash
# 統合対象:
# - src/utils/helpers.py
# - src/utils/formatters.py
# - src/utils/path_operations.py
# → src/shared/utils.py として統合
```

#### shared/config.py
```bash
# 統合対象:
# - src/shared/di_config.py
# - src/shared/config.py（既存）
# → src/shared/config.py として統合
```

#### workflow/steps.py
```bash
# 統合対象:
# - src/workflow/step/core.py
# - src/workflow/step/dependency.py
# - src/workflow/steps.py（既存）
# → 依存関係を統合
```

### 4. 削除対象ディレクトリ

```bash
rm -rf src/application
rm -rf src/domain
rm -rf src/infrastructure
rm -rf src/utils
rm -rf src/context/commands
rm -rf src/context/parsers
rm -rf src/context/resolver
rm -rf src/context/utils
rm -rf src/execution/fitting
rm -rf src/workflow/step
rm -rf src/workflow/workflow
```

### 5. 残存ファイルの処理

以下のファイルは新構造への適切な配置場所を検討：

```
src/context/config_resolver_proxy.py
src/context/dockerfile_resolver.py
src/context/execution_context.py
src/context/execution_data.py
src/domain/interfaces/docker_interface.py
src/domain/interfaces/execution_interface.py
src/domain/requests/composite/*
src/domain/requests/docker/*
src/domain/requests/file/*
src/domain/requests/python/*
src/domain/requests/shell/*
src/domain/results/docker_result.py
src/domain/results/file_result.py
src/domain/results/shell_result.py
src/infrastructure/environment/environment_manager.py
src/infrastructure/mock/*
src/workflow/step/core.py
src/workflow/step/dependency.py
src/workflow/workflow/graph_builder_utils.py
```

## 移行工数見積もり

- **単純移動**: 28コマンド（1時間）
- **手動統合**: 6箇所（3-4時間）
- **import文修正**: 全体調整（1-2時間）
- **テスト修正**: テストケース更新（1時間）

**総工数**: 約6-8時間

## 移行後の利点

1. **機能の凝集性向上**: 関連コードが同じディレクトリに集約
2. **依存関係の明確化**: レイヤー間の依存が分かりやすい
3. **保守性向上**: 機能追加時の影響範囲が限定的
4. **理解しやすさ**: 新しい開発者にとって直感的な構造