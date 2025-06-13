"""並行実行機能 - request_execution_graph.pyから分離"""
import os
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from src.domain.results.result import OperationResult

from .execution_core import RequestNode


class ParallelExecutor:
    """並行実行専用クラス"""

    def __init__(self, graph):
        """
        Args:
            graph: RequestExecutionGraph
        """
        self.graph = graph

    def execute(self, driver=None, max_workers: int = 4,
                executor_class: type = ThreadPoolExecutor) -> list[OperationResult]:
        """並行実行（純粋関数版）

        Args:
            driver: 実行に使用するドライバー
            max_workers: 最大ワーカー数（CPUコア数に基づいて自動調整）
            executor_class: 使用するExecutorクラス（テスト用）

        Returns:
            List[OperationResult]: 実行結果のリスト
        """
        from ..execution_planning import calculate_optimal_workers, create_execution_plan
        from ..result_processing import collect_workflow_result, create_legacy_operation_results

        # 純粋関数による計算
        dependencies = {node_id: set(self.graph.get_dependencies(node_id)) for node_id in self.graph.nodes}
        cpu_count = os.cpu_count() or 1
        optimal_workers = calculate_optimal_workers(max_workers, cpu_count)
        execution_plan = create_execution_plan(self.graph.nodes, dependencies, optimal_workers)

        # 副作用 (実際の実行) のみここで実行
        execution_results = self._execute_plan(execution_plan, driver, executor_class)

        # 純粋関数による結果処理
        node_statuses = {node_id: node.status for node_id, node in self.graph.nodes.items()}
        workflow_result = collect_workflow_result(execution_results, execution_plan, node_statuses)

        # レガシーAPI互換性のためOperationResultリストを返却
        return create_legacy_operation_results(workflow_result)

    def _execute_plan(self, execution_plan, driver, executor_class) -> dict:
        """実行計画を実際に実行（副作用を集約）

        Args:
            execution_plan: 実行計画
            driver: 実行ドライバー
            executor_class: Executorクラス

        Returns:
            実行結果辞書
        """
        execution_context = self._setup_execution_environment(execution_plan)

        # グローバルスレッドプールで実行
        with executor_class(max_workers=execution_plan.max_workers) as executor:
            for group in execution_plan.parallel_groups:
                group_result = self._process_execution_group(
                    group, executor, driver, execution_plan, execution_context
                )
                execution_context.update(group_result)

        return execution_context['all_results']

    def _setup_execution_environment(self, execution_plan) -> dict[str, Any]:
        """実行環境をセットアップする純粋関数

        Args:
            execution_plan: 実行計画

        Returns:
            実行コンテキスト
        """
        return {
            'all_results': {},
            'failed_nodes': set(),
            'max_workers': execution_plan.max_workers
        }

    def _process_execution_group(self, group: list[str], executor, driver,
                               execution_plan, execution_context: dict[str, Any]) -> dict[str, Any]:
        """実行グループを処理する

        Args:
            group: 実行グループ
            executor: スレッドプールエグゼキューター
            driver: 実行ドライバー
            execution_plan: 実行計画
            execution_context: 実行コンテキスト

        Returns:
            更新された実行コンテキスト
        """
        from ..execution_planning import NodeExecutionStatus, filter_executable_nodes

        # 純粋関数で実行可能ノードをフィルタ
        node_statuses = [
            NodeExecutionStatus(
                node_id=node_id,
                status=self.graph.nodes[node_id].status,
                allow_failure=getattr(self.graph.nodes[node_id].request, 'allow_failure', False)
            )
            for node_id in group
        ]

        executable_nodes = filter_executable_nodes(
            node_statuses, execution_context['failed_nodes'], execution_plan.node_dependencies
        )

        if not executable_nodes:
            # 実行可能ノードなし、スキップ
            self._mark_group_nodes_skipped(group)
            return execution_context

        # バッチ処理で効率化
        futures_batch = self._submit_batch(executor, executable_nodes, driver)

        # 結果を収集
        group_results = self._collect_group_results(futures_batch, execution_context)

        return group_results

    def _mark_group_nodes_skipped(self, group: list[str]) -> None:
        """グループ内のノードをスキップ状態にマーク

        Args:
            group: スキップするグループ
        """
        for node_id in group:
            if self.graph.nodes[node_id].status == "pending":
                self.graph.nodes[node_id].status = "skipped"

    def _submit_batch(self, executor, node_ids: list[str], driver) -> list[tuple]:
        """ノードをバッチでスレッドプールに送信

        Args:
            executor: ThreadPoolExecutor
            node_ids: 実行するノードIDのリスト
            driver: 実行ドライバー

        Returns:
            List[Tuple[Future, str]]: (Future, node_id)のリスト
        """
        futures = []

        for node_id in node_ids:
            node = self.graph.nodes[node_id]

            # 結果置換を適用
            self.graph.apply_result_substitution_to_request(node.request, node_id)

            # リクエスト実行前のデバッグ出力
            from .execution_debug import debug_request_before_execution
            debug_request_before_execution(self.graph.debug_logger, node, node_id)

            node.status = "running"

            # タスクを送信
            future = executor.submit(self._execute_node_safe, node, driver)
            futures.append((future, node_id))

        return futures

    def _execute_node_safe(self, node: RequestNode, driver) -> OperationResult:
        """ノードを安全に実行（例外ハンドリング付き）

        Args:
            node: 実行するノード
            driver: 実行ドライバー

        Returns:
            OperationResult: 実行結果
        """
        try:
            return node.request.execute(driver=driver)
        except Exception as e:
            # 例外をキャッチしてエラー結果を返す
            error_msg = f"{e!s}\n{traceback.format_exc()}"
            return OperationResult(success=False, error_message=error_msg)

    def _collect_group_results(self, futures_batch: list, execution_context: dict[str, Any]) -> dict[str, Any]:
        """グループの実行結果を収集

        Args:
            futures_batch: FutureとノードIDのリスト
            execution_context: 実行コンテキスト

        Returns:
            更新された実行コンテキスト
        """
        for future, node_id in futures_batch:
            node = self.graph.nodes[node_id]

            try:
                result = future.result(timeout=300)  # 5分のタイムアウト
                self._handle_successful_execution(node, node_id, result, execution_context)

            except Exception as e:
                self._handle_failed_execution(node, node_id, e, execution_context)

        return execution_context

    def _handle_successful_execution(self, node: RequestNode, node_id: str,
                                   result: OperationResult, execution_context: dict[str, Any]) -> None:
        """成功した実行の処理

        Args:
            node: 実行したノード
            node_id: ノードID
            result: 実行結果
            execution_context: 実行コンテキスト
        """
        node.result = result
        node.status = "completed" if result.success else "failed"
        execution_context['all_results'][node_id] = result

        # 実行結果を蓄積
        self.graph.execution_results[node_id] = result

        if not result.success and not getattr(node.request, 'allow_failure', False):
            execution_context['failed_nodes'].add(node_id)

    def _handle_failed_execution(self, node: RequestNode, node_id: str,
                               exception: Exception, execution_context: dict[str, Any]) -> None:
        """失敗した実行の処理

        Args:
            node: 実行したノード
            node_id: ノードID
            exception: 発生した例外
            execution_context: 実行コンテキスト
        """
        node.status = "failed"
        error_result = OperationResult(success=False, error_message=str(exception))
        node.result = error_result
        execution_context['all_results'][node_id] = error_result

        # エラー結果も蓄積
        self.graph.execution_results[node_id] = error_result

        if not getattr(node.request, 'allow_failure', False):
            execution_context['failed_nodes'].add(node_id)
