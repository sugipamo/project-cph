from src.operations.composite_request import CompositeRequest
from src.execution_env.request_factory import create_requests_from_run_steps

class RunWorkflowBuilder:
    def __init__(self, controller):
        self.controller = controller

    def build(self, run_steps):
        # run_steps: RunSteps型
        requests = []
        # 1. 必要ならビルドrequestを先頭に追加
        if self.needs_docker_build(run_steps):
            build_req = self.create_docker_build_request()
            requests.append(build_req)
        # 2. 各run_stepからrequest生成
        step_requests = create_requests_from_run_steps(self.controller, run_steps)
        # step_requestsがCompositeRequestなら展開、単体ならそのまま
        if isinstance(step_requests, CompositeRequest):
            requests.extend(step_requests.requests)
        else:
            requests.append(step_requests)
        return CompositeRequest.make_composite_request(requests)

    def needs_docker_build(self, run_steps):
        # TODO: run_stepsやcontrollerからビルド要否を判定
        return False  # 仮実装

    def create_docker_build_request(self):
        # TODO: controllerやconst_handlerからビルドrequestを生成
        raise NotImplementedError("create_docker_build_requestは未実装です") 