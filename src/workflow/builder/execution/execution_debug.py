"""実行デバッグ機能 - request_execution_graph.pyから分離"""
from typing import Any

from .execution_core import RequestNode


def debug_request_before_execution(debug_logger, node: RequestNode, node_id: str):
    """リクエスト実行前のデバッグ出力

    Args:
        debug_logger: デバッグロガー
        node: 実行するリクエストノード
        node_id: ノードID
    """
    if not debug_logger.is_enabled():
        return

    req = node.request

    # リクエストタイプを取得
    step_type = "unknown"
    if hasattr(req, 'operation_type'):
        if str(req.operation_type) == "OperationType.FILE" and hasattr(req, 'op'):
            step_type = f"FILE.{req.op.name}"
        else:
            step_type = str(req.operation_type)

    # デバッグ情報を収集
    debug_kwargs = {}

    # コマンド情報
    if hasattr(req, 'cmd') and req.cmd:
        debug_kwargs['cmd'] = req.cmd

    # パス情報
    if hasattr(req, 'path') and req.path:
        debug_kwargs['path'] = req.path
    if hasattr(req, 'dst_path') and req.dst_path:
        debug_kwargs['dest'] = req.dst_path
        debug_kwargs['source'] = getattr(req, 'path', '')

    # オプション情報
    if hasattr(req, 'allow_failure'):
        debug_kwargs['allow_failure'] = req.allow_failure
    if hasattr(req, 'show_output'):
        debug_kwargs['show_output'] = req.show_output

    # デバッグログ出力
    debug_logger.log_step_start(node_id, step_type, **debug_kwargs)


class ExecutionDebugger:
    """実行デバッグ専用クラス"""
    
    def __init__(self, debug_logger):
        """
        Args:
            debug_logger: デバッグロガー
        """
        self.debug_logger = debug_logger
    
    def debug_request_before_execution(self, node: RequestNode, node_id: str):
        """リクエスト実行前のデバッグ出力"""
        debug_request_before_execution(self.debug_logger, node, node_id)
    
    def debug_execution_plan(self, execution_plan):
        """実行計画のデバッグ出力"""
        if not self.debug_logger.is_enabled():
            return
        
        self.debug_logger.log_workflow_start(
            len(execution_plan.parallel_groups), 
            parallel=True
        )
        
        for i, group in enumerate(execution_plan.parallel_groups):
            self.debug_logger.debug(f"Group {i}: {group}")
    
    def debug_node_status(self, nodes: dict[str, RequestNode]):
        """ノード状態のデバッグ出力"""
        if not self.debug_logger.is_enabled():
            return
        
        status_counts = {}
        for node in nodes.values():
            status = node.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        self.debug_logger.debug(f"Node status summary: {status_counts}")
    
    def debug_execution_results(self, execution_results: dict[str, Any]):
        """実行結果のデバッグ出力"""
        if not self.debug_logger.is_enabled():
            return
        
        success_count = sum(1 for result in execution_results.values() 
                          if hasattr(result, 'success') and result.success)
        total_count = len(execution_results)
        
        self.debug_logger.debug(
            f"Execution results: {success_count}/{total_count} successful"
        )