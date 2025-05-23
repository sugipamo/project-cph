from src.operations.base_request import BaseRequest
from src.operations.constants.operation_type import OperationType

class BaseCompositeRequest(BaseRequest):
    def __init__(self, requests, debug_tag=None, name=None):
        super().__init__(name=name, debug_tag=debug_tag)
        if not all(isinstance(r, BaseRequest) for r in requests):
            raise TypeError("All elements of 'requests' must be BaseRequest (or its subclass)")
        self.requests = requests
        self._executed = False
        self._results = None

    def set_name(self, name: str):
        self.name = name
        return self
    
    def __len__(self):
        return len(self.requests)

    @property
    def operation_type(self):
        return OperationType.COMPOSITE

    def __repr__(self):
        reqs_str = ",\n  ".join(repr(r) for r in self.requests)
        return f"<{self.__class__.__name__} name={self.name} [\n  {reqs_str}\n]>"

    @classmethod
    def make_composite_request(cls, requests, debug_tag=None, name=None):
        if len(requests) == 1:
            req = requests[0]
            if name is not None:
                req = req.set_name(name)
            return req
        return cls(requests, debug_tag=debug_tag, name=name)

    def count_leaf_requests(self):
        count = 0
        for req in self.requests:
            if isinstance(req, BaseCompositeRequest):
                count += req.count_leaf_requests()
            else:
                count += 1
        return count 