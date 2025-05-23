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