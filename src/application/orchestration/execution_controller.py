"""Execution control class
"""
from typing import Any

from src.domain.exceptions.composite_step_failure import CompositeStepFailureError


class ExecutionController:
    """Responsible for controlling request execution"""

    def execute_requests(self, requests: list[Any], driver: Any) -> list[Any]:
        """Execute a list of requests sequentially

        Args:
            requests: List of requests to execute
            driver: Execution driver

        Returns:
            List of execution results
        """
        results = []
        for _i, req in enumerate(requests):
            # Display step name if available
            if hasattr(req, '_step_name') and req._step_name:
                print(f"\n▶ {req._step_name}")

            result = req.execute_operation(driver=driver)
            results.append(result)
            self._check_failure(req, result)

        return results

    def _check_failure(self, request: Any, result: Any) -> None:
        """Check execution result for failure and raise exception if necessary

        Args:
            request: Executed request
            result: Execution result
        """
        # If allow_failure is False or unspecified and operation failed, stop immediately
        allow_failure = getattr(request, 'allow_failure', False)
        if not allow_failure and not (hasattr(result, 'success') and result.success):
            raise CompositeStepFailureError(
                f"Step failed: {request} (allow_failure=False)\nResult: {result}",
                result=result
            )
