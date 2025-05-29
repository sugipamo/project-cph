import pytest
from src.env.step.run_step_rmtree import RmtreeRunStep
from src.env.factory.rmtree_command_request_factory import RmtreeCommandRequestFactory

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

def test_rmtree_run_step_validate_ok():
    step = RmtreeRunStep(type="rmtree", cmd=["dir1"])
    assert step.validate() is True

def test_rmtree_run_step_validate_ng():
    step = RmtreeRunStep(type="rmtree", cmd=None)
    with pytest.raises(ValueError):
        step.validate()
    step2 = RmtreeRunStep(type="rmtree", cmd=[])
    with pytest.raises(ValueError):
        step2.validate()

def test_rmtree_run_step_target():
    step = RmtreeRunStep(type="rmtree", cmd=["dir1"])
    assert step.target == "dir1"

def test_rmtree_command_request_factory_parse():
    step = RmtreeRunStep(type="rmtree", cmd=["{workspace_path}/test"])
    factory = RmtreeCommandRequestFactory(MockController())
    req = factory.create_request(step)
    # Currently no format processing, so path should remain as is
    assert req.path == "{workspace_path}/test" 