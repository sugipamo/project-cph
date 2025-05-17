from typing import List
from src.execution_env.env_resource_controller import EnvResourceController
from src.operations.composite_request import CompositeRequest
from src.execution_env.run_plan_loader import load_run_plan_from_language_env, load_env_json
from src.execution_env.run_plan_loader import RunPlan


class EnvWorkflowService:
    def __init__(self):
        pass

    def generate_requests(self, run_plans: List[RunPlan]):
        """
        run_plans例:
        [
            RunPlan(language="python", env="docker", count=2),
            RunPlan(language="cpp", env="local", count=1),
        ]
        各planごとに必要なrequest群（CompositeRequest等）を生成して返す
        ビルド用ファイル準備→ビルド実行→成果物準備→起動
        """
        import copy
        all_requests = []
        for plan in run_plans:
            for i in range(plan.count):
                # controller生成
                controller = EnvResourceController.from_plan(plan)
                requests = []
                # 1. ビルド用ファイル準備（prepare_sourcecodeを利用）
                requests.append(controller.prepare_sourcecode())
                # 2. ビルド実行
                for build_cmd in controller.get_build_commands():
                    req = controller.create_process_options(build_cmd)
                    requests.append(req)
                # 3. 成果物準備（現状は省略。必要ならここで成果物ファイルをコピー等）
                # 4. 起動
                run_cmd = controller.get_run_command()
                if run_cmd:
                    req = controller.create_process_options(run_cmd)
                    requests.append(req)
                composite = CompositeRequest(requests)
                all_requests.append(composite)
        return all_requests 
    
def make_service(language: str, env: str, count: int = 1):
    # language, env からRunPlanを生成
    run_plan = load_run_plan_from_language_env(language, env, count)
    run_plans = [run_plan]
    # ワークフローサービスでrequest群を生成
    service = EnvWorkflowService()
    requests = service.generate_requests(run_plans)
    # ここではrequest群をprintするだけ
    for i, req in enumerate(requests):
        print(f"Request {i}: {req}")

if __name__ == "__main__":
    #ここでコマンドうけつけ
    # language = input("language: ")
    # env = input("env: ")
    # count = int(input("count: "))
    # コマンドの引数で受付するようにしたい
    import sys
    language = sys.argv[1]
    env = sys.argv[2]
    count = int(sys.argv[3])
    make_service(language, env, count)