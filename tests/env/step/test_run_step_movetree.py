import pytest
from src.env.step.run_step_movetree import MoveTreeRunStep
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

def test_movetree_command_request_factory_parse():
    step = MoveTreeRunStep(type="movetree", cmd=["{workspace_path}/adir", "{workspace_path}/bdir"])
    factory = UnifiedCommandRequestFactory(MockController())
    factory.format_string = lambda s: s.replace("{workspace_path}", "/home/user/workspace")
    req = factory.create_request(step)
    assert req.path == "/home/user/workspace/adir"
    assert req.dst_path == "/home/user/workspace/bdir" 