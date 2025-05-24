import pytest
from src.env.step.run_step_mkdir import MkdirRunStep

def test_mkdir_run_step_validate_ok():
    step = MkdirRunStep(type="mkdir", cmd=["dir1"])
    assert step.validate() is True

def test_mkdir_run_step_validate_ng():
    step = MkdirRunStep(type="mkdir", cmd=None)
    with pytest.raises(ValueError):
        step.validate()
    step2 = MkdirRunStep(type="mkdir", cmd=[])
    with pytest.raises(ValueError):
        step2.validate()

def test_mkdir_run_step_target():
    step = MkdirRunStep(type="mkdir", cmd=["dir1"])
    assert step.target == "dir1" 