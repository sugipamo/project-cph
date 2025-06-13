"""順次実行機能 - request_execution_graph.pyから分離"""

from src.domain.results.result import OperationResult

from .execution_core import NodeExecutionResult, RequestNode


class SequentialExecutor:
    """順次実行専用クラス"""

    def __init__(self, graph):
        """
        Args:
            graph: RequestExecutionGraph
        """
        self.graph = graph

    def execute(self, driver=None) -> list[OperationResult]:
        """順次実行"""
        execution_order = self.graph.get_execution_order()
        results = []

        # ワークフロー開始ログ
        self.graph.debug_logger.log_workflow_start(len(execution_order), parallel=False)

        for node_id in execution_order:
            node = self.graph.nodes[node_id]

            # ノードを準備して実行
            execution_result = self._execute_single_node(node, node_id, driver)
            results.append(execution_result.result)

            # 失敗時の早期終了処理
            if execution_result.should_stop:
                break

        return results

    def _execute_single_node(self, node: RequestNode, node_id: str, driver) -> NodeExecutionResult:
        """単一ノードを実行（純粋な実行ロジック）

        Args:
            node: 実行するノード
            node_id: ノードID
            driver: 実行ドライバー

        Returns:
            ノード実行結果
        """
        # 結果置換を適用
        self.graph.apply_result_substitution_to_request(node.request, node_id)

        # リクエスト実行前のデバッグ出力
        self._debug_request_before_execution(node, node_id)

        # ステータスを更新
        node.status = "running"

        try:
            # リクエストを実行
            result = node.request.execute(driver=driver)
            return self._handle_execution_success(node, node_id, result)

        except Exception as e:
            return self._handle_execution_error(node, node_id, e)

    def _handle_execution_success(self, node: RequestNode, node_id: str, result: OperationResult) -> NodeExecutionResult:
        """実行成功時の処理

        Args:
            node: 実行したノード
            node_id: ノードID
            result: 実行結果

        Returns:
            ノード実行結果
        """
        node.result = result
        node.status = "completed" if result.success else "failed"

        # 実行結果を蓄積
        self.graph.execution_results[node_id] = result

        # 失敗時の処理判定
        should_stop = not result.success and not getattr(node.request, 'allow_failure', False)
        if should_stop:
            self.graph._mark_dependent_nodes_skipped(node_id)

        return NodeExecutionResult(result=result, should_stop=should_stop)

    def _handle_execution_error(self, node: RequestNode, node_id: str, exception: Exception) -> NodeExecutionResult:
        """実行エラー時の処理

        Args:
            node: 実行したノード
            node_id: ノードID
            exception: 発生した例外

        Returns:
            ノード実行結果
        """
        node.status = "failed"

        # エラー結果を作成
        error_result = OperationResult(success=False, error_message=str(exception))
        node.result = error_result

        # エラー結果も蓄積
        self.graph.execution_results[node_id] = error_result

        # 失敗時の処理判定
        should_stop = not getattr(node.request, 'allow_failure', False)
        if should_stop:
            self.graph._mark_dependent_nodes_skipped(node_id)

        return NodeExecutionResult(result=error_result, should_stop=should_stop)

    def _debug_request_before_execution(self, node: RequestNode, node_id: str):
        """リクエスト実行前のデバッグ出力

        Args:
            node: 実行するリクエストノード
            node_id: ノードID
        """
        from .execution_debug import debug_request_before_execution
        debug_request_before_execution(self.graph.debug_logger, node, node_id)
