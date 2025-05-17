from dataclasses import dataclass
from typing import List
from src.execution_env.env_resource_controller import EnvResourceController
from src.operations.composite_request import CompositeRequest

@dataclass
class RunPlan:
    language: str
    env: str
    count: int = 1
    # 今後必要なら追加パラメータもここに

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
        """
        all_requests = []
        for plan in run_plans:
            for i in range(plan.count):
                controller = EnvResourceController(language_name=plan.language, env_type=plan.env)
                # 例: ファイルコピー→コンテナ生成→コマンド実行のrequestをまとめる
                setup_requests = [
                    controller.copy_file("src", "dst"),  # 実際のパスや内容は要件に応じて拡張
                    # controller.create_process_options(["echo", "hello"])  # driverは呼び出し側で指定
                ]
                composite = CompositeRequest(setup_requests)
                all_requests.append(composite)
        return all_requests 