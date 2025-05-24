import pytest
from src.env.step.run_step_touch import TouchRunStep

def test_touch_run_step_validate_ok():
    step = TouchRunStep(type="touch", cmd=["file1.txt"])
    assert step.validate() is True

def test_touch_run_step_validate_ng():
    step = TouchRunStep(type="touch", cmd=None)
    with pytest.raises(ValueError):
        step.validate()
    step2 = TouchRunStep(type="touch", cmd=[])
    with pytest.raises(ValueError):
        step2.validate()

def test_touch_run_step_target():
    step = TouchRunStep(type="touch", cmd=["file1.txt"])
    assert step.target == "file1.txt" 