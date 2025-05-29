import pytest
from src.env.factory.remove_command_request_factory import RemoveCommandRequestFactory
from src.env.step.run_step_remove import RemoveRunStep
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
    return RemoveCommandRequestFactory(MockController())


def test_create_request_success(factory):
    step = RemoveRunStep(type="remove", target="test.txt")
    
    req = factory.create_request(step)
    
    assert isinstance(req, FileRequest)
    assert req.op_type == FileOpType.REMOVE
    assert req.path == "test.txt"


def test_create_request_wrong_type(factory):
    class WrongStep:
        pass
    
    step = WrongStep()
    with pytest.raises(TypeError) as excinfo:
        factory.create_request(step)
    assert "RemoveCommandRequestFactory expects RemoveRunStep" in str(excinfo.value)