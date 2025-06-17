# Operations と Workflow モジュールの責務分離改善案

## 現状の問題点サマリー

1. **依存関係の逆転**: workflow層がapplication層に依存している
2. **責務の混在**: 各モジュールが本来の責務以外の処理を含んでいる
3. **循環依存のリスク**: モジュール間の依存関係が複雑化している
4. **テスタビリティの低下**: 密結合により単体テストが困難

## 改善案

### 1. レイヤー構造の明確化

```
┌─────────────────────────────────────────────────────┐
│                   Application Layer                  │
│  (CLI, Orchestration, Request/Driver Factory)       │
├─────────────────────────────────────────────────────┤
│                   Workflow Layer                     │
│  (Step Orchestration, Dependency Resolution)        │
├─────────────────────────────────────────────────────┤
│                  Operations Layer                    │
│  (Request Types, Result Types, Interfaces)          │
├─────────────────────────────────────────────────────┤
│                Infrastructure Layer                  │
│  (File System, Shell, Docker Drivers)              │
└─────────────────────────────────────────────────────┘
```

### 2. インターフェースの導入

#### 2.1 Workflow層でインターフェースを定義

**src/workflow/interfaces/request_factory_interface.py**
```python
from abc import ABC, abstractmethod
from typing import Any, Optional
from src.operations.requests.base.base_request import OperationRequestFoundation

class IRequestFactory(ABC):
    """Request factory interface for workflow layer"""
    
    @abstractmethod
    def create_request(self, step: Any, context: Any) -> Optional[OperationRequestFoundation]:
        """Create operation request from step"""
        pass
```

**src/workflow/interfaces/driver_interface.py**
```python
from abc import ABC, abstractmethod
from typing import Any
from src.operations.results.result import OperationResult

class IDriver(ABC):
    """Driver interface for workflow layer"""
    
    @abstractmethod
    def execute(self, request: Any) -> OperationResult:
        """Execute operation request"""
        pass
```

#### 2.2 WorkflowExecutionServiceの改善

```python
class WorkflowExecutionService:
    def __init__(self, 
                 context, 
                 infrastructure,
                 request_factory: IRequestFactory,  # 依存性注入
                 driver: IDriver,                    # 依存性注入
                 config_service: IConfigService,     # 新規: 設定サービス
                 logger_service: ILoggerService):    # 新規: ログサービス
        self.context = context
        self.infrastructure = infrastructure
        self.request_factory = request_factory
        self.driver = driver
        self.config_service = config_service
        self.logger_service = logger_service
```

### 3. 共通概念の分離

#### 3.1 Step定義を共通モジュールへ移動

**src/common/step_types.py**
```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

class StepType(Enum):
    """Common step type definitions"""
    SHELL = "shell"
    PYTHON = "python"
    COPY = "copy"
    MKDIR = "mkdir"
    DOCKER_EXEC = "docker.exec"
    # ...

@dataclass
class Step:
    """Common step data structure"""
    type: StepType
    cmd: List[str]
    env: Optional[Dict[str, str]] = None
    # ...
```

### 4. 責務の再配置

#### 4.1 設定管理サービスの分離

**src/application/services/config_service.py**
```python
class ConfigService:
    """Handle all configuration-related operations"""
    
    def get_workflow_steps(self, context) -> List[Dict]:
        """Get workflow steps from configuration"""
        # Move logic from WorkflowExecutionService._get_workflow_steps
        pass
    
    def get_parallel_config(self, context) -> Dict:
        """Get parallel execution configuration"""
        # Move logic from WorkflowExecutionService._get_parallel_config
        pass
```

#### 4.2 環境ログサービスの分離

**src/application/services/environment_logger_service.py**
```python
class EnvironmentLoggerService:
    """Handle environment logging"""
    
    def log_environment_info(self, context) -> None:
        """Log environment information based on configuration"""
        # Move logic from WorkflowExecutionService._log_environment_info
        pass
```

### 5. 実装手順

1. **Phase 1: インターフェース定義** (影響: 小)
   - Workflow層にインターフェースを追加
   - 既存コードは変更なし

2. **Phase 2: 共通モジュールの作成** (影響: 中)
   - src/common を作成し、Step関連を移動
   - import文の更新が必要

3. **Phase 3: サービスの分離** (影響: 小)
   - ConfigService, EnvironmentLoggerServiceを作成
   - WorkflowExecutionServiceから責務を移譲

4. **Phase 4: 依存性注入の実装** (影響: 大)
   - WorkflowExecutionServiceのコンストラクタを変更
   - main.pyでの初期化処理を更新

5. **Phase 5: テストの更新** (影響: 中)
   - モックオブジェクトの作成
   - テストケースの更新

### 6. 期待される効果

1. **テスタビリティの向上**
   - 各モジュールが独立してテスト可能
   - モックオブジェクトの利用が容易

2. **保守性の向上**
   - 責務が明確になり、変更の影響範囲が限定的
   - 新機能追加時の拡張が容易

3. **再利用性の向上**
   - インターフェースによる疎結合
   - 実装の差し替えが可能

### 7. 移行時の注意点

1. **互換性の維持**
   - 段階的な移行を実施
   - 既存のAPIは維持しつつ、内部実装を変更

2. **テストの充実**
   - リファクタリング前後でテストが通ることを確認
   - 新しいインターフェースに対するテストを追加

3. **ドキュメントの更新**
   - アーキテクチャ図の更新
   - 新しい責務分担の説明を追加

## 具体的なコード変更例

### Before (現在の問題のあるコード)
```python
# src/workflow/workflow_execution_service.py
from src.application.factories.unified_request_factory import create_request
from src.application.orchestration.unified_driver import UnifiedDriver

class WorkflowExecutionService:
    def _execute_main_workflow(self, operations_composite, use_parallel=False, max_workers=4):
        unified_driver = UnifiedDriver(self.infrastructure)  # 直接生成
        # ...
```

### After (改善後のコード)
```python
# src/workflow/workflow_execution_service.py
from src.workflow.interfaces.driver_interface import IDriver

class WorkflowExecutionService:
    def __init__(self, context, infrastructure, driver: IDriver):
        self.driver = driver  # 依存性注入
        # ...
    
    def _execute_main_workflow(self, operations_composite, use_parallel=False, max_workers=4):
        # self.driverを使用（注入されたもの）
        # ...
```

この改善案により、operations と workflow の責務が明確に分離され、より保守性・拡張性の高いアーキテクチャが実現できます。