import pytest
from src.env.step.run_step_remove import RemoveRunStep

def test_remove_run_step_validate_ok():
    step = RemoveRunStep(type="remove", cmd=["target.txt"])
    assert step.validate() is True

def test_remove_run_step_validate_ng():
    step = RemoveRunStep(type="remove", cmd=None)
    with pytest.raises(ValueError):
        step.validate()
    step2 = RemoveRunStep(type="remove", cmd=[])
    with pytest.raises(ValueError):
        step2.validate()

def test_remove_run_step_target():
    step = RemoveRunStep(type="remove", cmd=["target.txt"])
    assert step.target == "target.txt" 