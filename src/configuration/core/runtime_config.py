"""実行時設定"""
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class RuntimeConfig:
    """実行時設定"""
    language_id: str
    source_file_name: str
    run_command: str
    timeout_seconds: int
    retry_settings: Dict[str, Any]
