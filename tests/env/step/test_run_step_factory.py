import pytest
from src.env.step.run_step_factory import RunStepFactory
from src.env.step.run_step_build import BuildRunStep

def test_run_step_factory_from_dict_ok():
    d = {"type": "build", "cmd": ["make"]}
    step = RunStepFactory.from_dict(d)
    assert isinstance(step, BuildRunStep)
    assert step.cmd == ["make"]

def test_run_step_factory_from_dict_ng():
    d = {"type": "notype", "cmd": ["a"]}
    with pytest.raises(KeyError):
        RunStepFactory.from_dict(d) 