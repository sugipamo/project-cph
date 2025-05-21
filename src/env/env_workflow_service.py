class EnvWorkflowService:
    def __init__(self, env_context, controller=None):
        self.env_context = env_context
        self.controller = controller
        if self.controller is None:
            # 適切なファクトリを使ってcontrollerを生成（パスはプロジェクト構成に合わせて修正）
            from src.env.env_resource_controller import EnvResourceController
            from src.env.resource.file.local_file_handler import LocalFileHandler
            from src.env.resource.run.local_run_handler import LocalRunHandler
            from src.env.resource.utils.const_handler import ConstHandler
            const_handler = ConstHandler(env_context)
            file_handler = LocalFileHandler(env_context, const_handler)
            run_handler = LocalRunHandler(env_context, const_handler)
            self.controller = EnvResourceController(env_context, file_handler, run_handler, const_handler)

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
