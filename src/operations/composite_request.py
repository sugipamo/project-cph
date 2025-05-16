class CompositeRequest:
    def __init__(self, requests):
        self.requests = requests
        self._executed = False
        self._results = None

    def execute(self):
        if self._executed:
            raise RuntimeError("This CompositeRequest has already been executed.")
        results = []
        for req in self.requests:
            results.append(req.execute())
        self._results = results
        self._executed = True
        return results 