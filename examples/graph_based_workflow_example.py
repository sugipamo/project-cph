"""
グラフベースワークフローの使用例

このサンプルでは、リストベースとグラフベースの両方のアプローチを比較し、
グラフベースの利点（依存関係の明示化、並列実行の可能性）を示します。
"""
from src.env.workflow import (
    GraphBasedWorkflowBuilder,
    RequestExecutionGraph,
    GraphToCompositeAdapter
)
from src.env.run_workflow_builder import RunWorkflowBuilder
from src.operations.di_container import DIContainer
from src.env.types import EnvResourceController
from unittest.mock import Mock


def create_sample_workflow_steps():
    """サンプルワークフローステップを作成"""
    return [
        # ディレクトリ作成
        {
            "type": "mkdir",
            "cmd": ["project"]
        },
        {
            "type": "mkdir", 
            "cmd": ["project/src"]
        },
        {
            "type": "mkdir",
            "cmd": ["project/tests"]
        },
        {
            "type": "mkdir",
            "cmd": ["project/docs"]
        },
        
        # ファイル作成（これらは並列実行可能）
        {
            "type": "touch",
            "cmd": ["project/README.md"]
        },
        {
            "type": "touch",
            "cmd": ["project/src/main.py"]
        },
        {
            "type": "touch",
            "cmd": ["project/tests/test_main.py"]
        },
        
        # ファイルコピー（依存関係あり）
        {
            "type": "copy",
            "cmd": ["project/README.md", "project/docs/README.md"]
        },
        
        # ビルド実行（すべてのファイルが必要）
        {
            "type": "shell",
            "cmd": ["cd project && echo 'Building project...'"]
        }
    ]


def example_list_based_execution():
    """従来のリストベース実行の例"""
    print("=== リストベース実行 ===")
    
    # モックの設定
    controller = Mock(spec=EnvResourceController)
    controller.env_context = Mock()
    controller.env_context.contest_name = "example"
    controller.env_context.problem_name = "test"
    controller.env_context.language = "python"
    controller.env_context.env_type = "local"
    controller.env_context.command_type = "run"
    
    operations = Mock(spec=DIContainer)
    
    # ビルダーを作成
    builder = RunWorkflowBuilder(controller, operations)
    
    # ワークフローステップを取得
    steps = create_sample_workflow_steps()
    
    # CompositeRequestを生成（従来の方法）
    composite_request, errors, warnings = builder.build_from_json_steps(steps)
    
    print(f"生成されたリクエスト数: {len(composite_request.requests)}")
    print(f"エラー: {errors}")
    print(f"警告: {warnings}")
    print("すべてのリクエストは順次実行されます。")
    print()


def example_graph_based_execution():
    """グラフベース実行の例"""
    print("=== グラフベース実行 ===")
    
    # モックの設定
    controller = Mock(spec=EnvResourceController)
    controller.env_context = Mock()
    controller.env_context.contest_name = "example"
    controller.env_context.problem_name = "test"
    controller.env_context.language = "python"
    controller.env_context.env_type = "local"
    controller.env_context.command_type = "run"
    
    operations = Mock(spec=DIContainer)
    
    # ビルダーを作成
    builder = RunWorkflowBuilder(controller, operations)
    
    # ワークフローステップを取得
    steps = create_sample_workflow_steps()
    
    # RequestExecutionGraphを生成
    graph, errors, warnings = builder.build_graph_from_json_steps(steps)
    
    print(f"生成されたノード数: {len(graph.nodes)}")
    print(f"生成されたエッジ数: {len(graph.edges)}")
    print(f"エラー: {errors}")
    print(f"警告: {warnings}")
    
    # 並列実行グループを表示
    try:
        groups = graph.get_parallel_groups()
        print(f"\n並列実行グループ数: {len(groups)}")
        for i, group in enumerate(groups):
            print(f"  グループ {i+1}: {group} ({len(group)}個のタスク)")
    except ValueError as e:
        print(f"並列グループの取得エラー: {e}")
    
    # グラフの可視化
    print("\n" + graph.visualize())
    print()


def example_adaptive_execution():
    """条件に応じた実行方法の選択"""
    print("=== アダプティブ実行 ===")
    
    # モックの設定
    controller = Mock(spec=EnvResourceController)
    controller.env_context = Mock()
    controller.env_context.contest_name = "example"
    controller.env_context.problem_name = "test"
    controller.env_context.language = "python"
    controller.env_context.env_type = "local"
    controller.env_context.command_type = "run"
    
    operations = Mock(spec=DIContainer)
    
    # ビルダーを作成
    builder = RunWorkflowBuilder(controller, operations)
    
    # ワークフローステップを取得
    steps = create_sample_workflow_steps()
    
    # 実行環境に応じて最適な方法を選択
    use_graph = len(steps) > 5  # ステップ数が多い場合はグラフベース
    
    result = builder.build_composite_or_graph(steps, use_graph=use_graph)
    
    if isinstance(result, RequestExecutionGraph):
        print("グラフベース実行が選択されました。")
        print(f"並列実行可能なグループ: {len(result.get_parallel_groups())}")
        
        # 並列実行
        # results = builder.execute_graph(result, driver=None, parallel=True)
    else:
        print("リストベース実行が選択されました。")
        print(f"順次実行されるリクエスト数: {len(result.requests)}")
        
        # 順次実行
        # results = result.execute(driver=None)
    print()


def example_graph_to_composite_conversion():
    """グラフからCompositeRequestへの変換例"""
    print("=== グラフからCompositeRequestへの変換 ===")
    
    # モックの設定
    controller = Mock(spec=EnvResourceController)
    controller.env_context = Mock()
    controller.env_context.contest_name = "example"
    controller.env_context.problem_name = "test"
    controller.env_context.language = "python"
    controller.env_context.env_type = "local"
    controller.env_context.command_type = "run"
    
    operations = Mock(spec=DIContainer)
    
    # グラフベースビルダーを作成
    graph_builder = GraphBasedWorkflowBuilder(controller, operations)
    
    # ワークフローステップを取得
    steps = create_sample_workflow_steps()
    
    # グラフを生成
    graph, _, _ = graph_builder.build_graph_from_json_steps(steps)
    
    # 後方互換性のためCompositeRequestに変換
    composite = GraphToCompositeAdapter.to_composite_request(graph)
    
    print(f"グラフのノード数: {len(graph.nodes)}")
    print(f"変換後のリクエスト数: {len(composite.requests)}")
    print("グラフの依存関係がトポロジカルソートされた順序で配置されます。")
    print()


if __name__ == "__main__":
    print("グラフベースワークフローシステムのデモ")
    print("=" * 50)
    print()
    
    # 各例を実行
    example_list_based_execution()
    example_graph_based_execution()
    example_adaptive_execution()
    example_graph_to_composite_conversion()
    
    print("まとめ:")
    print("- リストベース: シンプルで理解しやすい、順次実行のみ")
    print("- グラフベース: 依存関係を明示的に管理、並列実行可能")
    print("- 両方のアプローチは相互変換可能で、段階的な移行が可能")
    print("- 用途に応じて最適な方法を選択できる")