class EnvWorkflowService:
    def __init__(self):
        pass

    def generate_run_requests(self, run_steps_dict_list):
        # run_steps_dict_list: List[dict]（env.json等から取得した生データ）
        # RunSteps型に変換してから利用する
        from src.env.step.run_steps import RunSteps
        run_steps = RunSteps.from_list(run_steps_dict_list)
        # ここでRunWorkflowBuilder等に渡して使う
        # 例:
        # builder = RunWorkflowBuilder(controller)
        # composite_request = builder.build(run_steps)
        pass
