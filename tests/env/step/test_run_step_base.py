import pytest
from src.env.step.run_step_base import RunStep


def test_run_step_from_dict():
    """Test RunStep.from_dict class method"""
    data = {
        "type": "test",
        "cmd": ["echo", "hello"],
        "force_env_type": "local",
        "allow_failure": True,
        "show_output": False,
        "cwd": "/test/dir"
    }
    
    step = RunStep.from_dict(data)
    
    assert step.type == "test"
    assert step.cmd == ["echo", "hello"]
    assert step.force_env_type == "local"
    assert step.allow_failure is True
    assert step.show_output is False
    assert step.cwd == "/test/dir"


def test_run_step_from_dict_minimal():
    """Test RunStep.from_dict with minimal data"""
    data = {"type": "test"}
    
    step = RunStep.from_dict(data)
    
    assert step.type == "test"
    assert step.cmd == []
    assert step.force_env_type is None
    assert step.allow_failure is None  # from_dict returns None when not specified
    assert step.show_output is None   # from_dict returns None when not specified  
    assert step.cwd is None


def test_run_step_validate():
    """Test RunStep.validate method"""
    step = RunStep(type="test")
    assert step.validate() is True