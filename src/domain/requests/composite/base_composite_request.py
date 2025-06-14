"""Base composite request class."""
from typing import Optional

from src.domain.constants.operation_type import OperationType
from src.domain.requests.base.base_request import BaseRequest


class BaseCompositeRequest(BaseRequest):
    """Base class for composite requests that contain multiple sub-requests."""

    def __init__(self, requests: list[BaseRequest], debug_tag: Optional[str] = None, name: Optional[str] = None, _executed: bool = False, _results = None, _debug_info: Optional[dict] = None):
        super().__init__(name=name, debug_tag=debug_tag, _executed=_executed, _result=None, _debug_info=_debug_info)
        if not all(isinstance(r, BaseRequest) for r in requests):
            raise TypeError("All elements of 'requests' must be BaseRequest (or its subclass)")
        self.requests = requests
        self._results = _results

    def set_name(self, name: str) -> 'BaseCompositeRequest':
        """Set the name of this request."""
        self.name = name
        return self

    def __len__(self) -> int:
        return len(self.requests)

    @property
    def operation_type(self) -> OperationType:
        return OperationType.COMPOSITE

    def __repr__(self) -> str:
        reqs_str = ",\n  ".join(repr(r) for r in self.requests)
        return f"<{self.__class__.__name__} name={self.name} [\n  {reqs_str}\n]>"

    @classmethod
    def make_composite_request(cls, requests: list[BaseRequest], debug_tag: Optional[str] = None,
                             name: Optional[str] = None) -> BaseRequest:
        if len(requests) == 1:
            req = requests[0]
            if name is not None:
                req = req.set_name(name)
            return req
        return cls(requests, debug_tag=debug_tag, name=name)

    def count_leaf_requests(self) -> int:
        count = 0
        for req in self.requests:
            if isinstance(req, BaseCompositeRequest):
                count += req.count_leaf_requests()
            else:
                count += 1
        return count
