# テスト修正戦略 1: 設定管理システムの修正

## 問題の概要

Docker Command Builderおよび関連のインフラストラクチャコンポーネントにおいて、設定管理の依存性注入が必須となったが、テストで適切に設定されていない。

## 具体的な失敗要因

### 1. Configuration Manager未注入エラー

```python
# src/infrastructure/drivers/docker/utils/docker_command_builder.py
def _get_docker_option(option_name: str, user_options: Optional[dict[str, Any]]) -> Any:
    config_manager = _get_config_manager()
    if config_manager is None:
        raise KeyError(f"Docker option '{option_name}' not found: configuration manager not available")
```

**エラー**: `KeyError: Docker option 'xxx' not found: configuration manager not available`

### 2. テストでの設定管理不足

現在のテストは設定管理を初期化せずにDockerコマンドビルダーを呼び出している：

```python
# 現在の失敗テスト
def test_build_docker_run_command_basic(self):
    result = build_docker_run_command("ubuntu", "test", "{}")  # ❌ 設定管理なし
```

## 修正戦略

### Phase 1: 設定管理の初期化パターン

#### A. pytest fixtureの活用

```python
@pytest.fixture
def docker_config_manager():
    """Docker用の設定管理を提供"""
    from src.infrastructure.persistence.sqlite.system_config_loader import SystemConfigLoader
    from src.infrastructure.persistence.configuration_repository import ConfigurationRepository
    
    # テスト用の設定管理を作成
    config_repo = ConfigurationRepository(db_path=":memory:")
    config_manager = SystemConfigLoader(config_repo)
    
    # Docker関連の必要な設定を事前に登録（デフォルト値は設定ファイルから取得）
    config_manager.save_config_value("docker.default_timeout", "300")
    config_manager.save_config_value("docker.default_cwd", ".")
    config_manager.save_config_value("docker.default_env", "{}")
    config_manager.save_config_value("docker.debug_tag", "docker_run")
    config_manager.save_config_value("docker.request_name", "docker_run_request")
    
    return config_manager
```

#### B. 設定管理の注入方法

```python
@pytest.fixture
def setup_docker_config(docker_config_manager):
    """Dockerコマンドビルダーに設定管理を注入"""
    from src.infrastructure.drivers.docker.utils.docker_command_builder import set_config_manager
    
    # 設定管理を注入
    set_config_manager(docker_config_manager)
    
    yield docker_config_manager
    
    # テスト後のクリーンアップ
    set_config_manager(None)
```

### Phase 2: テストケースの更新

#### A. Before (失敗パターン)

```python
def test_build_docker_run_command_basic(self):
    """Basic docker run command building test."""
    result = build_docker_run_command("ubuntu", "test", "{}")
    # ❌ KeyError: configuration manager not available
```

#### B. After (修正パターン)

```python
def test_build_docker_run_command_basic(self, setup_docker_config):
    """Basic docker run command building test."""
    result = build_docker_run_command("ubuntu", "test", "{}")
    
    expected = ["docker", "run", "--name", "test", "ubuntu"]
    assert result == expected
```

### Phase 3: 統合テストでの設定管理

#### A. mock_infrastructureフィクスチャとの統合

```python
def test_docker_integration_with_config(mock_infrastructure, setup_docker_config):
    """設定管理と統合したDockerテスト"""
    infrastructure = mock_infrastructure
    
    # 設定管理が注入された状態でDockerコマンドを実行
    docker_driver = infrastructure.get_docker_driver()
    result = docker_driver.run_container("ubuntu", "test", "{}", True)
    
    assert result is not None
```

### Phase 4: 設定値のパラメータ化

```python
@pytest.mark.parametrize("docker_config", [
    {
        "docker.default_timeout": "300",
        "docker.default_cwd": ".",
        "docker.debug_tag": "docker_run"
    },
    {
        "docker.default_timeout": "600", 
        "docker.default_cwd": "/tmp",
        "docker.debug_tag": "docker_test"
    }
], indirect=True)
def test_docker_with_various_configs(docker_config, setup_docker_config):
    """様々な設定でのDockerテスト"""
    result = build_docker_run_command("ubuntu", "test", "{}")
    assert "docker" in result[0]
```

## 実装すべきファイル

### 1. 新規作成：`tests/fixtures/docker_fixtures.py`

```python
"""Docker関連のテストフィクスチャ"""

import pytest
from pathlib import Path

@pytest.fixture
def docker_config_manager():
    """Docker用設定管理フィクスチャ"""
    # 実装内容
    pass

@pytest.fixture  
def setup_docker_config(docker_config_manager):
    """Docker設定注入フィクスチャ"""
    # 実装内容
    pass
```

### 2. 更新対象：各テストファイル

**更新対象ファイル**:
- `tests/infrastructure/drivers/docker/utils/test_docker_command_builder.py`
- `tests/infrastructure/drivers/docker/test_docker_driver.py`
- `tests/infrastructure/drivers/logging/` 内の各テストファイル

### 3. conftest.pyの更新

```python
# tests/conftest.py に追加
from tests.fixtures.docker_fixtures import docker_config_manager, setup_docker_config
```

## 修正の優先順位

### High Priority (緊急)
1. `docker_command_builder` テストの設定管理注入
2. `LocalDockerDriver` テストの設定管理対応

### Medium Priority (重要)
3. Loggingドライバーの設定管理対応
4. Infrastructure統合テストの設定管理対応

### Low Priority (改善)
5. 設定値のパラメータ化テスト
6. 設定管理エラーハンドリングテスト

## 検証方法

### 1. 個別テスト実行
```bash
# 個別のDockerコマンドビルダーテスト実行
python3 -m pytest tests/infrastructure/drivers/docker/utils/test_docker_command_builder.py::TestDockerCommandBuilder::test_build_docker_run_command_basic -v
```

### 2. Docker関連テスト一括実行
```bash
# Docker関連テスト全体実行
python3 -m pytest tests/infrastructure/drivers/docker/ -v
```

### 3. 設定管理統合テスト
```bash
# 設定管理を使用する全テスト実行
python3 -m pytest -k "docker" -v
```

## 期待される結果

- Docker Command Builderテストの`KeyError`解消
- 設定管理依存のテストすべてが正常実行
- 今後の設定管理変更に対する保守性向上

## 注意事項

- 設定管理の注入はテスト毎に独立して行う
- テスト後のクリーンアップを必ず実施
- メモリ内データベース（`:memory:`）を使用してテスト高速化
- プロジェクトの"フォールバック処理禁止"ポリシーを遵守
- 引数にデフォルト値を指定することを禁止する（CLAUDE.mdルール遵守）
- すべての設定値は明示的に渡すことを徹底