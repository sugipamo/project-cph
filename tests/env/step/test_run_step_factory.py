import pytest
from src.env.step.run_step_factory import RunStepFactory
from src.env.step.run_step_build import BuildRunStep

def test_run_step_factory_from_dict_ok():
    d = {"type": "build", "cmd": ["make"]}
    step = RunStepFactory.from_dict(d)
    assert isinstance(step, BuildRunStep)
    assert step.cmd == ["make"]

def test_run_step_factory_from_dict_ng():
    d = {"type": "notype", "cmd": ["a"]}
    with pytest.raises(KeyError):
        RunStepFactory.from_dict(d)

def test_run_step_factory_from_dict_shell():
    """Test with shell type"""
    d = {"type": "shell", "cmd": ["echo", "test"]}
    step = RunStepFactory.from_dict(d)
    assert step.type == "shell"
    assert step.cmd == ["echo", "test"]

def test_run_step_factory_from_dict_with_optional_fields():
    """Test with all optional fields"""
    d = {
        "type": "shell",
        "cmd": ["ls"],
        "force_env_type": "docker",
        "allow_failure": True,
        "show_output": False,
        "cwd": "/tmp"
    }
    step = RunStepFactory.from_dict(d)
    assert step.type == "shell"
    assert step.cmd == ["ls"]
    assert step.force_env_type == "docker"
    assert step.allow_failure is True
    assert step.show_output is False
    assert step.cwd == "/tmp"

def test_run_step_factory_from_dict_minimal():
    """Test with minimal required fields"""
    d = {"type": "shell"}
    step = RunStepFactory.from_dict(d)
    assert step.type == "shell"
    assert step.cmd == []

def test_run_step_factory_from_dict_none_type():
    """Test with None type value - should raise KeyError"""
    d = {"cmd": ["echo"]}  # no type key
    with pytest.raises(KeyError):
        RunStepFactory.from_dict(d) 