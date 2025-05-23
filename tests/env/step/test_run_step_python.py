import pytest
from src.env.step.run_step_python import PythonRunStep

def test_python_run_step_from_dict():
    d = {"type": "python", "cmd": ["print('hi')"], "cwd": "/tmp", "show_output": False}
    step = PythonRunStep.from_dict(d)
    assert step.type == "python"
    assert step.cmd == ["print('hi')"]
    assert step.cwd == "/tmp"
    assert step.show_output is False

def test_python_run_step_validate_ok():
    step = PythonRunStep(type="python", cmd=["print('hi')"])
    assert step.validate() is True

def test_python_run_step_validate_ng_none():
    step = PythonRunStep(type="python", cmd=None)
    with pytest.raises(ValueError):
        step.validate()

def test_python_run_step_validate_ng_notlist():
    step = PythonRunStep(type="python", cmd="notalist")
    with pytest.raises(ValueError):
        step.validate() 