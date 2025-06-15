"""Tests for execution orchestration module."""
from concurrent.futures import Future
from unittest.mock import Mock, patch

import pytest

from src.workflow.builder.execution_orchestration import (
    BatchResult,
    ExecutionContext,
    calculate_execution_progress,
    calculate_resource_usage,
    collect_execution_results,
    create_execution_context,
    create_execution_plan_summary,
    estimate_remaining_time,
    handle_execution_failure,
    optimize_worker_allocation,
    prepare_batch_execution,
    safe_execute_node,
    validate_execution_readiness,
)


class TestExecutionContext:
    """Test ExecutionContext dataclass."""

    def test_init_basic(self):
        nodes = {"n1": Mock(), "n2": Mock()}
        dependencies = {"n1": set(), "n2": {"n1"}}

        context = ExecutionContext(
            nodes=nodes,
            dependencies=dependencies,
            max_workers=4,
            timeout=300
        )

        assert context.nodes == nodes
        assert context.dependencies == dependencies
        assert context.max_workers == 4
        assert context.timeout == 300

    def test_node_count_property(self):
        context = ExecutionContext(
            nodes={"n1": Mock(), "n2": Mock(), "n3": Mock()},
            dependencies={},
            max_workers=2
        )
        assert context.node_count == 3

    def test_dependency_count_property(self):
        context = ExecutionContext(
            nodes={"n1": Mock(), "n2": Mock(), "n3": Mock()},
            dependencies={"n1": set(), "n2": {"n1"}, "n3": {"n1", "n2"}},
            max_workers=2
        )
        assert context.dependency_count == 3  # 0 + 1 + 2

    def test_immutability(self):
        context = ExecutionContext(
            nodes={},
            dependencies={},
            max_workers=4
        )

        with pytest.raises(AttributeError):
            context.max_workers = 8


class TestBatchResult:
    """Test BatchResult dataclass."""

    def test_success_result_factory(self):
        result = BatchResult.success_result(
            node_id="n1",
            result={"data": "value"},
            execution_time=1.5
        )

        assert result.node_id == "n1"
        assert result.success is True
        assert result.result == {"data": "value"}
        assert result.execution_time == 1.5
        assert result.error_message is None

    def test_error_result_factory(self):
        result = BatchResult.error_result(
            node_id="n2",
            error_message="Connection timeout",
            execution_time=30.0
        )

        assert result.node_id == "n2"
        assert result.success is False
        assert result.result is None
        assert result.execution_time == 30.0
        assert result.error_message == "Connection timeout"


class TestExecutionFunctions:
    """Test execution orchestration functions."""

    def test_create_execution_context(self):
        nodes = {"n1": Mock(), "n2": Mock()}
        dependencies = {"n1": set(), "n2": {"n1"}}

        context = create_execution_context(
            nodes=nodes,
            dependencies=dependencies,
            max_workers=8,
            timeout=600
        )

        assert context.nodes == nodes
        assert context.dependencies == dependencies
        assert context.max_workers == 8
        assert context.timeout == 600

        # 元の辞書を変更してもコンテキストに影響しない
        nodes["n3"] = Mock()
        dependencies["n2"].add("n3")

        assert len(context.nodes) == 2
        assert "n3" not in context.dependencies["n2"]

    def test_prepare_batch_execution(self):
        context = ExecutionContext(
            nodes={"n1": Mock(), "n2": Mock()},
            dependencies={},
            max_workers=4,
            timeout=300
        )

        executable_nodes = ["n1", "n2"]
        metadata = prepare_batch_execution(executable_nodes, context)

        assert "batch_id" in metadata
        assert metadata["node_count"] == 2
        assert metadata["max_workers"] == 4
        assert metadata["timeout"] == 300
        assert metadata["nodes"] == ["n1", "n2"]

    @patch('src.domain.results.result.OperationResult')
    def test_collect_execution_results_success(self, mock_operation_result):
        # Mock futures
        future1 = Mock(spec=Future)
        future1.result.return_value = {"success": True}

        future2 = Mock(spec=Future)
        future2.result.return_value = {"success": True}

        futures = [(future1, "n1"), (future2, "n2")]
        execution_order = ["n1", "n2"]

        results = collect_execution_results(futures, execution_order, timeout=10)

        assert len(results) == 2
        assert results["n1"] == {"success": True}
        assert results["n2"] == {"success": True}

        future1.result.assert_called_once_with(timeout=10)
        future2.result.assert_called_once_with(timeout=10)

    @patch('src.domain.results.result.OperationResult')
    def test_collect_execution_results_with_failure(self, mock_operation_result_class):
        mock_error_result = Mock()
        mock_operation_result_class.return_value = mock_error_result

        # Mock futures
        future1 = Mock(spec=Future)
        future1.result.return_value = {"success": True}

        future2 = Mock(spec=Future)
        future2.result.side_effect = Exception("Execution failed")

        futures = [(future1, "n1"), (future2, "n2")]
        execution_order = ["n1", "n2"]

        results = collect_execution_results(futures, execution_order)

        assert len(results) == 2
        assert results["n1"] == {"success": True}
        assert results["n2"] == mock_error_result

        mock_operation_result_class.assert_called_once_with(
            success=False,
            error_message="Execution failed"
        )

    def test_handle_execution_failure(self):
        adjacency_list = {
            "n1": {"n2", "n3"},
            "n2": {"n4"},
            "n3": {"n4"},
            "n4": {"n5"}
        }

        node_states = {
            "n1": "failed",
            "n2": "pending",
            "n3": "pending",
            "n4": "pending",
            "n5": "pending"
        }

        updated_states = handle_execution_failure("n1", adjacency_list, node_states)

        # n1の依存先が全てスキップされる
        assert updated_states["n1"] == "failed"
        assert updated_states["n2"] == "skipped"
        assert updated_states["n3"] == "skipped"
        assert updated_states["n4"] == "skipped"  # 再帰的にスキップ
        assert updated_states["n5"] == "skipped"  # 再帰的にスキップ

    def test_calculate_execution_progress(self):
        completed = {"n1", "n2"}
        failed = {"n3"}
        skipped = {"n4", "n5"}
        total_nodes = 8

        progress = calculate_execution_progress(completed, failed, skipped, total_nodes)

        assert progress["total_nodes"] == 8
        assert progress["completed"] == 2
        assert progress["failed"] == 1
        assert progress["skipped"] == 2
        assert progress["remaining"] == 3  # 8 - 5
        assert progress["progress_percentage"] == 62.5  # 5/8 * 100
        assert progress["success_rate"] == 40.0  # 2/5 * 100

    def test_calculate_execution_progress_edge_cases(self):
        # 全ノード未処理
        progress = calculate_execution_progress(set(), set(), set(), 5)
        assert progress["progress_percentage"] == 0
        assert progress["success_rate"] == 0

        # ノードなし
        progress = calculate_execution_progress(set(), set(), set(), 0)
        assert progress["progress_percentage"] == 0
        assert progress["success_rate"] == 0

    def test_validate_execution_readiness_valid(self):
        context = ExecutionContext(
            nodes={"n1": Mock(), "n2": Mock()},
            dependencies={"n1": set(), "n2": {"n1"}},
            max_workers=4,
            timeout=300
        )

        errors = validate_execution_readiness(context)
        assert errors == []

    def test_validate_execution_readiness_invalid(self):
        context = ExecutionContext(
            nodes={},
            dependencies={"n1": {"n2"}},  # n1もn2も存在しない
            max_workers=0,
            timeout=-1
        )

        errors = validate_execution_readiness(context)

        assert "No nodes to execute" in errors
        assert "Invalid max_workers: 0" in errors
        assert "Invalid timeout: -1" in errors
        assert any("doesn't exist in nodes" in e for e in errors)

    def test_create_execution_plan_summary(self):
        context = ExecutionContext(
            nodes={"n1": Mock(), "n2": Mock(), "n3": Mock()},
            dependencies={"n2": {"n1"}, "n3": {"n2"}},
            max_workers=2,
            timeout=300
        )

        parallel_groups = [["n1"], ["n2"], ["n3"]]

        summary = create_execution_plan_summary(context, parallel_groups)

        assert summary["total_nodes"] == 3
        assert summary["total_dependencies"] == 2
        assert summary["max_workers"] == 2
        assert summary["timeout"] == 300
        assert summary["execution_groups"] == 3
        assert summary["max_parallelism"] == 1
        assert summary["estimated_execution_time"] == 90  # 3 * 30
        assert len(summary["groups"]) == 3
        assert summary["groups"][0]["nodes"] == ["n1"]

    @patch('src.domain.results.result.OperationResult')
    def test_safe_execute_node_success(self, mock_operation_result_class):
        node = Mock()
        driver = Mock()
        expected_result = Mock()
        node.request.execute.return_value = expected_result

        result = safe_execute_node(node, driver)

        assert result == expected_result
        node.request.execute.assert_called_once_with(driver=driver)
        mock_operation_result_class.assert_not_called()

    @patch('src.domain.results.result.OperationResult')
    @patch('traceback.format_exc')
    def test_safe_execute_node_failure(self, mock_format_exc, mock_operation_result_class):
        mock_format_exc.return_value = "Traceback..."
        mock_error_result = Mock()
        mock_operation_result_class.return_value = mock_error_result

        node = Mock()
        driver = Mock()
        node.request.execute.side_effect = Exception("Test error")

        result = safe_execute_node(node, driver)

        assert result == mock_error_result
        mock_operation_result_class.assert_called_once()
        call_args = mock_operation_result_class.call_args
        assert call_args[1]["success"] is False
        assert "Test error" in call_args[1]["error_message"]
        assert "Traceback..." in call_args[1]["error_message"]

    def test_optimize_worker_allocation(self):
        # 各グループのサイズに応じてワーカーを割り当て
        parallel_groups = [["n1", "n2", "n3"], ["n4"], ["n5", "n6"]]
        max_workers = 2

        allocations = optimize_worker_allocation(parallel_groups, max_workers)

        assert allocations == [2, 1, 2]  # min(group_size, max_workers)

    def test_optimize_worker_allocation_edge_cases(self):
        # 空のグループ
        assert optimize_worker_allocation([], 4) == []

        # 大きなグループ
        parallel_groups = [["n" + str(i) for i in range(10)]]
        allocations = optimize_worker_allocation(parallel_groups, 5)
        assert allocations == [5]  # 最大ワーカー数で制限

    def test_calculate_resource_usage(self):
        context = ExecutionContext(
            nodes={"n1": Mock(), "n2": Mock(), "n3": Mock()},
            dependencies={},
            max_workers=4
        )

        current_running = {"n1", "n2"}

        usage = calculate_resource_usage(context, current_running)

        assert usage["total_nodes"] == 3
        assert usage["max_workers"] == 4
        assert usage["current_running"] == 2
        assert usage["worker_utilization"] == 50.0  # 2/4 * 100
        assert usage["available_workers"] == 2
        assert set(usage["running_nodes"]) == {"n1", "n2"}

    def test_calculate_resource_usage_edge_cases(self):
        context = ExecutionContext(
            nodes={},
            dependencies={},
            max_workers=0
        )

        usage = calculate_resource_usage(context, set())

        assert usage["worker_utilization"] == 0
        assert usage["available_workers"] == 0

    def test_estimate_remaining_time(self):
        # 3グループ完了、5グループ合計、60秒経過
        remaining_time = estimate_remaining_time(3, 5, 60.0)

        # 平均20秒/グループ、残り2グループ = 40秒
        assert remaining_time == 40.0

    def test_estimate_remaining_time_edge_cases(self):
        # まだ開始していない
        assert estimate_remaining_time(0, 5, 0.0) == 0.0

        # 既に完了
        assert estimate_remaining_time(5, 5, 100.0) == 0.0

        # 完了数が総数を超える（異常ケース）
        assert estimate_remaining_time(6, 5, 120.0) == 0.0
