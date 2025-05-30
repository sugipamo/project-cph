from src.operations.composite.composite_request import CompositeRequest
from src.env.factory.request_factory_selector import RequestFactorySelector
from src.operations.di_container import DIContainer
from src.env.types import EnvResourceController, CompositeRequest
import os

class RunWorkflowBuilder:
    def __init__(self, controller: EnvResourceController, operations: DIContainer):
        self.controller = controller
        self.operations = operations

    @classmethod
    def from_controller(cls, controller: EnvResourceController, operations: DIContainer) -> 'RunWorkflowBuilder':
        """
        controllerとoperationsからRunWorkflowBuilderを生成
        """
        return cls(controller, operations)

    def build_from_nodes(self, step_nodes: list) -> CompositeRequest:
        """
        ConfigNodeのリストからCompositeRequestを生成
        """
        from src.operations.file.file_request import FileRequest
        from src.operations.composite.driver_bound_request import DriverBoundRequest
        
        requests = []
        
        for node in step_nodes:
            if not node.value or not isinstance(node.value, dict):
                continue
                
            step_type = node.value.get('type')
            if not step_type:
                continue
                
            # ファクトリーを取得
            factory = RequestFactorySelector.get_factory_for_step_type(
                step_type, self.controller, self.operations
            )
            if factory:
                request = factory.create_request_from_node(node)
                if request:
                    # FileRequestの場合はfile_driverでラップ
                    if isinstance(request, FileRequest):
                        file_driver = self.operations.resolve('file_driver')
                        request = DriverBoundRequest(request, file_driver)
                    requests.append(request)
        
        return CompositeRequest.make_composite_request(requests)

