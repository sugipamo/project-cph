# テスト修正戦略 3: テストフィクスチャの活用と統合（CLAUDE.md準拠版）

## 問題の概要

現在のテストでは、`conftest.py`で提供されている統一されたテストフィクスチャが十分に活用されていない。各テストが個別にモックを作成しており、一貫性がなく保守性が低い状態となっている。

## 設計方針遵守要件（CLAUDE.md準拠）

- **デフォルト値使用禁止**: 引数にデフォルト値を指定せず、呼び出し元で値を明示的に用意
- **設定ファイル編集禁止**: ユーザーから明示されない限り設定値は変更しない
- **フォールバック処理禁止**: 必要なエラーを見逃さないよう適切なエラーハンドリング
- **副作用の制限**: src/infrastructure、tests/infrastructureのみで副作用を許可
- **依存性注入**: すべてmain.pyから注入する設計

## 現在の進捗状況

**✅ 部分的修正済み**: 
- `test_docker_command_builder.py`で設定管理のモックパターンが実装済み
- `test_docker_driver.py`で基本的なパラメータ修正が完了

**❌ 未修正の課題**:
- `mock_infrastructure`フィクスチャの未活用
- 各テストでの個別モック作成
- フィクスチャ間の依存関係が不明確

## 利用可能なフィクスチャ分析

### 1. **既存のフィクスチャ** (`conftest.py`)

```python
@pytest.fixture
def mock_controller():
    """共通のMockControllerを提供"""

@pytest.fixture
def di_container():
    """基本的なDIコンテナを提供"""

@pytest.fixture
def mock_env_context():
    """モック環境コンテキストを提供"""

@pytest.fixture
def temp_workspace():
    """テスト用の一時ワークスペースを提供"""

@pytest.fixture
def mock_infrastructure():
    """統一されたモックインフラストラクチャを提供"""
    return build_mock_infrastructure()
```

### 2. **フィクスチャの活用状況**

#### A. 十分に活用されているフィクスチャ
- `temp_workspace`: 一時ファイル操作で適切に使用
- `mock_env_context`: 環境コンテキストのテストで使用

#### B. 未活用のフィクスチャ
- **`mock_infrastructure`**: 最も重要だが未活用
- **`di_container`**: DIコンテナの統合テストで未使用
- **`mock_controller`**: 制御フローテストで未使用

## 修正戦略

### Phase 1: mock_infrastructure フィクスチャの統合

#### A. 基本的な活用パターン（デフォルト値禁止準拠）

```python
# 現在のパターン（個別モック作成）
def test_docker_operation(self):
    mock_file_driver = Mock()
    mock_shell_driver = Mock()
    driver = LocalDockerDriver(file_driver=mock_file_driver)
    # ... テスト実行

# 推奨パターン（mock_infrastructure使用、必須パラメータ明示）
def test_docker_operation(self, mock_infrastructure):
    """統一モックインフラを使用したDockerテスト"""
    infrastructure = mock_infrastructure
    docker_driver = infrastructure.get_docker_driver()
    
    # 必須パラメータを明示的に指定（デフォルト値禁止準拠）
    result = docker_driver.run_container(
        image="ubuntu", 
        name="test", 
        options={}, 
        show_output=True
    )
    assert result is not None
```

#### B. 複数ドライバー統合テスト

```python
def test_multi_driver_integration(self, mock_infrastructure):
    """複数ドライバーの統合テスト（必須パラメータ明示）"""
    infrastructure = mock_infrastructure
    
    # 統一されたモックインフラから各ドライバーを取得
    docker_driver = infrastructure.get_docker_driver()
    file_driver = infrastructure.get_file_driver()
    logger = infrastructure.get_logger()
    
    # ドライバー間の依存関係が適切に設定されていることを確認
    assert docker_driver.file_driver == file_driver
    
    # 統合動作のテスト（必須パラメータを明示的に指定）
    docker_driver.run_container(
        image="test", 
        name="container", 
        options={}, 
        show_output=False
    )
    logger.info("Container operation completed")
```

### Phase 2: 設定管理フィクスチャの統合（設定編集禁止準拠）

#### A. 設定管理統合パターン（事前設定済み想定）

```python
@pytest.fixture
def configured_mock_infrastructure(mock_infrastructure):
    """設定済みモックインフラストラクチャ（既存設定読み込み）"""
    infrastructure = mock_infrastructure
    config_manager = infrastructure.get_config_manager()
    
    # 既存の設定値を使用（設定編集禁止準拠）
    # 設定値が不足している場合は明示的にエラーを発生
    docker_timeout = config_manager.get_config_value("docker.default_timeout")
    docker_cwd = config_manager.get_config_value("docker.default_cwd")
    logging_level = config_manager.get_config_value("logging.level")
    
    if not all([docker_timeout, docker_cwd, logging_level]):
        raise ValueError("必要な設定値が不足しています。設定ファイルを確認してください。")
    
    # 設定管理をDockerコマンドビルダーに注入（main.pyからの注入パターン準拠）
    from src.infrastructure.drivers.docker.utils.docker_command_builder import inject_config_manager
    inject_config_manager(config_manager)
    
    yield infrastructure
    
    # クリーンアップ（デフォルト値None使用禁止準拠）
    # 明示的に空のコンフィグマネージャーを注入
    empty_config_manager = infrastructure.create_empty_config_manager()
    inject_config_manager(empty_config_manager)
```

#### B. 設定管理統合テスト

```python
def test_docker_command_with_config(self, configured_mock_infrastructure):
    """設定管理統合Dockerコマンドテスト（必須パラメータ明示）"""
    infrastructure = configured_mock_infrastructure
    
    # 設定が注入された状態でのDockerコマンドビルダーテスト
    from src.infrastructure.drivers.docker.utils.docker_command_builder import build_docker_run_command
    
    # 必須パラメータを明示的に指定（デフォルト値禁止準拠）
    cmd = build_docker_run_command(
        image="ubuntu", 
        container_name="test", 
        options={},
        timeout_seconds=300,
        working_directory="."
    )
    assert "docker" in cmd[0]
    assert "ubuntu" in cmd
```

### Phase 3: 環境コンテキストフィクスチャの統合

#### A. 環境コンテキスト統合パターン

```python
def test_environment_aware_operations(self, mock_infrastructure, mock_env_context):
    """環境コンテキスト統合テスト（必須パラメータ明示）"""
    infrastructure = mock_infrastructure
    env_context = mock_env_context
    
    # 環境コンテキストを使用したコンポーネント初期化（必須パラメータ明示）
    environment_manager = infrastructure.get_environment_manager()
    environment_manager.set_context(
        context=env_context,
        validate_context=True
    )
    
    # 環境に応じた動作確認
    assert environment_manager.get_working_directory() == env_context.current_dir
    assert environment_manager.get_language() == env_context.language
```

#### B. 環境依存テストの統合

```python
@pytest.mark.parametrize("env_type", ["local", "docker"])
def test_environment_specific_behavior(self, mock_infrastructure, env_type):
    """環境別動作テスト（必須パラメータ明示）"""
    infrastructure = mock_infrastructure
    
    # 環境タイプに応じた動作確認（必須パラメータ明示）
    env_manager = infrastructure.get_environment_manager()
    env_manager.set_env_type(
        env_type=env_type,
        validate_type=True
    )
    
    if env_type == "docker":
        docker_driver = infrastructure.get_docker_driver()
        result = docker_driver.run_container(
            image="ubuntu", 
            name="test", 
            options={}, 
            show_output=True
        )
        assert result is not None
    else:
        # ローカル環境での動作確認（必須パラメータ明示）
        shell_driver = infrastructure.get_shell_driver()
        result = shell_driver.execute_command(
            command="echo test",
            timeout_seconds=30
        )
        assert result is not None
```

### Phase 4: 一時ワークスペースフィクスチャの統合

#### A. ファイル操作統合パターン

```python
def test_file_operations_with_workspace(self, mock_infrastructure, temp_workspace):
    """一時ワークスペース統合ファイル操作テスト（必須パラメータ明示）"""
    infrastructure = mock_infrastructure
    file_driver = infrastructure.get_file_driver()
    
    # 一時ワークスペース内でのファイル操作（必須パラメータ明示）
    test_file = temp_workspace / "test.txt"
    file_driver.create_file(
        file_path=test_file, 
        content="test content",
        encoding="utf-8",
        overwrite_if_exists=False
    )
    
    # ファイル存在確認
    assert file_driver.exists(file_path=test_file)
    
    # 内容確認（必須パラメータ明示）
    content = file_driver.read_file(
        file_path=test_file,
        encoding="utf-8"
    )
    assert content == "test content"
```

#### B. Docker-ファイル操作統合テスト

```python
def test_docker_file_integration(self, mock_infrastructure, temp_workspace):
    """Docker-ファイル操作統合テスト（必須パラメータ明示）"""
    infrastructure = mock_infrastructure
    docker_driver = infrastructure.get_docker_driver()
    file_driver = infrastructure.get_file_driver()
    
    # Dockerfileの作成（必須パラメータ明示）
    dockerfile_path = temp_workspace / "Dockerfile"
    dockerfile_content = "FROM ubuntu\nRUN echo 'test'"
    file_driver.create_file(
        file_path=dockerfile_path, 
        content=dockerfile_content,
        encoding="utf-8",
        overwrite_if_exists=False
    )
    
    # Dockerイメージのビルド（必須パラメータ明示）
    result = docker_driver.build_docker_image(
        dockerfile_content=dockerfile_content, 
        tag="test:latest", 
        options={}, 
        context_path=str(temp_workspace),
        show_output=True,
        timeout_seconds=600
    )
    assert result is not None
```

## 新しいフィクスチャの提案（CLAUDE.md準拠）

### 1. 特化型フィクスチャ（設定編集禁止準拠）

```python
# tests/fixtures/specialized_fixtures.py

@pytest.fixture
def docker_test_environment(mock_infrastructure, temp_workspace):
    """Docker特化テスト環境（既存設定読み込み）"""
    infrastructure = mock_infrastructure
    
    # 既存のDocker関連設定を検証（設定編集禁止準拠）
    config_manager = infrastructure.get_config_manager()
    docker_timeout = config_manager.get_config_value("docker.default_timeout")
    
    if not docker_timeout:
        raise ValueError("docker.default_timeout設定が不足しています")
    
    # 一時ワークスペースの準備（必須パラメータ明示）
    dockerfile_path = temp_workspace / "Dockerfile"
    dockerfile_path.write_text(
        content="FROM ubuntu\nRUN echo 'test'",
        encoding="utf-8"
    )
    
    return {
        'infrastructure': infrastructure,
        'workspace': temp_workspace,
        'dockerfile_path': dockerfile_path,
        'docker_timeout': docker_timeout
    }

@pytest.fixture
def logging_test_environment(mock_infrastructure):
    """Logging特化テスト環境（既存設定読み込み）"""
    infrastructure = mock_infrastructure
    
    # 既存のログ関連設定を検証（設定編集禁止準拠）
    config_manager = infrastructure.get_config_manager()
    logging_level = config_manager.get_config_value("logging.level")
    logging_format = config_manager.get_config_value("logging.format")
    
    if not all([logging_level, logging_format]):
        raise ValueError("ログ設定が不足しています。設定ファイルを確認してください")
    
    return {
        'infrastructure': infrastructure,
        'logging_level': logging_level,
        'logging_format': logging_format
    }
```

### 2. パラメータ化フィクスチャ（必須パラメータ明示）

```python
@pytest.fixture(params=["local", "docker"])
def environment_type(request):
    """環境タイプのパラメータ化（必須パラメータ明示）"""
    env_type = request.param
    
    # パラメータの妥当性検証（フォールバック処理禁止準拠）
    if env_type not in ["local", "docker"]:
        raise ValueError(f"不正な環境タイプ: {env_type}")
    
    return env_type

@pytest.fixture(params=["INFO", "DEBUG", "WARNING"])
def log_level(request):
    """ログレベルのパラメータ化（妥当性検証付き）"""
    level = request.param
    
    # ログレベルの妥当性検証（フォールバック処理禁止準拠）
    valid_levels = ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]
    if level not in valid_levels:
        raise ValueError(f"不正なログレベル: {level}")
    
    return level
```

## 修正対象ファイル

### 1. 高優先度（即座に修正すべき）

```python
# tests/infrastructure/drivers/logging/test_unified_logger.py
def test_unified_logger_integration(self, mock_infrastructure):
    """統一ロガーの統合テスト"""
    infrastructure = mock_infrastructure
    logger = infrastructure.get_logger()
    
    # 統一されたログ機能のテスト
    logger.info("Test message")
    assert logger.message_count > 0

# tests/mock/test_mock_file_driver.py  
def test_mock_file_driver_integration(self, mock_infrastructure, temp_workspace):
    """モックファイルドライバーの統合テスト"""
    infrastructure = mock_infrastructure
    file_driver = infrastructure.get_file_driver()
    
    # 一時ワークスペースでのファイル操作
    test_file = temp_workspace / "test.txt"
    file_driver.create_file(test_file, "content")
    assert file_driver.exists(test_file)
```

### 2. 中優先度（段階的修正）

```python
# tests/infrastructure/environment/test_environment_manager.py
def test_environment_manager_integration(self, mock_infrastructure, mock_env_context):
    """環境管理の統合テスト"""
    infrastructure = mock_infrastructure
    env_manager = infrastructure.get_environment_manager()
    
    env_manager.set_context(mock_env_context)
    assert env_manager.get_working_directory() == mock_env_context.current_dir
```

### 3. 新規作成ファイル

**`tests/fixtures/integrated_fixtures.py`**:
```python
"""統合テストフィクスチャ"""

@pytest.fixture
def full_integration_environment(mock_infrastructure, temp_workspace, mock_env_context):
    """完全統合テスト環境"""
    # 実装内容
    pass
```

## 検証方法

### 1. フィクスチャ統合テスト
```bash
# 統合フィクスチャを使用するテスト実行
python3 -m pytest tests/infrastructure/ -k "integration" -v
```

### 2. フィクスチャ依存関係確認
```bash
# フィクスチャの依存関係を確認
python3 -m pytest --fixtures-per-test tests/infrastructure/drivers/docker/test_docker_driver.py -v
```

### 3. 段階的フィクスチャ移行確認
```bash
# 段階的にフィクスチャを統合したテスト実行
python3 -m pytest tests/infrastructure/drivers/logging/ -v
```

## 期待される結果

- **統一性**: すべてのテストで`mock_infrastructure`フィクスチャを使用
- **保守性**: 個別モック作成の削減
- **拡張性**: 新しいコンポーネント追加時のフィクスチャ再利用
- **テスト品質**: より現実的な統合テストの実現

## 注意事項

- **既存の`conftest.py`を最大限活用**
- **フィクスチャの初期化順序に注意**
- **テスト分離の原則を維持**
- **`build_mock_infrastructure()`の実装詳細を理解して活用**