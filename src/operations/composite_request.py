from src.operations.base_request import BaseRequest
from src.operations.operation_type import OperationType
import inspect
import os

class CompositeRequest(BaseRequest):
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

    @property
    def operation_type(self):
        return OperationType.COMPOSITE

    def execute(self, driver=None):
        if self._executed:
            raise RuntimeError("This CompositeRequest has already been executed.")
        results = []
        for req in self.requests:
            if hasattr(req, 'execute'):
                try:
                    results.append(req.execute(driver=driver))
                except TypeError:
                    results.append(req.execute())
            else:
                results.append(req)
        self._results = results
        self._executed = True
        return results

    def __repr__(self):
        reqs_str = ",\n  ".join(repr(r) for r in self.requests)
        return f"<CompositeRequest name={self.name} [\n  {reqs_str}\n]>"

def flatten_results(results):
    flat = []
    for r in results:
        if isinstance(r, list):
            flat.extend(flatten_results(r))
        else:
            flat.append(r)
    return flat 