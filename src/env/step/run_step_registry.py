from typing import Type, Dict
from src.env.step.run_step_base import RunStep

RUN_STEP_TYPE_MAP: Dict[str, Type[RunStep]] = {}

def register_run_step_type(type_name: str):
    def decorator(cls):
        RUN_STEP_TYPE_MAP[type_name] = cls
        return cls
    return decorator 