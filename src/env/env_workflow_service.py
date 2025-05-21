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
    def __init__(self, env_context, controller):
        self.env_context = env_context
        self.controller = controller

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
        return cls(env_context, controller)

    def generate_run_requests(self, run_steps_dict_list):
        """
        run_steps_dict_list: List[dict]（env.json等から取得した生データ）
        CompositeRequestを返す
        """
        from src.env.step.run_steps import RunSteps
        from src.env.run_workflow_builder import RunWorkflowBuilder
        run_steps = RunSteps.from_list(run_steps_dict_list)
        builder = RunWorkflowBuilder.from_controller(self.controller)
        composite_request = builder.build(run_steps)
        return composite_request
