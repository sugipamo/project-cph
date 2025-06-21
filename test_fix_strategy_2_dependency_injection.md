# テスト修正戦略 2: 依存性注入システムの修正

## 問題の概要

プロジェクトが依存性注入（DI）パターンに移行したため、テストで適切な依存関係の構築とモックが必要となった。現在のテストは古いパターンでコンポーネントを直接インスタンス化しており、必要な依存関係が不足している。

## 現在の進捗状況

**✅ 部分的修正済み**: `test_docker_driver.py`では以下の修正が完了：
- `LocalFileDriver(base_dir=Path('.'))`の明示的な初期化
- 全パラメータの明示的指定
- ShellRequestの完全なパラメータ渡し

**❌ 未修正の課題**:
- DIコンテナの統合不足
- インフラストラクチャ全体の依存性注入
- Logging、Mock、その他のドライバーでの依存性不足

## 依存性注入の要求事項

### 1. **DIContainer統合パターン**

現在利用可能な`conftest.py`のフィクスチャ：
```python
@pytest.fixture
def di_container():
    """基本的なDIコンテナを提供"""
    di = DIContainer()
    di.register("DockerRequest", lambda: DockerRequest)
    di.register("ShellRequest", lambda: ShellRequest) 
    # ... 他の登録
    return di

@pytest.fixture  
def mock_infrastructure():
    """統一されたモックインフラストラクチャを提供"""
    return build_mock_infrastructure()
```

### 2. **主要な依存性注入ポイント**

#### A. Driver レベルの依存性
- **FileDriver**: `base_dir`パラメータ必須
- **ShellDriver**: DI経由でのインスタンス生成
- **ConfigurationManager**: 設定管理の注入

#### B. Infrastructure レベルの依存性
- **DIContainer**: 全コンポーネントの登録と管理
- **DatabaseConnections**: SQLite管理の依存性
- **LoggerAdapters**: ログ出力管理の依存性

## 修正戦略

### Phase 1: DIコンテナ統合テストパターン

#### A. 基本的なDI統合テスト

```python
def test_docker_driver_with_di_container(di_container, mock_infrastructure):
    """DIコンテナを使用したDockerドライバーテスト"""
    
    # DIコンテナからドライバーを取得
    infrastructure = mock_infrastructure
    docker_driver = infrastructure.get_docker_driver()
    
    # 依存関係が正しく注入されていることを確認
    assert docker_driver.file_driver is not None
    assert docker_driver.shell_driver is not None
    
    # 実際の操作テスト
    result = docker_driver.run_container("ubuntu", name="test", options={}, show_output=True)
    assert result is not None
```

#### B. 複合的な依存性テスト

```python
def test_infrastructure_component_integration(mock_infrastructure):
    """インフラストラクチャコンポーネント統合テスト"""
    
    infrastructure = mock_infrastructure
    
    # 各ドライバーの取得と依存性確認
    docker_driver = infrastructure.get_docker_driver()
    file_driver = infrastructure.get_file_driver()
    logger = infrastructure.get_logger()
    
    # 相互依存性の確認
    assert docker_driver.file_driver == file_driver
    assert hasattr(docker_driver, 'shell_driver')
    
    # 統合動作確認
    docker_driver.run_container("test", name="container", options={}, show_output=False)
```

### Phase 2: Mock Infrastructure活用パターン

#### A. 現在のmock_infrastructureフィクスチャの活用

```python
# build_mock_infrastructure()が提供する統一モック
def test_with_mock_infrastructure(mock_infrastructure):
    """統一モックインフラを使用したテスト"""
    
    # モックインフラから必要なコンポーネントを取得
    docker_driver = mock_infrastructure.get_docker_driver()
    config_manager = mock_infrastructure.get_config_manager()
    logger = mock_infrastructure.get_logger()
    
    # すべてのコンポーネントが適切にモック化されている
    assert docker_driver is not None
    assert config_manager is not None  
    assert logger is not None
```

#### B. 特定コンポーネントのモック拡張

```python
def test_docker_with_custom_mock_config(mock_infrastructure):
    """カスタムモック設定を使用したDockerテスト"""
    
    infrastructure = mock_infrastructure
    
    # 特定の設定値をモックに追加
    config_manager = infrastructure.get_config_manager()
    config_manager.save_config_value("docker.default_timeout", "600")
    
    # 設定が反映されたコンポーネントの動作確認
    docker_driver = infrastructure.get_docker_driver()
    result = docker_driver.run_container("ubuntu", name="test", options={}, show_output=True)
    
    assert result is not None
```

### Phase 3: Logging Driver依存性注入

#### A. LoggerAdapter の依存性解決

現在失敗しているLoggingテスト：
```python
# 失敗パターン
def test_log_error_with_correlation(self):
    adapter = ApplicationLoggerAdapter()  # ❌ 依存性不足

# 修正パターン  
def test_log_error_with_correlation(self, mock_infrastructure):
    infrastructure = mock_infrastructure
    logger = infrastructure.get_logger()
    
    # LoggerAdapterに必要な依存性を注入
    adapter = ApplicationLoggerAdapter(
        logger=logger.base_logger,
        config_manager=infrastructure.get_config_manager()
    )
    
    # テスト実行
    adapter.log_error_with_correlation("test error", correlation_id="123")
```

#### B. OutputManager の依存性解決

```python
def test_output_manager_with_dependencies(mock_infrastructure):
    """OutputManager の依存性注入テスト"""
    
    infrastructure = mock_infrastructure
    config_manager = infrastructure.get_config_manager()
    
    # OutputManagerに設定管理を注入
    output_manager = OutputManager(
        level=LogLevel.INFO,
        config_manager=config_manager
    )
    
    output_manager.add("Test message")
    assert len(output_manager.entries) == 1
```

### Phase 4: Mock File Driver依存性注入

#### A. MockFileDriver初期化の修正

```python
# 現在の失敗パターン
def test_create_and_exists():
    driver = MockFileDriver()  # ❌ base_dir未指定

# 修正パターン 1: 直接初期化
def test_create_and_exists(temp_workspace):
    driver = MockFileDriver(base_dir=temp_workspace)
    
    # テスト実行
    driver.create_file(Path("test.txt"), "content")
    assert driver.exists(Path("test.txt"))

# 修正パターン 2: mock_infrastructure使用
def test_create_and_exists_with_infrastructure(mock_infrastructure):
    infrastructure = mock_infrastructure
    file_driver = infrastructure.get_file_driver()
    
    # モックファイルドライバーとして動作
    file_driver.create_file(Path("test.txt"), "content")
    assert file_driver.exists(Path("test.txt"))
```

#### B. ファイル操作の依存性注入

```python
def test_file_operations_with_di(mock_infrastructure, temp_workspace):
    """ファイル操作の完全な依存性注入テスト"""
    
    infrastructure = mock_infrastructure
    file_driver = infrastructure.get_file_driver()
    
    # 一時ワークスペースでの操作
    test_file = temp_workspace / "test.txt"
    file_driver.create_file(test_file, "test content")
    
    # 読み込み確認
    content = file_driver.read_file(test_file)
    assert content == "test content"
    
    # 依存性注入されたコンポーネント間の連携確認
    docker_driver = infrastructure.get_docker_driver()
    assert docker_driver.file_driver == file_driver
```

## 実装すべきファイル

### 1. 新規作成：`tests/fixtures/di_fixtures.py`

```python
"""依存性注入関連のテストフィクスチャ"""

import pytest
from pathlib import Path

@pytest.fixture
def enhanced_mock_infrastructure():
    """拡張されたモックインフラストラクチャ"""
    from src.infrastructure.build_infrastructure import build_mock_infrastructure
    
    infrastructure = build_mock_infrastructure()
    
    # 追加の依存性設定
    config_manager = infrastructure.get_config_manager()
    config_manager.save_config_value("docker.default_timeout", "300")
    config_manager.save_config_value("logging.level", "INFO")
    
    return infrastructure

@pytest.fixture
def di_with_real_config(temp_dir):
    """実際の設定を使用するDIコンテナ"""
    # 必須パラメータを明示的に指定
    from src.infrastructure.build_infrastructure import build_infrastructure
    return build_infrastructure(base_dir=temp_dir)
```

### 2. 更新対象テストファイル

**高優先度**:
- `tests/infrastructure/drivers/logging/adapters/test_application_logger_adapter.py`
- `tests/infrastructure/drivers/logging/test_mock_output_manager.py`
- `tests/infrastructure/drivers/logging/test_output_manager.py`
- `tests/infrastructure/drivers/logging/test_unified_logger.py`

**中優先度**:
- `tests/mock/test_mock_file_driver.py`
- `tests/infrastructure/environment/test_environment_manager.py`
- `tests/infrastructure/persistence/` 内の各テストファイル

### 3. DIコンテナの設定更新

```python
# tests/conftest.py の di_container フィクスチャを拡張
@pytest.fixture
def enhanced_di_container():
    """拡張されたDIコンテナ"""
    di = DIContainer()
    
    # 基本コンポーネント登録
    di.register("DockerRequest", lambda: DockerRequest)
    di.register("ShellRequest", lambda: ShellRequest)
    di.register("FileRequest", lambda: FileRequest)
    
    # インフラストラクチャコンポーネント登録
    di.register("ConfigurationManager", lambda: mock_config_manager)
    di.register("Logger", lambda: mock_logger)
    di.register("FileDriver", lambda base_dir: MockFileDriver(base_dir=base_dir))
    
    return di
```

## 修正の優先順位

### Critical Priority (緊急)
1. `mock_infrastructure` フィクスチャの完全活用
2. LoggerAdapter, OutputManager の依存性注入
3. MockFileDriver の base_dir パラメータ修正

### High Priority (重要)  
4. DIコンテナとテストの統合
5. Infrastructure統合テストの依存性解決
6. Environment Manager の依存性注入

### Medium Priority (改善)
7. Persistence レイヤーの依存性注入
8. 複合コンポーネントテストの依存性管理

## 検証方法

### 1. 依存性注入テスト実行
```bash
# Logging関連の依存性注入テスト
python3 -m pytest tests/infrastructure/drivers/logging/ -v

# Mock関連の依存性注入テスト  
python3 -m pytest tests/mock/ -v
```

### 2. 統合テスト実行
```bash
# インフラストラクチャ統合テスト
python3 -m pytest tests/infrastructure/ -k "infrastructure" -v

# DIコンテナ統合テスト
python3 -m pytest -k "di_container" -v
```

### 3. 依存性チェーン確認
```bash
# 依存性チェーンの動作確認
python3 -m pytest tests/integration/ -v
```

## 期待される結果

- すべてのコンポーネントで適切な依存性注入
- `mock_infrastructure` フィクスチャの完全活用
- DIコンテナを通じた一貫したコンポーネント管理
- テスト間での依存性の分離と再利用性向上

## 注意事項

- DIコンテナの設定はテスト毎に分離
- モックと実装の依存性を明確に分離
- `build_mock_infrastructure()` の既存実装を最大限活用
- プロジェクトの"副作用はinfrastructureのみ"ポリシーを遵守

## CLAUDE.md準拠事項

- **デフォルト値禁止**: 全ての引数を明示的に指定
- **フォールバック処理禁止**: エラーを適切に処理
- **副作用制限**: infrastructure層のみで副作用を許可
- **依存性注入**: main.pyからの注入を徹底
- **設定管理**: デフォルト値の使用を完全に排除
- **全ての依存関係を明示的に注入**