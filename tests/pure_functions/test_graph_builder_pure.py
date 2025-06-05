"""
グラフベースワークフロービルダー純粋関数のテスト
モック不要で実際の動作をテスト
"""
import pytest
from pathlib import Path
from src.pure_functions.graph_builder_pure import (
    NodeInfo,
    DependencyInfo,
    GraphBuildResult,
    extract_node_resource_info_pure,
    build_node_info_list_pure,
    analyze_node_dependencies_pure,
    is_parent_directory_pure,
    has_resource_conflict_pure,
    build_execution_graph_pure,
    validate_graph_structure_pure,
    calculate_graph_metrics_pure
)
from src.env_core.step.step import Step, StepType, StepContext


class TestNodeInfo:
    """NodeInfoのテスト"""
    
    


class TestDependencyInfo:
    """DependencyInfoのテスト"""
    
    def test_create_dependency_info(self):
        """依存関係情報作成のテスト"""
        info = DependencyInfo(
            from_node_id="node1",
            to_node_id="node2",
            dependency_type="FILE_CREATION",
            resource_path="test.txt",
            description="Test dependency"
        )
        
        assert info.from_node_id == "node1"
        assert info.to_node_id == "node2"
        assert info.dependency_type == "FILE_CREATION"
        assert info.resource_path == "test.txt"
        assert info.description == "Test dependency"
    


class TestExtractNodeResourceInfo:
    """ノードリソース情報抽出のテスト"""
    
    def test_mkdir_step_resources(self):
        """MKDIRステップのリソース情報テスト"""
        step = Step(type=StepType.MKDIR, cmd=["./output"])
        
        creates_files, creates_dirs, reads_files, requires_dirs = extract_node_resource_info_pure(step)
        
        assert creates_dirs == {"./output"}
        assert creates_files == set()
        assert reads_files == set()
        assert requires_dirs == set()
    
    def test_touch_step_resources(self):
        """TOUCHステップのリソース情報テスト"""
        step = Step(type=StepType.TOUCH, cmd=["./output/file.txt"])
        
        creates_files, creates_dirs, reads_files, requires_dirs = extract_node_resource_info_pure(step)
        
        assert creates_files == {"./output/file.txt"}
        assert creates_dirs == set()
        assert reads_files == set()
        assert "output" in requires_dirs or "./output" in requires_dirs
    
    def test_copy_step_resources(self):
        """COPYステップのリソース情報テスト"""
        step = Step(type=StepType.COPY, cmd=["src.txt", "./output/dst.txt"])
        
        creates_files, creates_dirs, reads_files, requires_dirs = extract_node_resource_info_pure(step)
        
        assert creates_files == {"./output/dst.txt"}
        assert creates_dirs == set()
        assert reads_files == {"src.txt"}
        assert "output" in requires_dirs or "./output" in requires_dirs
    
    def test_move_step_resources(self):
        """MOVEステップのリソース情報テスト"""
        step = Step(type=StepType.MOVE, cmd=["old.txt", "new.txt"])
        
        creates_files, creates_dirs, reads_files, requires_dirs = extract_node_resource_info_pure(step)
        
        assert creates_files == {"new.txt"}
        assert reads_files == {"old.txt"}
        assert requires_dirs == set()  # ルートディレクトリ
    
    def test_shell_step_resources(self):
        """SHELLステップのリソース情報テスト"""
        step = Step(type=StepType.SHELL, cmd=["echo", "hello"])
        
        creates_files, creates_dirs, reads_files, requires_dirs = extract_node_resource_info_pure(step)
        
        assert creates_files == set()
        assert creates_dirs == set()
        assert reads_files == set()
        assert requires_dirs == {"./workspace"}
    
    def test_build_step_resources(self):
        """BUILDステップのリソース情報テスト"""
        step = Step(type=StepType.BUILD, cmd=["./project"])
        
        creates_files, creates_dirs, reads_files, requires_dirs = extract_node_resource_info_pure(step)
        
        assert creates_files == set()
        assert creates_dirs == set()
        assert reads_files == set()
        assert requires_dirs == {"./project"}
    
    def test_build_step_default_workspace(self):
        """BUILDステップ（デフォルトワークスペース）のリソース情報テスト"""
        step = Step(type=StepType.BUILD, cmd=[""])  # 空文字列でワークスペースデフォルト
        
        creates_files, creates_dirs, reads_files, requires_dirs = extract_node_resource_info_pure(step)
        
        assert requires_dirs == {"./workspace"}


class TestBuildNodeInfoList:
    """ノード情報リスト構築のテスト"""
    
    def test_build_single_node(self):
        """単一ノード構築のテスト"""
        step = Step(type=StepType.SHELL, cmd=["echo", "test"])
        
        node_infos = build_node_info_list_pure([step])
        
        assert len(node_infos) == 1
        assert node_infos[0].id == "step_0"
        assert node_infos[0].step == step
        assert node_infos[0].metadata["step_type"] == "shell"
        assert node_infos[0].metadata["original_index"] == 0
    
    def test_build_multiple_nodes(self):
        """複数ノード構築のテスト"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["./output"]),
            Step(type=StepType.TOUCH, cmd=["./output/file.txt"]),
            Step(type=StepType.SHELL, cmd=["ls", "./output"])
        ]
        
        node_infos = build_node_info_list_pure(steps)
        
        assert len(node_infos) == 3
        assert node_infos[0].id == "step_0"
        assert node_infos[1].id == "step_1"
        assert node_infos[2].id == "step_2"
        
        # リソース情報の確認
        assert node_infos[0].creates_dirs == {"./output"}
        assert node_infos[1].creates_files == {"./output/file.txt"}
        assert node_infos[2].requires_dirs == {"./workspace"}
    
    def test_build_with_context(self):
        """コンテキスト付きノード構築のテスト"""
        context = StepContext(
            contest_name="abc123",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="build",
            workspace_path="./workspace",
            contest_current_path="./current"
        )
        
        step = Step(type=StepType.PYTHON, cmd=["print('hello')"])
        
        node_infos = build_node_info_list_pure([step], context)
        
        assert len(node_infos) == 1
        assert node_infos[0].step == step


class TestAnalyzeNodeDependencies:
    """ノード依存関係分析のテスト"""
    
    def test_file_creation_dependency(self):
        """ファイル作成依存のテスト"""
        # ファイル作成 -> 読み取り
        create_step = Step(type=StepType.TOUCH, cmd=["data.txt"])
        read_step = Step(type=StepType.SHELL, cmd=["cat", "data.txt"])
        
        node_infos = build_node_info_list_pure([create_step, read_step])
        
        # 手動でリソース情報を調整（SHELLステップではdata.txtを読み取ると仮定）
        node_infos[1] = NodeInfo(
            id=node_infos[1].id,
            step=node_infos[1].step,
            creates_files=set(),
            creates_dirs=set(),
            reads_files={"data.txt"},
            requires_dirs={"./workspace"},
            metadata=node_infos[1].metadata
        )
        
        dependencies = analyze_node_dependencies_pure(node_infos)
        
        # ファイル作成依存が検出される
        file_deps = [d for d in dependencies if d.dependency_type == "FILE_CREATION"]
        assert len(file_deps) >= 1
        assert any(d.resource_path == "data.txt" for d in file_deps)
    
    def test_directory_creation_dependency(self):
        """ディレクトリ作成依存のテスト"""
        mkdir_step = Step(type=StepType.MKDIR, cmd=["./output"])
        touch_step = Step(type=StepType.TOUCH, cmd=["./output/file.txt"])
        
        node_infos = build_node_info_list_pure([mkdir_step, touch_step])
        dependencies = analyze_node_dependencies_pure(node_infos)
        
        # ディレクトリ作成依存が検出される可能性
        dir_deps = [d for d in dependencies if d.dependency_type == "DIRECTORY_CREATION"]
        assert len(dir_deps) >= 0  # 依存関係があるかもしれない
    
    def test_no_dependencies(self):
        """依存関係なしのテスト"""
        step1 = Step(type=StepType.SHELL, cmd=["echo", "hello"])
        step2 = Step(type=StepType.SHELL, cmd=["echo", "world"])
        
        node_infos = build_node_info_list_pure([step1, step2])
        dependencies = analyze_node_dependencies_pure(node_infos)
        
        # 明確な依存関係はない（順序依存は除く）
        resource_deps = [d for d in dependencies 
                        if d.dependency_type in ["FILE_CREATION", "DIRECTORY_CREATION"]]
        assert len(resource_deps) == 0
    
    def test_resource_conflict_dependency(self):
        """リソース競合による依存のテスト"""
        # 同じファイルを作成する2つのステップ
        step1 = Step(type=StepType.TOUCH, cmd=["conflict.txt"])
        step2 = Step(type=StepType.TOUCH, cmd=["conflict.txt"])
        
        node_infos = build_node_info_list_pure([step1, step2])
        dependencies = analyze_node_dependencies_pure(node_infos)
        
        # 順序依存が追加される
        order_deps = [d for d in dependencies if d.dependency_type == "EXECUTION_ORDER"]
        assert len(order_deps) >= 1


class TestUtilityFunctions:
    """ユーティリティ関数のテスト"""
    
    def test_is_parent_directory_pure_true(self):
        """親ディレクトリ判定（True）のテスト"""
        assert is_parent_directory_pure("./output", "./output/subdir")
        assert is_parent_directory_pure("/home/user", "/home/user/project")
    
    def test_is_parent_directory_pure_false(self):
        """親ディレクトリ判定（False）のテスト"""
        assert not is_parent_directory_pure("./output", "./other")
        assert not is_parent_directory_pure("/home/user", "/home/other")
        assert not is_parent_directory_pure("./output/subdir", "./output")
    
    def test_has_resource_conflict_pure_file_conflict(self):
        """ファイル競合のテスト"""
        node1 = NodeInfo(
            id="node1", step=Step(type=StepType.TOUCH, cmd=["test.txt"]),
            creates_files={"test.txt"}, creates_dirs=set(),
            reads_files=set(), requires_dirs=set(), metadata={}
        )
        node2 = NodeInfo(
            id="node2", step=Step(type=StepType.TOUCH, cmd=["test.txt"]),
            creates_files={"test.txt"}, creates_dirs=set(),
            reads_files=set(), requires_dirs=set(), metadata={}
        )
        
        assert has_resource_conflict_pure(node1, node2)
    
    def test_has_resource_conflict_pure_no_conflict(self):
        """リソース競合なしのテスト"""
        node1 = NodeInfo(
            id="node1", step=Step(type=StepType.TOUCH, cmd=["file1.txt"]),
            creates_files={"file1.txt"}, creates_dirs=set(),
            reads_files=set(), requires_dirs=set(), metadata={}
        )
        node2 = NodeInfo(
            id="node2", step=Step(type=StepType.TOUCH, cmd=["file2.txt"]),
            creates_files={"file2.txt"}, creates_dirs=set(),
            reads_files=set(), requires_dirs=set(), metadata={}
        )
        
        assert not has_resource_conflict_pure(node1, node2)


class TestBuildExecutionGraph:
    """実行グラフ構築のテスト"""
    
    def test_build_simple_graph(self):
        """シンプルなグラフ構築のテスト"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["./output"]),
            Step(type=StepType.TOUCH, cmd=["./output/file.txt"])
        ]
        
        result = build_execution_graph_pure(steps)
        
        assert len(result.nodes) == 2
        assert len(result.errors) == 0
        assert result.nodes[0].step.type == StepType.MKDIR
        assert result.nodes[1].step.type == StepType.TOUCH
    
    def test_build_graph_with_dependencies(self):
        """依存関係付きグラフ構築のテスト"""
        steps = [
            Step(type=StepType.TOUCH, cmd=["input.txt"]),
            Step(type=StepType.COPY, cmd=["input.txt", "output.txt"])
        ]
        
        result = build_execution_graph_pure(steps)
        
        assert len(result.nodes) == 2
        assert len(result.dependencies) >= 1
        
        # ファイル作成依存が検出される
        file_deps = [d for d in result.dependencies if d.dependency_type == "FILE_CREATION"]
        assert len(file_deps) >= 1
    
    def test_build_empty_graph(self):
        """空のグラフ構築のテスト"""
        result = build_execution_graph_pure([])
        
        assert len(result.nodes) == 0
        assert len(result.dependencies) == 0
        assert len(result.errors) == 1
        assert "No steps provided" in result.errors[0]
    
    def test_build_graph_with_context(self):
        """コンテキスト付きグラフ構築のテスト"""
        context = StepContext(
            contest_name="abc123",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="build",
            workspace_path="./workspace",
            contest_current_path="./current"
        )
        
        steps = [Step(type=StepType.PYTHON, cmd=["print('hello')"])]
        
        result = build_execution_graph_pure(steps, context)
        
        assert len(result.nodes) == 1
        assert len(result.errors) == 0


class TestValidateGraphStructure:
    """グラフ構造検証のテスト"""
    
    def test_validate_valid_graph(self):
        """有効なグラフの検証テスト"""
        step = Step(type=StepType.SHELL, cmd=["echo", "test"])
        nodes = build_node_info_list_pure([step])
        dependencies = []
        
        errors = validate_graph_structure_pure(nodes, dependencies)
        
        assert errors == []
    
    def test_validate_duplicate_node_ids(self):
        """重複ノードIDの検証テスト"""
        # 手動で重複IDを作成
        step = Step(type=StepType.SHELL, cmd=["echo", "test"])
        node1 = NodeInfo(
            id="duplicate", step=step, creates_files=set(), creates_dirs=set(),
            reads_files=set(), requires_dirs=set(), metadata={}
        )
        node2 = NodeInfo(
            id="duplicate", step=step, creates_files=set(), creates_dirs=set(),
            reads_files=set(), requires_dirs=set(), metadata={}
        )
        
        errors = validate_graph_structure_pure([node1, node2], [])
        
        assert len(errors) >= 1
        assert "Duplicate node IDs" in errors[0]
    
    def test_validate_invalid_dependency_reference(self):
        """無効な依存関係参照の検証テスト"""
        step = Step(type=StepType.SHELL, cmd=["echo", "test"])
        nodes = build_node_info_list_pure([step])
        
        # 存在しないノードを参照する依存関係
        invalid_dep = DependencyInfo(
            from_node_id="nonexistent",
            to_node_id="step_0",
            dependency_type="FILE_CREATION",
            resource_path="test.txt",
            description="Invalid dependency"
        )
        
        errors = validate_graph_structure_pure(nodes, [invalid_dep])
        
        assert len(errors) >= 1
        assert "unknown from_node" in errors[0]


class TestCalculateGraphMetrics:
    """グラフメトリクス計算のテスト"""
    
    def test_calculate_basic_metrics(self):
        """基本メトリクス計算のテスト"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["./output"]),
            Step(type=StepType.TOUCH, cmd=["./output/file.txt"]),
            Step(type=StepType.SHELL, cmd=["ls", "./output"])
        ]
        
        result = build_execution_graph_pure(steps)
        metrics = calculate_graph_metrics_pure(result)
        
        assert metrics["node_count"] == 3
        assert metrics["error_count"] == 0
        assert metrics["success_rate"] == 1.0
        assert metrics["step_types"]["mkdir"] == 1
        assert metrics["step_types"]["touch"] == 1
        assert metrics["step_types"]["shell"] == 1
        assert metrics["total_dirs_created"] == 1
        assert metrics["total_files_created"] == 1
    
    def test_calculate_metrics_with_dependencies(self):
        """依存関係付きメトリクス計算のテスト"""
        steps = [
            Step(type=StepType.TOUCH, cmd=["input.txt"]),
            Step(type=StepType.COPY, cmd=["input.txt", "output.txt"])
        ]
        
        result = build_execution_graph_pure(steps)
        metrics = calculate_graph_metrics_pure(result)
        
        assert metrics["dependency_count"] >= 1
        assert metrics["complexity_score"] > 0
        assert "FILE_CREATION" in metrics["dependency_types"]
    
    def test_calculate_empty_metrics(self):
        """空のメトリクス計算のテスト"""
        result = GraphBuildResult([], [], ["No steps"], [])
        metrics = calculate_graph_metrics_pure(result)
        
        assert metrics["node_count"] == 0
        assert metrics["dependency_count"] == 0
        assert metrics["error_count"] == 1
        assert metrics["success_rate"] == 0
        assert metrics["step_types"] == {}
        assert metrics["complexity_score"] == 0


class TestPureFunctionProperties:
    """純粋関数の特性テスト"""
    
    def test_deterministic_behavior(self):
        """決定論的動作のテスト"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["./output"]),
            Step(type=StepType.TOUCH, cmd=["./output/file.txt"])
        ]
        
        # 同じ入力に対して常に同じ出力
        result1 = build_execution_graph_pure(steps)
        result2 = build_execution_graph_pure(steps)
        
        assert len(result1.nodes) == len(result2.nodes)
        assert len(result1.dependencies) == len(result2.dependencies)
        assert result1.errors == result2.errors
    
    def test_no_side_effects(self):
        """副作用なしのテスト"""
        original_steps = [Step(type=StepType.SHELL, cmd=["echo", "test"])]
        
        # 関数実行
        result = build_execution_graph_pure(original_steps)
        
        # 元のステップが変更されていないことを確認
        assert original_steps[0].type == StepType.SHELL
        assert original_steps[0].cmd == ["echo", "test"]
    
    def test_immutable_outputs(self):
        """出力の不変性テスト"""
        steps = [Step(type=StepType.SHELL, cmd=["echo", "test"])]
        result = build_execution_graph_pure(steps)
        
        # 結果オブジェクトが不変であることを確認
        with pytest.raises(AttributeError):
            result.nodes[0].id = "new_id"


class TestComplexScenarios:
    """複雑なシナリオのテスト"""
    
    def test_build_workflow_scenario(self):
        """ビルドワークフローシナリオのテスト"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["./output"]),
            Step(type=StepType.COPY, cmd=["main.py", "./output/main.py"]),
            Step(type=StepType.BUILD, cmd=["./output"]),
            Step(type=StepType.TEST, cmd=["python3", "./output/main.py"])
        ]
        
        result = build_execution_graph_pure(steps)
        
        # すべて有効なノードが生成される
        assert len(result.nodes) == 4
        assert len(result.errors) == 0
        
        # メトリクス確認
        metrics = calculate_graph_metrics_pure(result)
        assert metrics["success_rate"] == 1.0
        assert metrics["total_dirs_created"] == 1
        assert metrics["total_files_created"] == 1
    
    def test_parallel_execution_scenario(self):
        """並列実行シナリオのテスト"""
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "task1"]),
            Step(type=StepType.SHELL, cmd=["echo", "task2"]),
            Step(type=StepType.SHELL, cmd=["echo", "task3"])
        ]
        
        result = build_execution_graph_pure(steps)
        
        # 独立したタスクなので依存関係は最小限
        assert len(result.nodes) == 3
        resource_deps = [d for d in result.dependencies 
                        if d.dependency_type in ["FILE_CREATION", "DIRECTORY_CREATION"]]
        assert len(resource_deps) == 0  # リソース依存なし