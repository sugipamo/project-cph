from src.env.step.run_step_registry import RUN_STEP_TYPE_MAP
from src.env.step.run_step_base import RunStep

class RunStepFactory:
    @staticmethod
    def from_dict(d: dict) -> RunStep:
        type_ = d["type"] if "type" in d else None
        step_cls = RUN_STEP_TYPE_MAP[type_]
        if not step_cls:
            raise ValueError(f"未登録のRunStep type: {type_}")
        # サブクラスのfrom_dictまたはfrom_dict_innerを呼ぶ
        if hasattr(step_cls, "from_dict") and step_cls is not RunStep:
            return step_cls.from_dict(d)
        # fallback: RunStepのfrom_dict_inner
        cmd_ = d["cmd"] if "cmd" in d else []
        extra = {k: v for k, v in d.items() if k not in ("type", "cmd")}
        step = step_cls(type=type_, cmd=cmd_, extra=extra)
        step.validate()
        return step 