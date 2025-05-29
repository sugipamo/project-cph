import pytest
from src.env.factory.mkdir_command_request_factory import MkdirCommandRequestFactory
from src.env.step.run_step_mkdir import MkdirRunStep
from src.operations.file.file_request import FileRequest, FileOpType


class MockController:
    def __init__(self):
        self.env_context = type("EnvContext", (), {
            "contest_name": "test_contest",
            "problem_name": "a",
            "language": "python",
            "command_type": "test",
            "env_type": "local"
        })()


@pytest.fixture
def factory():
    return MkdirCommandRequestFactory(MockController())


def test_create_request_success(factory):
    step = MkdirRunStep(type="mkdir", cmd=["new_directory"])
    # format_stringメソッドをモック
    factory.format_string = lambda s: f"formatted_{s}"
    
    req = factory.create_request(step)
    
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.MKDIR
    assert req.path == "formatted_new_directory"


def test_create_request_wrong_type(factory):
    class WrongStep:
        pass
    
    step = WrongStep()
    with pytest.raises(TypeError) as excinfo:
        factory.create_request(step)
    assert "MkdirCommandRequestFactory expects MkdirRunStep" in str(excinfo.value)