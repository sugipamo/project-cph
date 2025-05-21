from src.operations.composite_request import CompositeRequest
from src.operations.di_container import DIContainer
from src.execution_env.request_factory_selector import RequestFactorySelector
from src.execution_env.command_factories import (
    ShellCommandRequestFactory,
    DockerCommandRequestFactory,
    CopyCommandRequestFactory,
    OjCommandRequestFactory,
    BaseCommandRequestFactory,
)

def create_requests_from_run_steps(controller, run_steps, di_container: DIContainer):
    """
    run_steps: RunSteps型（RunStepのリスト）
    controller: EnvResourceController
    di_container: DIContainer
    """
    requests = []
    for step in run_steps:
        factory = RequestFactorySelector.get_factory_for_step(controller, step, di_container)
        req = factory.create_request(step)
        requests.append(req)
    return CompositeRequest.make_composite_request(requests) 