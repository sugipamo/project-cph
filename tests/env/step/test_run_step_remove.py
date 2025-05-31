import pytest
from src.env.step.run_step_remove import RemoveRunStep
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

def test_remove_run_step_validate_ok():
    step = RemoveRunStep(type="remove", cmd=["target.txt"])
    assert step.validate() is True

def test_remove_run_step_validate_ng():
    step = RemoveRunStep(type="remove", cmd=None)
    with pytest.raises(ValueError):
        step.validate()
    step2 = RemoveRunStep(type="remove", cmd=[])
    with pytest.raises(ValueError):
        step2.validate()

def test_remove_run_step_target():
    step = RemoveRunStep(type="remove", cmd=["target.txt"])
    assert step.target == "target.txt"

def test_remove_command_request_factory_parse():
    step = RemoveRunStep(type="remove", cmd=["{workspace_path}/test"])
    factory = UnifiedCommandRequestFactory(MockController())
    req = factory.create_request(step)
    # Currently no format processing, so path should remain as is
    assert req.path == "{workspace_path}/test" 