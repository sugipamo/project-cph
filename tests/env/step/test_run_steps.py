from src.env.step.run_steps import RunSteps
from src.env.step.run_step_build import BuildRunStep

def test_run_steps_from_list_and_iter():
    lst = [
        {"type": "build", "cmd": ["make"]},
        {"type": "build", "cmd": ["cmake"]}
    ]
    steps = RunSteps.from_list(lst)
    assert isinstance(steps[0], BuildRunStep)
    assert len(steps) == 2
    assert [s.cmd for s in steps] == [["make"], ["cmake"]]

def test_run_steps_validate_all():
    lst = [
        {"type": "build", "cmd": ["make"]},
        {"type": "build", "cmd": ["cmake"]}
    ]
    steps = RunSteps.from_list(lst)
    steps.validate_all() 