# from src.env.env_context_with_di import build_di_container_and_context

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
    def __init__(self, env_context, operations):
        from src.env_integration.controller import EnvResourceController
        from src.env_resource.file.local_file_handler import LocalFileHandler
        from src.env_resource.run.local_run_handler import LocalRunHandler

        file_handler = LocalFileHandler(env_context)
        run_handler = LocalRunHandler(env_context)
        self.controller = EnvResourceController(env_context, file_handler, run_handler)
        self.env_context = env_context
        self.operations = operations


    def run_workflow(self):
        """
        self.env_contextからstepsを取得し、CompositeRequestを生成・実行して結果を返す
        """
        context = self.env_context
        try:
            step_nodes = context.get_steps()  # ConfigNodeのリストを取得
        except Exception as e:
            raise ValueError(f"env.jsonからコマンド({context.command_type})のsteps取得に失敗: {e}")
        
        # RunWorkflowBuilderを使用してConfigNodeから直接リクエストを生成
        from src.env_integration.builder import RunWorkflowBuilder
        builder = RunWorkflowBuilder.from_controller(self.controller, self.operations)
        composite_request = builder.build_from_nodes(step_nodes)
        
        # driverの種類はenv_type等で判定
        env_type = self.env_context.env_type.lower()
        driver_key = 'shell_driver' if env_type == 'local' else 'docker_driver'
        driver = self.operations.resolve(driver_key) if self.operations else None
        if driver is None:
            raise ValueError(f"driver({driver_key})が設定されていません")
        result = composite_request.execute(driver=driver)
        return result
