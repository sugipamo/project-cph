import pytest
from src.env.step.run_step_shell import ShellRunStep

def test_shell_run_step_validate_ok():
    step = ShellRunStep(type="shell", cmd=["ls", "-l"])
    assert step.validate() is True

def test_shell_run_step_validate_ng():
    step = ShellRunStep(type="shell", cmd=None)
    with pytest.raises(ValueError):
        step.validate()
    step2 = ShellRunStep(type="shell", cmd="notalist")
    with pytest.raises(ValueError):
        step2.validate() 