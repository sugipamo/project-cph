import pytest
from src.env.factory.rmtree_command_request_factory import RmtreeCommandRequestFactory
from src.env.step.run_step_rmtree import RmtreeRunStep
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
    return RmtreeCommandRequestFactory(MockController())


def test_create_request_success(factory):
    step = RmtreeRunStep(type="rmtree", cmd=["test_dir"])
    
    req = factory.create_request(step)
    
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.RMTREE
    assert req.path == "test_dir"


def test_create_request_wrong_type(factory):
    class WrongStep:
        pass
    
    step = WrongStep()
    with pytest.raises(TypeError) as excinfo:
        factory.create_request(step)
    assert "RmtreeCommandRequestFactory expects RmtreeRunStep" in str(excinfo.value)