"""出力設定"""
from dataclasses import dataclass


@dataclass(frozen=True)
class OutputConfig:
    """出力設定"""
    show_workflow_summary: bool
    show_step_details: bool
    show_execution_completion: bool
    format_preset: str
