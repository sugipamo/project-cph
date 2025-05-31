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

def test_move_command_request_factory_parse():
    step = MoveRunStep(type="move", cmd=["{workspace_path}/a.txt", "{workspace_path}/b.txt"])
    factory = UnifiedCommandRequestFactory(MockController())
    factory.format_string = lambda s: s.replace("{workspace_path}", "/home/user/workspace")
    req = factory.create_request(step)
    assert req.path == "/home/user/workspace/a.txt"
    assert req.dst_path == "/home/user/workspace/b.txt" 