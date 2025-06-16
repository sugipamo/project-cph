"""Composite request implementation."""
from typing import Any, Optional

from src.operations.constants.request_types import RequestType
from src.operations.interfaces.execution_interface import ExecutionInterface
from src.operations.requests.base.base_request import OperationRequestFoundation
from src.operations.requests.composite.base_composite_request import CompositeRequestFoundation
from src.operations.requests.composite.composite_structure import CompositeStructure


class CompositeRequest(CompositeRequestFoundation):
    """Composite request that contains multiple sub-requests."""

    def __init__(self, requests: list[OperationRequestFoundation], debug_tag: Optional[str] = None, name: Optional[str] = None,
                 execution_controller: Optional[ExecutionInterface] = None, _executed: bool = False, _results = None, _debug_info: Optional[dict] = None):
        # Initialize structure first before calling super().__init__
        self.structure = CompositeStructure(requests)
        self.execution_controller = execution_controller  # Will be injected from infrastructure
        # Now call super().__init__ which tries to set self.requests
        super().__init__(requests, name=name, debug_tag=debug_tag, _executed=_executed, _results=_results, _debug_info=_debug_info)

    def __len__(self) -> int:
        return len(self.structure)

    @property
    def requests(self) -> list[OperationRequestFoundation]:
        return self.structure.requests

    @requests.setter
    def requests(self, value: list[OperationRequestFoundation]) -> None:
        # Update the structure when requests is set
        if hasattr(self, 'structure'):
            self.structure = CompositeStructure(value)
        else:
            # This will be called during initialization
            pass

    @property
    def request_type(self) -> RequestType:
        """Return the request type for type-safe identification."""
        return RequestType.COMPOSITE_REQUEST

    def execute_composite_operation(self, driver: Any) -> list[Any]:
        return super().execute_operation(driver)


    def _execute_core(self, driver: Any) -> list[Any]:
        results = []
        for req in self.requests:
            result = req.execute_operation(driver=driver)

            # Handle output directly using OutputManager static method
            # Note: show_output is now used for step details display, not immediate output
            # if hasattr(req, 'show_output') and req.show_output:
            #     from src.application.orchestration.output_manager import OutputManager
            #     OutputManager.handle_request_output(req, result)

            results.append(result)

            # Check failure if execution controller is available
            if self.execution_controller and hasattr(self.execution_controller, '_check_failure'):
                self.execution_controller._check_failure(req, result)

        return results

    def execute_parallel(self, driver: Any, max_workers: int = 4) -> list[Any]:
        """Execute requests in parallel using ThreadPoolExecutor"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def execute_request(req):
            result = req.execute_operation(driver=driver)
            # Check failure if execution controller is available
            if self.execution_controller and hasattr(self.execution_controller, '_check_failure'):
                self.execution_controller._check_failure(req, result)
            return result

        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all requests for parallel execution
            future_to_index = {executor.submit(execute_request, req): i for i, req in enumerate(self.requests)}

            # Collect results in original order
            results = [None] * len(self.requests)
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                results[index] = future.result()

        return results

    def __repr__(self) -> str:
        return f"<CompositeRequest name={self.name} {self.structure}>"

    @classmethod
    def make_composite_request(cls, requests: list[OperationRequestFoundation], debug_tag: Optional[str] = None,
                             name: Optional[str] = None) -> OperationRequestFoundation:
        """If requests has only one item, return it as-is; if two or more, wrap in CompositeRequest.
        However, if name is specified, call set_name.
        """
        if len(requests) == 1:
            req = requests[0]
            if name is not None:
                req = req.set_name(name)
            return req
        return cls(requests, debug_tag=debug_tag, name=name)

    def count_leaf_requests(self) -> int:
        """Recursively count all leaves (CompositeRequestFoundation that are not CompositeRequest).
        """
        return self.structure.count_leaf_requests()
