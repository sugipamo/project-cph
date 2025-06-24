"""パス情報の集約"""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExecutionPaths:
    """パス情報の集約"""
    local_workspace: Path
    contest_current: Path
    contest_stock: Path
    contest_template: Path
    contest_temp: Path
