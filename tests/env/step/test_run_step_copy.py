import pytest
from src.env.step.run_step_copy import CopyRunStep

def test_copy_run_step_validate_ok():
    step = CopyRunStep(type="copy", cmd=["src.txt", "dst.txt"])
    assert step.validate() is True

def test_copy_run_step_validate_ng():
    step = CopyRunStep(type="copy", cmd=["src.txt"])
    with pytest.raises(ValueError):
        step.validate()

def test_copy_run_step_src_dst():
    step = CopyRunStep(type="copy", cmd=["src.txt", "dst.txt"])
    assert step.src == "src.txt"
    assert step.dst == "dst.txt" 