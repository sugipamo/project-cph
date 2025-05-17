from src.operations.operation_type import OperationType
import inspect
import os

class RequestDebugInfoMixin:
    def _set_debug_info(self, debug_tag=None):
        if os.environ.get("CPH_DEBUG_REQUEST_INFO", "1") != "1":
            self._debug_info = None
            return
        frame = inspect.stack()[2]
        self._debug_info = {
            "file": frame.filename,
            "line": frame.lineno,
            "function": frame.function,
            "debug_tag": debug_tag,
        }
    def debug_info(self):
        return getattr(self, "_debug_info", None)

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