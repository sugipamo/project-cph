import pytest
from src.env.step.run_step_build import BuildRunStep

def test_build_run_step_validate_ok():
    step = BuildRunStep(type="build", cmd=["make"])
    assert step.validate() is True
    step2 = BuildRunStep(type="build", cmd=None)
    assert step2.validate() is True

def test_build_run_step_validate_ng():
    step = BuildRunStep(type="build", cmd="notalist")
    with pytest.raises(ValueError):
        step.validate() 