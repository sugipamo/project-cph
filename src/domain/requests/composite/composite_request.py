"""Composite request implementation."""
from typing import List, Any, Optional
from src.domain.requests.composite.base_composite_request import BaseCompositeRequest
from src.domain.interfaces.execution_interface import ExecutionInterface, OutputInterface
from src.domain.requests.composite.composite_structure import CompositeStructure
from src.domain.requests.base.base_request import BaseRequest


class CompositeRequest(BaseCompositeRequest):
    """Composite request that contains multiple sub-requests."""
    
    def __init__(self, requests: List[BaseRequest], debug_tag: str = None, name: str = None,
                 execution_controller: Optional[ExecutionInterface] = None):
        # Initialize structure first before calling super().__init__
        self.structure = CompositeStructure(requests)
        self.execution_controller = execution_controller  # Will be injected from infrastructure
        self._executed = False
        self._results = None
        # Now call super().__init__ which tries to set self.requests
        super().__init__(requests, name=name, debug_tag=debug_tag)

    def __len__(self) -> int:
        return len(self.structure)
    
    @property
    def requests(self) -> List[BaseRequest]:
        return self.structure.requests
    
    @requests.setter
    def requests(self, value: List[BaseRequest]) -> None:
        # Update the structure when requests is set
        if hasattr(self, 'structure'):
            self.structure = CompositeStructure(value)
        else:
            # This will be called during initialization
            pass

    def execute(self, driver: Any) -> List[Any]:
        return super().execute(driver)

    def _execute_core(self, driver: Any) -> List[Any]:
        results = []
        for req in self.requests:
            result = req.execute(driver=driver)
            
            # Handle output directly using OutputManager static method
            if hasattr(req, 'show_output') and req.show_output:
                from src.application.orchestration.output_manager import OutputManager
                OutputManager.handle_request_output(req, result)
            
            results.append(result)
            
            # Check failure if execution controller is available
            if self.execution_controller and hasattr(self.execution_controller, '_check_failure'):
                self.execution_controller._check_failure(req, result)
        
        self._results = results
        return results

    def __repr__(self) -> str:
        return f"<CompositeRequest name={self.name} {self.structure}>"

    @classmethod
    def make_composite_request(cls, requests: List[BaseRequest], debug_tag: str = None, 
                             name: str = None) -> BaseRequest:
        """
        If requests has only one item, return it as-is; if two or more, wrap in CompositeRequest.
        However, if name is specified, call set_name.
        """
        if len(requests) == 1:
            req = requests[0]
            if name is not None:
                req = req.set_name(name)
            return req
        return cls(requests, debug_tag=debug_tag, name=name)

    def count_leaf_requests(self) -> int:
        """
        Recursively count all leaves (BaseCompositeRequest that are not CompositeRequest).
        """
        return self.structure.count_leaf_requests()