from src.env.env_context_with_di import build_di_container_and_context

class EnvWorkflowService:
    """
    ワークフロー全体のリクエスト生成サービス。
    
    利用例:
    ```python
    from src.env.env_workflow_service import EnvWorkflowService
    from src.context.execution_context import ExecutionContext

    env_context = ExecutionContext(
        command_type="run",
        language="python",
        contest_name="abc001",
        problem_name="a",
        env_type="local",
        env_json=...,  # env.jsonのdict
        contest_current_path="contests/abc001"
    )
    run_steps_dict_list = [
        {"type": "build", "cmd": ["make"]},
        {"type": "copy", "cmd": ["a.txt", "b.txt"]},
        {"type": "shell", "cmd": ["echo", "hello"]},
        {"type": "remove", "cmd": ["b.txt"]},
    ]
    service = EnvWorkflowService.from_context(env_context)
    composite_request = service.generate_run_requests(run_steps_dict_list)
    # composite_request.execute(driver=...)  # 必要に応じて実行
    ```
    """
    def __init__(self, env_context, controller, di_container):
        self.env_context = env_context
        self.controller = controller
        self.di_container = di_container

    @classmethod
    def from_context(cls, env_context):
        """
        本番用の依存性を組み立ててEnvWorkflowServiceを生成する
        """
        from src.env.env_resource_controller import EnvResourceController
        from src.env.resource.file.local_file_handler import LocalFileHandler
        from src.env.resource.run.local_run_handler import LocalRunHandler
        from src.env.resource.utils.const_handler import ConstHandler
        const_handler = ConstHandler(env_context)
        file_handler = LocalFileHandler(env_context, const_handler)
        run_handler = LocalRunHandler(env_context, const_handler)
        controller = EnvResourceController(env_context, file_handler, run_handler, const_handler)
        env_context, di_container = build_di_container_and_context(env_context)
        return cls(env_context, controller, di_container=di_container)

    def generate_run_requests(self, run_steps_dict_list):
        """
        run_steps_dict_list: List[dict]（env.json等から取得した生データ）
        CompositeRequestを返す
        エラー時はValueError等を投げる
        """
        from src.env.step.run_steps import RunSteps
        from src.env.run_workflow_builder import RunWorkflowBuilder
        # env_contextのバリデーション
        if hasattr(self.env_context, "validate"):
            valid, err = self.env_context.validate()
            if not valid:
                raise ValueError(f"env_context validation failed: {err}")
        # RunSteps生成とバリデーション
        run_steps = RunSteps.from_list(run_steps_dict_list)
        if hasattr(run_steps, "validate_all"):
            try:
                run_steps.validate_all()
            except Exception as e:
                raise ValueError(f"RunSteps validation failed: {e}")
        builder = RunWorkflowBuilder.from_controller(self.controller)
        composite_request = builder.build(run_steps)
        return composite_request

    def run_workflow(self):
        """
        self.env_contextからstepsを取得し、CompositeRequestを生成・実行して結果を返す
        """
        context = self.env_context
        try:
            steps = context.get_steps()
        except Exception as e:
            raise ValueError(f"env.jsonからコマンド({context.command_type})のsteps取得に失敗: {e}")
        composite_request = self.generate_run_requests(steps)
        # driverの種類はenv_type等で判定
        env_type = getattr(self.env_context, 'env_type', 'local').lower()
        driver_key = 'shell_driver' if env_type == 'local' else 'docker_driver'
        driver = self.di_container.resolve(driver_key) if self.di_container else None
        result = composite_request.execute(driver=driver)
        return result
