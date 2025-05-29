import pytest
from src.env.factory.python_command_request_factory import PythonCommandRequestFactory
from src.env.step.run_step_python import PythonRunStep
from src.operations.python.python_request import PythonRequest

class DummyController:
    def __init__(self):
        self.env_context = type("EnvContext", (), {
            "contest_name": "test",
            "problem_name": "a",
            "language": "python",
            "env_type": "local",
            "command_type": "test",
            "resolver": None
        })()
class DummyRunStep:
    pass

def make_python_run_step(cmd, cwd=None, show_output=True):
    step = PythonRunStep(type="python", cmd=cmd, cwd=cwd, show_output=show_output)
    return step

def test_create_request_normal():
    factory = PythonCommandRequestFactory(controller=DummyController())
    factory.format_string = lambda s: f"parsed:{s}"
    step = make_python_run_step(["code.py"], cwd="/tmp", show_output=False)
    req = factory.create_request(step)
    assert isinstance(req, PythonRequest)
    assert req.code_or_file == ["parsed:code.py"]
    assert req.cwd == "parsed:/tmp"
    assert req.show_output is False

def test_create_request_default_show_output():
    factory = PythonCommandRequestFactory(controller=DummyController())
    factory.format_string = lambda s: f"parsed:{s}"
    step = make_python_run_step(["code.py"])
    req = factory.create_request(step)
    assert req.show_output is True

def test_create_request_type_error():
    factory = PythonCommandRequestFactory(controller=DummyController())
    with pytest.raises(TypeError):
        factory.create_request(DummyRunStep()) 