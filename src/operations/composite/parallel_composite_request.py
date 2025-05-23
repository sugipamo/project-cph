from src.operations.composite.composite_request import CompositeRequest
from concurrent.futures import ThreadPoolExecutor, as_completed

class ParallelCompositeRequest(CompositeRequest):
    def __init__(self, requests, debug_tag=None, name=None, max_workers=None):
        super().__init__(requests, debug_tag=debug_tag, name=name)
        self.max_workers = max_workers

    def execute(self, driver):
        if self._executed:
            raise RuntimeError("This ParallelCompositeRequest has already been executed.")
        results = [None] * len(self.requests)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx = {executor.submit(req.execute, driver): idx for idx, req in enumerate(self.requests)}
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    self._executed = True
                    raise
        self._results = results
        self._executed = True
        return results

    def __repr__(self):
        reqs_str = ",\n  ".join(repr(r) for r in self.requests)
        return f"<ParallelCompositeRequest name={self.name} [\n  {reqs_str}\n]>" 