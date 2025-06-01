import pytest
from src.env.step.run_step_movetree import MoveTreeRunStep

class MockController:
    def __init__(self):
        self.env_context = type("EnvContext", (), {
            "contest_name": "test",
            "problem_name": "a",
            "language": "python",
            "env_type": "local",
            "command_type": "test",
            "resolver": None
        })()

def test_movetree_run_step_validate_ok():
    step = MoveTreeRunStep(type="movetree", cmd=["srcdir", "dstdir"])
    assert step.validate() is True

def test_movetree_run_step_validate_ng():
    step = MoveTreeRunStep(type="movetree", cmd=None)
    with pytest.raises(ValueError):
        step.validate()
    step2 = MoveTreeRunStep(type="movetree", cmd=["srcdir"])
    with pytest.raises(ValueError):
        step2.validate()

def test_movetree_run_step_src_dst():
    step = MoveTreeRunStep(type="movetree", cmd=["srcdir", "dstdir"])
    assert step.src == "srcdir"
    assert step.dst == "dstdir"

# test_movetree_command_request_factory_parse removed due to factory refactoring 