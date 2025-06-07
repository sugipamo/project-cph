"""
Execution types for test results
"""
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class ExecutionStatus(Enum):
    """Test execution status"""
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIP = "SKIP"


@dataclass(frozen=True)
class ExecutionResult:
    """Test result data"""
    test_name: str
    status: ExecutionStatus
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None


# Aliases for backward compatibility
TestStatus = ExecutionStatus
TestResult = ExecutionResult