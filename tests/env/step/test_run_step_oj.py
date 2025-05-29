import pytest
from src.env.step.run_step_oj import OjRunStep

def test_oj_run_step_validate_ok():
    step = OjRunStep(type="oj", cmd=["test"])
    assert step.validate() is True

def test_oj_run_step_validate_ng():
    step = OjRunStep(type="oj", cmd=None)
    with pytest.raises(ValueError):
        step.validate()
    step2 = OjRunStep(type="oj", cmd="notalist")
    with pytest.raises(ValueError):
        step2.validate()

def test_oj_run_step_from_dict():
    """Test OjRunStep.from_dict method"""
    data = {
        "type": "oj",
        "cmd": ["oj", "t"],
        "force_env_type": "local",
        "allow_failure": True,
        "show_output": False,
        "cwd": "/tmp"
    }
    
    step = OjRunStep.from_dict(data)
    
    assert step.type == "oj"
    assert step.cmd == ["oj", "t"]
    assert step.force_env_type == "local"
    assert step.allow_failure is True
    assert step.show_output is False
    assert step.cwd == "/tmp"

def test_oj_run_step_repr():
    """Test OjRunStep.__repr__ method"""
    step = OjRunStep(
        type="oj", 
        cmd=["oj", "t"],
        force_env_type="local",
        allow_failure=True,
        show_output=False,
        cwd="/tmp"
    )
    
    repr_str = repr(step)
    assert "OjRunStep" in repr_str
    assert "type=oj" in repr_str
    assert "cmd=['oj', 't']" in repr_str 