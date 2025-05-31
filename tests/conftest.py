"""
共通テストフィクスチャの定義
テストコードの重複を削減し、保守性を向上させる
"""
import pytest
from src.operations.di_container import DIContainer


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
    from src.operations.docker.docker_request import DockerRequest, DockerOpType
    from src.operations.file.file_request import FileRequest
    from src.operations.file.file_op_type import FileOpType
    from src.operations.shell.shell_request import ShellRequest
    from src.operations.python.python_request import PythonRequest
    
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