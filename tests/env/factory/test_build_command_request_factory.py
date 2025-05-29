import pytest
from src.env.factory.build_command_request_factory import BuildCommandRequestFactory
from src.env.step.run_step_build import BuildRunStep
from src.operations.shell.shell_request import ShellRequest


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
    return BuildCommandRequestFactory(MockController())


def test_create_request_success(factory):
    step = BuildRunStep(type="build", cmd=["make", "all"])
    
    req = factory.create_request(step)
    
    assert isinstance(req, ShellRequest)
    assert req.cmd == ["make", "all"]


def test_create_request_default_cmd(factory):
    step = BuildRunStep(type="build", cmd=[])
    
    req = factory.create_request(step)
    
    assert isinstance(req, ShellRequest)
    assert req.cmd == ["make"]


def test_create_request_wrong_type(factory):
    class WrongStep:
        pass
    
    step = WrongStep()
    with pytest.raises(TypeError) as excinfo:
        factory.create_request(step)
    assert "BuildCommandRequestFactory expects BuildRunStep" in str(excinfo.value)