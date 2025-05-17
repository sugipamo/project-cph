from typing import List
from src.execution_env.env_resource_controller import EnvResourceController
from src.operations.composite_request import CompositeRequest
from src.execution_env.run_plan_loader import load_env_context_from_language_env, load_env_json
from src.execution_env.run_plan_loader import EnvContext, OjContext
import copy


class EnvWorkflowService:
    def __init__(self):
        pass

    def generate_requests(self, env_contexts: List[EnvContext]):
        """
        env_contexts例:
        [
            EnvContext(language="python", env="docker", count=2),
            EnvContext(language="cpp", env="local", count=1),
        ]
        各env_contextごとに必要なrequest群（CompositeRequest等）を生成して返す
        ビルド用ファイル準備→ビルド実行→成果物準備→起動
        """
        all_requests = []
        for context in env_contexts:
            for i in range(context.count):
                # controller生成
                controller = EnvResourceController.from_context(context)
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
    # language, env からEnvContextを生成
    env_context = load_env_context_from_language_env(language, env, count)
    # oj用のOjContextをEnvContextから生成
    oj_context = OjContext.from_context(env_context)
    env_contexts = [env_context, oj_context]
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
    count = int(sys.argv[3])
    make_service(language, env, count)