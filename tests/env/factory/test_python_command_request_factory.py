import pytest
from src.env.factory.python_command_request_factory import PythonCommandRequestFactory
from src.env.step.run_step_python import PythonRunStep
from src.operations.python.python_request import PythonRequest

class DummyConstHandler:
    def parse(self, s):
        return f"parsed:{s}"
class DummyController:
    const_handler = DummyConstHandler()
class DummyRunStep:
    pass

def make_python_run_step(cmd, cwd=None, show_output=True):
    step = PythonRunStep(type="python", cmd=cmd, cwd=cwd, show_output=show_output)
    return step

def test_create_request_normal():
    factory = PythonCommandRequestFactory(controller=DummyController())
    step = make_python_run_step(["code.py"], cwd="/tmp", show_output=False)
    req = factory.create_request(step)
    assert isinstance(req, PythonRequest)
    assert req.code_or_file == ["parsed:code.py"]
    assert req.cwd == "parsed:/tmp"
    assert req.show_output is False

def test_create_request_default_show_output():
    factory = PythonCommandRequestFactory(controller=DummyController())
    step = make_python_run_step(["code.py"])
    req = factory.create_request(step)
    assert req.show_output is True

def test_create_request_type_error():
    factory = PythonCommandRequestFactory(controller=DummyController())
    with pytest.raises(TypeError):
        factory.create_request(DummyRunStep()) 