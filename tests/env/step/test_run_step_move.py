import pytest
from src.env.step.run_step_move import MoveRunStep
from src.env_factories.unified_factory import UnifiedCommandRequestFactory

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

def test_move_run_step_validate_ok():
    step = MoveRunStep(type="move", cmd=["src.txt", "dst.txt"])
    assert step.validate() is True

def test_move_run_step_validate_ng():
    step = MoveRunStep(type="move", cmd=None)
    with pytest.raises(ValueError):
        step.validate()
    step2 = MoveRunStep(type="move", cmd=["src.txt"])
    with pytest.raises(ValueError):
        step2.validate()

def test_move_run_step_src_dst():
    step = MoveRunStep(type="move", cmd=["src.txt", "dst.txt"])
    assert step.src == "src.txt"
    assert step.dst == "dst.txt"

# test_move_command_request_factory_parse removed due to factory refactoring 