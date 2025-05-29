import pytest
from src.env.factory.touch_command_request_factory import TouchCommandRequestFactory
from src.env.step.run_step_touch import TouchRunStep
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
    return TouchCommandRequestFactory(MockController())


def test_create_request_success(factory):
    step = TouchRunStep(type="touch", cmd=["new_file.txt"])
    # format_stringメソッドをモック
    factory.format_string = lambda s: f"formatted_{s}"
    
    req = factory.create_request(step)
    
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.TOUCH
    assert req.path == "formatted_new_file.txt"


def test_create_request_wrong_type(factory):
    class WrongStep:
        pass
    
    step = WrongStep()
    with pytest.raises(TypeError) as excinfo:
        factory.create_request(step)
    assert "TouchCommandRequestFactory expects TouchRunStep" in str(excinfo.value)