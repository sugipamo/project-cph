from typing import List
from src.execution_env.env_resource_controller import EnvResourceController
from src.execution_env.run_plan_loader import load_env_context_from_language_env, load_env_json
from src.execution_env.run_plan_loader import EnvContext, OjContext
import copy
from src.operations.composite_request import CompositeRequest

class EnvWorkflowService:
    def __init__(self):
        pass

    def generate_requests(self, env_contexts: List[EnvContext]):
        """
        env_contexts例:
        [
            EnvContext(language="python", env="docker"),
            EnvContext(language="cpp", env="local"),
        ]
        各env_contextごとに必要なrequest群（CompositeRequest等）を生成して返す
        ビルド用ファイル準備→ビルド実行→成果物準備→起動
        """
        all_requests = []
        for context in env_contexts:
            requests = []
            controller = EnvResourceController.from_context(context)
            if controller.env_context.build_cmd:
                req = controller.get_build_commands()
                requests.append(req)

            req = controller.get_run_command()
            requests.append(req)
            all_requests.append(CompositeRequest(requests))

            oj_context = OjContext.from_context(context)
            oj_requests = []
            if oj_context.test_cmd:
                req = controller.create_process_options(oj_context.test_cmd)
                oj_requests.append(req)
            if oj_context.submit_cmd:
                req = controller.create_process_options(oj_context.submit_cmd)
                oj_requests.append(req)
            all_requests.append(CompositeRequest(oj_requests))

        return all_requests
    
def make_service(language: str, env: str):
    # language, env からEnvContextを生成
    env_context = load_env_context_from_language_env(language, env)
    
    env_contexts = [env_context]
    # ワークフローサービスでrequest群を生成
    service = EnvWorkflowService()
    requests = service.generate_requests(env_contexts)
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
    make_service(language, env)