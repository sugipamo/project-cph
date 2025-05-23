class CompositeStepFailure(Exception):
    def __init__(self, message, result=None, original_exception=None):
        super().__init__(message)
        self.result = result
        self.original_exception = original_exception 