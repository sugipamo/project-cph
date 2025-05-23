from src.operations.base_request import BaseRequest
from src.operations.constants.operation_type import OperationType
from src.operations.composite_step_failure import CompositeStepFailure
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    
    def __len__(self):
        return len(self.requests)

    @property
    def operation_type(self):
        return OperationType.COMPOSITE

    def execute(self, driver):
        if self._executed:
            raise RuntimeError("This CompositeRequest has already been executed.")
        results = []
        for req in self.requests:
            result = req.execute(driver=driver)
            # show_output属性がTrueなら出力を表示
            if hasattr(req, 'show_output') and req.show_output:
                if hasattr(result, 'stdout') and result.stdout:
                    print(result.stdout, end="")
                if hasattr(result, 'stderr') and result.stderr:
                    print(result.stderr, end="")
            results.append(result)
            # allow_failureがFalseまたは未指定、かつ失敗した場合は即停止
            allow_failure = getattr(req, 'allow_failure', False)
            if not allow_failure and not (hasattr(result, 'success') and result.success):
                raise CompositeStepFailure(f"Step failed: {req} (allow_failure=False)\nResult: {result}")
        self._results = results
        self._executed = True
        return results

    def __repr__(self):
        reqs_str = ",\n  ".join(repr(r) for r in self.requests)
        return f"<CompositeRequest name={self.name} [\n  {reqs_str}\n]>"

    @classmethod
    def make_composite_request(cls, requests, debug_tag=None, name=None):
        """
        requestsが1つだけならそのまま返し、2つ以上ならCompositeRequestでラップして返す。
        ただし、nameが指定されている場合はset_nameを呼ぶ。
        """
        if len(requests) == 1:
            req = requests[0]
            if name is not None:
                req = req.set_name(name)
            return req
        return cls(requests, debug_tag=debug_tag, name=name)

    def count_leaf_requests(self):
        """
        再帰的に全ての葉(BaseRequestでCompositeRequestでないもの)の数を数える。
        """
        count = 0
        for req in self.requests:
            if isinstance(req, CompositeRequest):
                count += req.count_leaf_requests()
            else:
                count += 1
        return count
