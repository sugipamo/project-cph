from src.operations.operation_type import OperationType
import inspect
import os
from src.operations.request_debug_info_mixin import RequestDebugInfoMixin

class CompositeRequest(RequestDebugInfoMixin):
    def __init__(self, requests, debug_tag=None):
        self.requests = requests
        self._executed = False
        self._results = None
        self._set_debug_info(debug_tag)

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
        return f"<CompositeRequest [\n  {reqs_str}\n]>"

def flatten_results(results):
    flat = []
    for r in results:
        if isinstance(r, list):
            flat.extend(flatten_results(r))
        else:
            flat.append(r)
    return flat 