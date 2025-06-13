"""ワークフロー用デバッグロガーアダプター"""
from typing import Any, Dict, List, Optional
from src.utils.debug_logger import DebugLogger
from .debug_context import DebugContext, DebugEvent, create_debug_event
from .debug_formatter import (
    format_execution_debug,
    format_validation_debug,
    format_graph_debug,
    format_optimization_debug
)


class WorkflowDebugAdapter:
    """ワークフロー用デバッグロガーアダプター
    
    既存のDebugLoggerと新しい純粋関数ベースのデバッグシステムを橋渡し
    """
    
    def __init__(self, debug_logger: DebugLogger, context: DebugContext):
        """
        Args:
            debug_logger: 既存のデバッグロガー
            context: デバッグコンテキスト
        """
        self.debug_logger = debug_logger
        self.context = context
        self.events: List[DebugEvent] = []
    
    def is_enabled(self) -> bool:
        """デバッグが有効かチェック"""
        return self.context.enabled and self.debug_logger.is_enabled()
    
    def log_execution_start(self, node_id: str, step_type: str, **kwargs) -> None:
        """実行開始ログ"""
        if not self.is_enabled():
            return
        
        # 純粋関数でフォーマット
        message = format_execution_debug(node_id, step_type, self.context, **kwargs)
        
        # イベントを記録
        event = create_debug_event(
            self.context,
            level="info",
            component="execution",
            event_type="start",
            message=message,
            node_id=node_id,
            step_type=step_type,
            **kwargs
        )
        self.events.append(event)
        
        # 既存のロガーにも出力
        self.debug_logger.log_step_start(node_id, step_type, **kwargs)
    
    def log_validation_result(self, validation_type: str, result: Any) -> None:
        """検証結果ログ"""
        if not self.is_enabled():
            return
        
        # 純粋関数でフォーマット
        message = format_validation_debug(validation_type, result, self.context)
        
        # イベントを記録
        event = create_debug_event(
            self.context,
            level="info" if getattr(result, 'is_valid', True) else "warning",
            component="validation",
            event_type=validation_type,
            message=message,
            result=str(result)
        )
        self.events.append(event)
        
        # 既存のロガーにも出力
        if message:
            self.debug_logger.debug(message)
    
    def log_graph_operation(self, operation: str, graph_info: Dict[str, Any]) -> None:
        """グラフ操作ログ"""
        if not self.is_enabled():
            return
        
        # 純粋関数でフォーマット
        message = format_graph_debug(operation, graph_info, self.context)
        
        # イベントを記録
        event = create_debug_event(
            self.context,
            level="debug",
            component="graph",
            event_type=operation,
            message=message,
            **graph_info
        )
        self.events.append(event)
        
        # 既存のロガーにも出力
        if message:
            self.debug_logger.debug(message)
    
    def log_optimization_result(self, optimization_type: str, stats: Dict[str, Any]) -> None:
        """最適化結果ログ"""
        if not self.is_enabled():
            return
        
        # 純粋関数でフォーマット
        message = format_optimization_debug(optimization_type, stats, self.context)
        
        # イベントを記録
        event = create_debug_event(
            self.context,
            level="info",
            component="optimization",
            event_type=optimization_type,
            message=message,
            **stats
        )
        self.events.append(event)
        
        # 既存のロガーにも出力
        if message:
            self.debug_logger.debug(message)
    
    def log_workflow_start(self, step_count: int, parallel: bool = False) -> None:
        """ワークフロー開始ログ（既存APIとの互換性）"""
        if not self.is_enabled():
            return
        
        execution_type = "parallel" if parallel else "sequential"
        message = f"Starting {execution_type} workflow with {step_count} steps"
        
        # イベントを記録
        event = create_debug_event(
            self.context,
            level="info",
            component="workflow",
            event_type="start",
            message=message,
            step_count=step_count,
            parallel=parallel
        )
        self.events.append(event)
        
        # 既存のロガーにも出力
        self.debug_logger.log_workflow_start(step_count, parallel)
    
    def debug(self, message: str) -> None:
        """汎用デバッグメッセージ（既存APIとの互換性）"""
        if not self.is_enabled():
            return
        
        # イベントを記録
        event = create_debug_event(
            self.context,
            level="debug",
            component="general",
            event_type="message",
            message=message
        )
        self.events.append(event)
        
        # 既存のロガーにも出力
        self.debug_logger.debug(message)
    
    def get_debug_events(self) -> List[DebugEvent]:
        """記録されたデバッグイベントを取得"""
        return self.events.copy()
    
    def create_debug_summary(self) -> str:
        """デバッグサマリーを作成"""
        from .debug_formatter import format_debug_summary
        return format_debug_summary(self.events)
    
    def create_debug_timeline(self, max_events: int = 20) -> str:
        """デバッグタイムラインを作成"""
        from .debug_formatter import format_debug_timeline
        return format_debug_timeline(self.events, max_events)


def create_workflow_debug_adapter(debug_config: Optional[Dict[str, Any]] = None) -> WorkflowDebugAdapter:
    """ワークフローデバッグアダプターを作成
    
    Args:
        debug_config: デバッグ設定
        
    Returns:
        ワークフローデバッグアダプター
    """
    from .debug_context import create_debug_context
    
    # 既存のデバッグロガーを作成
    debug_logger = DebugLogger(debug_config)
    
    # デバッグコンテキストを作成
    enabled = debug_config.get('enabled', True) if debug_config else True
    level = debug_config.get('level', 'info') if debug_config else 'info'
    context = create_debug_context(enabled=enabled, level=level)
    
    return WorkflowDebugAdapter(debug_logger, context)