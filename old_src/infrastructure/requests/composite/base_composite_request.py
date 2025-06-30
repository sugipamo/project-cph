"""Base composite request class."""
from typing import Optional

from old_src.infrastructure.requests.base.base_request import OperationRequestFoundation
from old_src.operations.constants.operation_type import OperationType
from old_src.operations.constants.request_types import RequestType


class CompositeRequestFoundation(OperationRequestFoundation):
    """Foundation class for composite requests that contain multiple sub-requests.

    This class provides the foundation for requests that aggregate multiple operations
    into a single executable unit with proper result tracking.
    """

    def __init__(self, requests: list[OperationRequestFoundation], debug_tag: Optional[str], name: Optional[str]):
        super().__init__(name=name, debug_tag=debug_tag)
        if not all(isinstance(r, OperationRequestFoundation) for r in requests):
            raise TypeError("All elements of 'requests' must be OperationRequestFoundation (or its subclass)")
        self.requests = requests
        self._results = []

    def set_name(self, name: str) -> 'CompositeRequestFoundation':
        """Set the name of this request."""
        self.name = name
        return self

    def __len__(self) -> int:
        return len(self.requests)

    @property
    def operation_type(self) -> OperationType:
        return OperationType.COMPOSITE

    @property
    def request_type(self) -> RequestType:
        """Return the request type for type-safe identification."""
        return RequestType.COMPOSITE_REQUEST_FOUNDATION

    def __repr__(self) -> str:
        reqs_str = ",\n  ".join(repr(r) for r in self.requests)
        return f"<{self.request_type.short_name} name={self.name} [\n  {reqs_str}\n]>"

    @classmethod
    def make_composite_request(cls, requests: list[OperationRequestFoundation], debug_tag: Optional[str],
                             name: Optional[str]) -> OperationRequestFoundation:
        if len(requests) == 1:
            req = requests[0]
            if name is not None:
                req = req.set_name(name)
            return req
        return cls(requests, debug_tag=debug_tag, name=name)

    def count_leaf_requests(self) -> int:
        count = 0
        for req in self.requests:
            if isinstance(req, CompositeRequestFoundation):
                count += req.count_leaf_requests()
            else:
                count += 1
        return count

