from src.operations.composite.composite_request import CompositeRequest
from src.operations.composite.driver_bound_request import DriverBoundRequest
from src.operations.di_container import DIContainer
from src.env.request_factory_selector import RequestFactorySelector
from src.operations.shell.shell_request import ShellRequest
from src.operations.file.file_request import FileRequest
from src.operations.file.local_file_driver import LocalFileDriver
from src.operations.shell.local_shell_driver import LocalShellDriver

def create_requests_from_run_steps(controller, run_steps, operations: DIContainer):
    """
    run_steps: RunSteps型（RunStepのリスト）
    controller: EnvResourceController
    operations: DIContainer
    """
    requests = []
    def safe_resolve(operations, key):
        try:
            return operations.resolve(key) if operations else None
        except KeyError:
            return None
    shell_driver = safe_resolve(operations, 'shell_driver')
    file_driver = safe_resolve(operations, 'file_driver')
    for step in run_steps:
        factory = RequestFactorySelector.get_factory_for_step(controller, step, operations)
        req = factory.create_request(step)
        # ShellRequest/ FileRequest などでdriverを割り当てる
        if isinstance(req, ShellRequest):
            requests.append(DriverBoundRequest(req, shell_driver))
        elif isinstance(req, FileRequest):
            if file_driver is not None:
                requests.append(DriverBoundRequest(req, file_driver))
            else:
                requests.append(req)  # fallback: driver未指定
        else:
            requests.append(req)
    return CompositeRequest.make_composite_request(requests) 