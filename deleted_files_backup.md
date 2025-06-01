# 削除ファイルバックアップ記録

## 削除日時: 2025-06-01

### Phase 1: 完全に未使用のファイル（10個）

1. src/env_core/step/simple_graph_analysis.py
2. src/env_core/types.py
3. src/env_core/workflow/application/step_to_request_adapter.py
4. src/env_core/workflow/domain/workflow_domain_service.py
5. src/env_core/workflow/infrastructure/request_infrastructure_service.py
6. src/env_core/workflow/layered_workflow_builder.py
7. src/env_factories/request_builders.py
8. src/env_integration/fitting/environment_inspector.py
9. src/env_integration/fitting/preparation_planner.py
10. src/factories/factory_coordinator.py

### Phase 2: 未使用システム（削除済み）

#### 設定管理システム (src/config/*)
- src/config/cache.py
- src/config/discovery.py
- src/config/exceptions.py
- src/config/manager.py
- src/config/schema.py
- src/config/template.py
- src/config/validation.py

#### エラーハンドリングシステム (src/core/exceptions/*)
- src/core/exceptions/base_exceptions.py
- src/core/exceptions/error_handler.py
- src/core/exceptions/error_logger.py
- src/core/exceptions/error_recovery.py
- src/core/exceptions/message_formatter.py

#### 環境ファクトリーシステム (src/env_factories/*)
- src/env_factories/base/factory.py
- src/env_factories/builders/base_builder.py
- src/env_factories/builders/builder_registry.py
- src/env_factories/builders/docker_request_builder.py
- src/env_factories/builders/file_request_builder.py
- src/env_factories/builders/python_request_builder.py
- src/env_factories/builders/shell_request_builder.py
- src/env_factories/command_types.py
- src/env_factories/unified_factory.py
- src/env_factories/unified_selector.py

#### 環境統合システム (src/env_integration/*)
- src/env_integration/builder.py
- src/env_integration/controller.py
- src/env_integration/fitting/preparation_executor.py
- src/env_integration/service.py

### Phase 3: 放棄されたアーキテクチャ（削除済み）

#### 環境リソース管理システム (src/env_resource/*)
- src/env_resource/file/base_file_handler.py
- src/env_resource/file/docker_file_handler.py  
- src/env_resource/file/local_file_handler.py
- src/env_resource/run/base_run_handler.py
- src/env_resource/run/docker_run_handler.py
- src/env_resource/run/local_run_handler.py
- src/env_resource/utils/docker_naming.py
- src/env_resource/utils/path_environment_checker.py

#### 抽象ファクトリーシステム (src/factories/*)
- src/factories/abstract_factory.py
- src/factories/factory_coordinator.py

## 削除統計

- **Phase 1**: 完全に未使用のファイル 10個
- **Phase 2**: 未使用システム 26個  
- **Phase 3**: 放棄されたアーキテクチャ 10個
- **合計削除**: 46ファイル
- **削除前**: 176ファイル → **削除後**: 126ファイル (74%)
- **未使用ファイル**: 73個 → 28個 (62%削減)

### 復元方法
gitを使用している場合: `git checkout <commit_hash> -- <file_path>`