"""
共通テストフィクスチャの定義
テストコードの重複を削減し、保守性を向上させる
"""
import os
import tempfile
from pathlib import Path

import pytest

from src.infrastructure.build_infrastructure import build_mock_infrastructure
from src.infrastructure.di_container import DIContainer


@pytest.fixture
def mock_controller():
    """共通のMockControllerを提供"""
    class MockController:
        def __init__(self):
            self.env_context = type("EnvContext", (), {
                "contest_name": "test_contest",
                "problem_name": "a",
                "language": "python",
                "command_type": "test",
                "env_type": "local"
            })()
    return MockController()


@pytest.fixture
def di_container():
    """基本的なDIコンテナを提供"""
    from src.domain.requests.docker.docker_request import DockerOpType, DockerRequest
    from src.domain.requests.file.file_op_type import FileOpType
    from src.domain.requests.file.file_request import FileRequest
    from src.domain.requests.python.python_request import PythonRequest
    from src.domain.requests.shell.shell_request import ShellRequest

    di = DIContainer()
    di.register("DockerRequest", lambda: DockerRequest)
    di.register("DockerOpType", lambda: DockerOpType)
    di.register("FileRequest", lambda: FileRequest)
    di.register("FileOpType", lambda: FileOpType)
    di.register("ShellRequest", lambda: ShellRequest)
    di.register("PythonRequest", lambda: PythonRequest)
    return di


@pytest.fixture
def mock_env_context():
    """モック環境コンテキストを提供"""
    return type("EnvContext", (), {
        "contest_name": "test_contest",
        "problem_name": "a",
        "language": "python",
        "command_type": "test",
        "env_type": "local",
        "current_dir": ".",
        "base_dir": ".",
        "template_dir": "./contest_template",
        "target_dir": "./contest_current"
    })()


def assert_no_driver_error(request_class, error_message, **kwargs):
    """ドライバー不在エラーのテストヘルパー"""
    req = request_class(**kwargs)
    with pytest.raises(ValueError) as excinfo:
        req.execute(None)
    assert str(excinfo.value) == error_message


def assert_request_success(result, operation_type=None):
    """リクエスト成功確認のヘルパー"""
    assert result.is_success()
    if operation_type:
        assert result.op == operation_type


@pytest.fixture
def temp_workspace():
    """テスト用の一時ワークスペースを提供"""
    with tempfile.TemporaryDirectory() as temp_dir:
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        try:
            yield Path(temp_dir)
        finally:
            os.chdir(old_cwd)


@pytest.fixture
def mock_infrastructure():
    """統一されたモックインフラストラクチャを提供"""
    return build_mock_infrastructure()


@pytest.fixture
def mock_drivers(mock_infrastructure):
    """個別のモックドライバーを提供"""
    return {
        'file_driver': mock_infrastructure.resolve('file_driver'),
        'shell_driver': mock_infrastructure.resolve('shell_driver'),
        'docker_driver': mock_infrastructure.resolve('docker_driver'),
        'python_driver': mock_infrastructure.resolve('python_driver'),
    }


@pytest.fixture
def clean_mock_state(mock_drivers):
    """テスト実行前にモック状態をクリア"""
    # ファイルドライバーのクリア
    file_driver = mock_drivers['file_driver']
    file_driver.files.clear()
    file_driver.contents.clear()
    file_driver.operations.clear()

    # シェルドライバーのクリア
    shell_driver = mock_drivers['shell_driver']
    shell_driver._commands_executed.clear()

    # ドッカードライバーのクリア
    docker_driver = mock_drivers['docker_driver']
    if hasattr(docker_driver, 'clear_history'):
        docker_driver.clear_history()

    # Pythonドライバーのクリア
    python_driver = mock_drivers['python_driver']
    if hasattr(python_driver, 'clear_history'):
        python_driver.clear_history()

    yield mock_drivers


@pytest.fixture(scope="module")
def fast_sqlite_manager():
    """Shared FastSQLiteManager for persistence tests with in-memory database."""
    from src.infrastructure.persistence.sqlite.fast_sqlite_manager import FastSQLiteManager

    manager = FastSQLiteManager(db_path=":memory:", skip_migrations=False)
    yield manager
    # Cleanup after module
    FastSQLiteManager.reset_shared_connection()


@pytest.fixture
def clean_sqlite_manager(fast_sqlite_manager):
    """Clean FastSQLiteManager for each test."""
    # Clean data before test
    fast_sqlite_manager.cleanup_test_data()
    yield fast_sqlite_manager
    # Clean data after test
    fast_sqlite_manager.cleanup_test_data()
