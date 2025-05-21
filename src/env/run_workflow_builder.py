from src.operations.composite_request import CompositeRequest
from src.env.request_factory import create_requests_from_run_steps
from src.env.step.run_step_shell import ShellRunStep
from src.env.step.run_step_oj import OjRunStep
from src.operations.di_container import DIContainer
from src.env.types import EnvResourceController, RunSteps, CompositeRequest

class RunWorkflowBuilder:
    def __init__(self, controller: EnvResourceController, di_container: DIContainer):
        self.controller = controller
        self.di_container = di_container

    @classmethod
    def from_controller(cls, controller: EnvResourceController) -> 'RunWorkflowBuilder':
        """
        controllerから本番用DIContainerをセットアップしてRunWorkflowBuilderを生成
        """
        from src.operations.docker.docker_request import DockerRequest, DockerOpType
        di = DIContainer()
        di.register("DockerRequest", lambda: DockerRequest)
        di.register("DockerOpType", lambda: DockerOpType)
        # 他の本番用依存も必要に応じて登録
        return cls(controller, di)

    def build(self, run_steps: RunSteps) -> CompositeRequest:
        """
        run_steps: RunSteps型
        """
        requests = []
        # 1. 必要ならビルドrequestを先頭に追加
        if self.needs_docker_build(run_steps):
            build_req = self.create_docker_build_request()
            requests.append(build_req)
        # 2. 各run_stepからrequest生成
        step_requests = create_requests_from_run_steps(self.controller, run_steps, self.di_container)
        # step_requestsがCompositeRequestなら展開、単体ならそのまま
        if isinstance(step_requests, CompositeRequest):
            requests.extend(step_requests.requests)
        else:
            requests.append(step_requests)
        return CompositeRequest.make_composite_request(requests)

    def needs_docker_build(self, run_steps: RunSteps) -> bool:
        """
        run_steps内にDockerRequestが必要なstep（docker環境のshell/oj等）が含まれていればTrue
        """
        env_type = getattr(self.controller.env_context, "env_type", "local").lower()
        if env_type != "docker":
            return False
        # shell/oj系stepが1つでもあればビルド必要とみなす（仮実装）
        for step in run_steps:
            if isinstance(step, (ShellRunStep, OjRunStep)):
                return True
        return False

    def create_docker_build_request(self) -> object:
        """
        docker build用のDockerRequestを生成（DIContainerからクラスを解決）
        """
        image_name = self.controller.const_handler.image_name
        dockerfile_text = self.controller.const_handler.dockerfile_text
        DockerRequest = self.di_container.resolve("DockerRequest")
        DockerOpType = self.di_container.resolve("DockerOpType")
        return DockerRequest(
            DockerOpType.RUN,
            image=image_name,
            options={"dockerfile": dockerfile_text}
        ) 