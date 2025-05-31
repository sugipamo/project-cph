"""
純粋なWorkflow生成のデモ

operationsに依存しない純粋なRequest生成を実証
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def demonstrate_pure_workflow():
    """純粋なワークフロー生成のデモ"""
    
    print("=== 純粋なWorkflow生成デモ ===")
    print()
    
    # PureRequestFactoryの直接テスト
    from env.step_generation.step import Step, StepType
    from env.workflow.pure_request_factory import PureRequestFactory
    
    print("1. PureRequestFactory の直接テスト:")
    
    # mkdir step
    mkdir_step = Step(
        type=StepType.MKDIR,
        cmd=["./test_dir"],
        allow_failure=False
    )
    
    mkdir_request = PureRequestFactory.create_request_from_step(mkdir_step)
    print(f"   mkdir step → {type(mkdir_request).__name__}")
    print(f"   Path: {mkdir_request.path}")
    print()
    
    # copy step  
    copy_step = Step(
        type=StepType.COPY,
        cmd=["./source.txt", "./dest.txt"],
        allow_failure=True
    )
    
    copy_request = PureRequestFactory.create_request_from_step(copy_step)
    print(f"   copy step → {type(copy_request).__name__}")
    print(f"   Source: {copy_request.path}, Dest: {copy_request.dst_path}")
    print()
    
    # shell step
    shell_step = Step(
        type=StepType.SHELL,
        cmd=["echo", "Hello World"],
        allow_failure=False,
        show_output=True
    )
    
    shell_request = PureRequestFactory.create_request_from_step(shell_step)
    print(f"   shell step → {type(shell_request).__name__}")
    print(f"   Command: {shell_request.cmd}")
    print()
    
    print("✅ PureRequestFactory: operationsなしでRequest生成成功")
    print()
    
    print("2. 純粋なGraphBasedWorkflowBuilder:")
    
    # 純粋なワークフロービルダーの使用
    from env.workflow.graph_based_workflow_builder import GraphBasedWorkflowBuilder
    from env.step_generation.step import StepContext
    
    # コンテキスト作成（environmentに依存しない）
    context = StepContext(
        contest_name="abc300",
        problem_name="a", 
        language="python",
        env_type="local",
        command_type="open",
        workspace_path="./workspace",
        contest_current_path="./contest_current"
    )
    
    # 純粋なビルダー作成
    builder = GraphBasedWorkflowBuilder.from_context(context)
    print(f"   Builder created: {type(builder).__name__}")
    print(f"   Context: {context.contest_name}/{context.problem_name}")
    print()
    
    # JSONステップからグラフ生成
    json_steps = [
        {"type": "mkdir", "cmd": ["./test_project"]},
        {"type": "touch", "cmd": ["./test_project/main.py"]},
        {"type": "copy", "cmd": ["./template.py", "./test_project/main.py"]}
    ]
    
    try:
        graph, errors, warnings = builder.build_graph_from_json_steps(json_steps)
        print(f"   Graph generated: {len(graph.nodes)} nodes")
        print(f"   Errors: {len(errors)}, Warnings: {len(warnings)}")
        
        # ノード詳細
        for node_id, node in graph.nodes.items():
            print(f"     - {node_id}: {type(node.request).__name__}")
        
        print()
        print("✅ GraphBasedWorkflowBuilder: operationsなしでGraph生成成功")
        
    except Exception as e:
        print(f"   エラー: {e}")
        print("   （一部の依存関係でエラーが発生する可能性があります）")
    
    print()
    print("=== 責務分離の成果 ===")
    print("✅ workflow: 純粋なRequest生成（operations不要）")
    print("✅ PureRequestFactory: 単純な変換ロジック")
    print("✅ テスタブル: 副作用なし")
    print("✅ 高速: DI解決の無駄な処理を排除")


if __name__ == "__main__":
    demonstrate_pure_workflow()