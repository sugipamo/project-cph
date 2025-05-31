from src.operations.composite.base_composite_request import BaseCompositeRequest
from src.operations.composite.execution_controller import ExecutionController
from src.operations.composite.output_manager import OutputManager
from src.operations.composite.composite_structure import CompositeStructure
from src.operations.base_request import BaseRequest

class CompositeRequest(BaseCompositeRequest):
    def __init__(self, requests, debug_tag=None, name=None):
        super().__init__(requests, name=name, debug_tag=debug_tag)
        self.structure = CompositeStructure(requests)
        self.execution_controller = ExecutionController()
        self._executed = False
        self._results = None

    def __len__(self):
        return len(self.structure)
    
    @property
    def requests(self):
        return self.structure.requests

    def execute(self, driver):
        return super().execute(driver)

    def _execute_core(self, driver):
        results = []
        for req in self.requests:
            result = req.execute(driver=driver)
            OutputManager.handle_request_output(req, result)
            results.append(result)
            
            # allow_failureチェックは ExecutionController に委譲
            self.execution_controller._check_failure(req, result)
        
        self._results = results
        return results

    def __repr__(self):
        return f"<CompositeRequest name={self.name} {self.structure}>"

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
        再帰的に全ての葉(BaseCompositeRequestでCompositeRequestでないもの)の数を数える。
        """
        return self.structure.count_leaf_requests()
