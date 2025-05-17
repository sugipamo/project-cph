from src.operations.operation_type import OperationType

class CompositeRequest:
    def __init__(self, requests):
        self.requests = requests
        self._executed = False
        self._results = None

    @property
    def operation_type(self):
        return OperationType.COMPOSITE

    def execute(self):
        if self._executed:
            raise RuntimeError("This CompositeRequest has already been executed.")
        results = []
        for req in self.requests:
            results.append(req.execute())
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