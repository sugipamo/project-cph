"""
fitting と workflow の統合例

責務分離:
- workflow: 純粋にrequestを生成
- fitting: operations経由で実環境確認と事前準備
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from env.fitting import PreparationExecutor
from operations.di_container import DIContainer
from env.build_operations import build_operations


def demonstrate_workflow_fitting_separation():
    """workflow と fitting の責務分離のデモ"""
    
    # 1. operationsの準備
    operations = build_operations()
    
    # 2. サンプルワークフロー定義（operationsに依存しない）
    json_steps = [
        {"type": "mkdir", "cmd": ["./test_project"]},
        {"type": "mkdir", "cmd": ["./test_project/src"]},
        {"type": "touch", "cmd": ["./test_project/src/main.py"]},
        {"type": "copy", "cmd": ["./contest_template/python/main.py", "./test_project/src/main.py"]}
    ]
    
    print("=== Workflow Generation (純粋・operations非依存) ===")
    
    # 3. workflow: 純粋にrequestを生成（operationsを使わない）
    # 注: 実際のworkflowビルダーはcontrollerを必要とするため、
    # ここではコンセプトを示すための疑似コード
    print("- ユーザー指定のjson_stepsから純粋にrequestを生成")
    print(f"- Steps: {len(json_steps)} items")
    for step in json_steps:
        print(f"  - {step['type']}: {step['cmd']}")
    
    print("\n=== Environment Fitting (operations使用) ===")
    
    # 4. fitting: operations経由で実環境確認
    fitting_executor = PreparationExecutor(operations)
    
    # 環境状態確認
    env_state = fitting_executor.check_environment_state("./test_project")
    print(f"- Environment check: {env_state}")
    
    # 疑似的なワークフロー要求を使用
    class MockWorkflowRequests:
        def __init__(self):
            self.requests = []
            # 疑似的なrequestオブジェクト
            self.mock_requests = [
                {"path": "./test_project", "type": "mkdir"},
                {"path": "./test_project/src", "type": "mkdir"},
                {"path": "./test_project/src/main.py", "type": "touch"}
            ]
    
    mock_workflow = MockWorkflowRequests()
    
    # 差異確認と事前準備
    print("- Checking requirements against environment...")
    missing_items = fitting_executor.verify_requirements_against_environment(
        mock_workflow, "./test_project"
    )
    print(f"- Missing items: {missing_items}")
    
    if missing_items['preparation_needed']:
        print("- Generating preparation requests...")
        prep_requests = fitting_executor.create_preparation_requests(missing_items)
        print(f"- Generated {len(prep_requests)} preparation requests")
        
        print("- Executing preparation...")
        prep_results = fitting_executor.execute_preparation(prep_requests)
        
        successful = sum(1 for r in prep_results if r.success)
        print(f"- Preparation completed: {successful}/{len(prep_results)} successful")
    else:
        print("- No preparation needed, environment is ready")
    
    print("\n=== Integration Result ===")
    print("✅ workflow: 純粋なrequest生成（operations非依存）")
    print("✅ fitting: operations経由で実環境適合")
    print("✅ 責務分離完了")


def demonstrate_fitting_integration():
    """fitting モジュールの統合機能デモ"""
    
    operations = build_operations()
    fitting_executor = PreparationExecutor(operations)
    
    # 疑似ワークフロー
    class MockWorkflow:
        def __init__(self):
            self.requests = []
    
    mock_workflow = MockWorkflow()
    
    print("\n=== Fitting Integration Demo ===")
    
    # メイン統合機能の使用
    result = fitting_executor.fit_workflow_to_environment(
        mock_workflow, "./demo_project"
    )
    
    print("Fitting result:")
    for key, value in result.items():
        if key != 'preparation_results':  # 長い結果は省略
            print(f"  {key}: {value}")
    
    return result


if __name__ == "__main__":
    demonstrate_workflow_fitting_separation()
    demonstrate_fitting_integration()