from typing import List, Dict, Any
from src.env.step.run_step_base import RunStep
from src.env.step.run_step_factory import RunStepFactory

class RunSteps:
    """
    複数のRunStepを管理するクラス。
    from_listでdictリストから生成、filterやバリデーションも提供。
    """
    def __init__(self, steps: List[RunStep]):
        self.steps = steps

    @classmethod
    def from_list(cls, lst: List[Dict[str, Any]]) -> "RunSteps":
        return cls([RunStepFactory.from_dict(d) for d in lst])

    def __iter__(self):
        return iter(self.steps)

    def __getitem__(self, idx):
        return self.steps[idx]

    def __len__(self):
        return len(self.steps)

    def validate_all(self) -> None:
        for step in self.steps:
            if hasattr(step, "validate"):
                step.validate() 