from src.execution_env.run_plan_loader import load_run_plan_from_language_env
from src.execution_env.env_workflow_service import EnvWorkflowService, RunPlan

# 仮のmain的なエントリポイント

def main_workflow(language: str, env: str, count: int = 1):
    # language, env からRunPlanを生成
    run_plan = load_run_plan_from_language_env(language, env, count)
    run_plans = [run_plan]
    # ワークフローサービスでrequest群を生成
    service = EnvWorkflowService()
    requests = service.generate_requests(run_plans)
    # ここではrequest群をprintするだけ
    for i, req in enumerate(requests):
        print(f"Request {i}: {req}")

# 例: CLIから呼び出す場合
if __name__ == "__main__":
    # 仮の引数
    main_workflow("python", "docker", count=2) 