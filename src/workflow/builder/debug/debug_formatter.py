"""デバッグ出力フォーマッター（純粋関数版）"""
from typing import Any, Dict, List

from .debug_context import DebugContext, DebugEvent


def format_execution_debug(node_id: str,
                          step_type: str,
                          context: DebugContext,
                          **kwargs) -> str:
    """実行デバッグ情報をフォーマット（純粋関数）

    Args:
        node_id: ノードID
        step_type: ステップタイプ
        context: デバッグコンテキスト
        **kwargs: 追加の実行情報

    Returns:
        フォーマットされたデバッグメッセージ
    """
    if not context.enabled:
        return ""

    parts = [f"Executing {step_type} [{node_id}]"]

    # コマンド情報
    if kwargs.get('cmd'):
        cmd_str = ' '.join(kwargs['cmd']) if isinstance(kwargs['cmd'], list) else str(kwargs['cmd'])
        parts.append(f"cmd: {cmd_str}")

    # パス情報
    if kwargs.get('path'):
        parts.append(f"path: {kwargs['path']}")

    if kwargs.get('dest'):
        source = kwargs.get('source', '')
        if source:
            parts.append(f"copy: {source} -> {kwargs['dest']}")
        else:
            parts.append(f"dest: {kwargs['dest']}")

    # オプション情報
    options = []
    if kwargs.get('allow_failure'):
        options.append("allow_failure")
    if kwargs.get('show_output'):
        options.append("show_output")

    if options:
        parts.append(f"options: {', '.join(options)}")

    return " | ".join(parts)


def format_validation_debug(validation_type: str,
                           result: Any,
                           context: DebugContext) -> str:
    """検証デバッグ情報をフォーマット（純粋関数）

    Args:
        validation_type: 検証タイプ
        result: 検証結果
        context: デバッグコンテキスト

    Returns:
        フォーマットされたデバッグメッセージ
    """
    if not context.enabled:
        return ""

    if hasattr(result, 'is_valid'):
        status = "PASS" if result.is_valid else "FAIL"
        error_count = len(getattr(result, 'errors', []))
        warning_count = len(getattr(result, 'warnings', []))

        parts = [f"Validation {validation_type}: {status}"]

        if error_count > 0:
            parts.append(f"errors: {error_count}")

        if warning_count > 0:
            parts.append(f"warnings: {warning_count}")

        return " | ".join(parts)

    return f"Validation {validation_type}: completed"


def format_graph_debug(operation: str,
                      graph_info: Dict[str, Any],
                      context: DebugContext) -> str:
    """グラフデバッグ情報をフォーマット（純粋関数）

    Args:
        operation: 操作名
        graph_info: グラフ情報
        context: デバッグコンテキスト

    Returns:
        フォーマットされたデバッグメッセージ
    """
    if not context.enabled:
        return ""

    parts = [f"Graph {operation}"]

    if 'node_count' in graph_info:
        parts.append(f"nodes: {graph_info['node_count']}")

    if 'edge_count' in graph_info:
        parts.append(f"edges: {graph_info['edge_count']}")

    if 'parallel_groups' in graph_info:
        parts.append(f"groups: {graph_info['parallel_groups']}")

    if 'max_parallelism' in graph_info:
        parts.append(f"max_parallel: {graph_info['max_parallelism']}")

    return " | ".join(parts)


def format_optimization_debug(optimization_type: str,
                             stats: Dict[str, Any],
                             context: DebugContext) -> str:
    """最適化デバッグ情報をフォーマット（純粋関数）

    Args:
        optimization_type: 最適化タイプ
        stats: 最適化統計
        context: デバッグコンテキスト

    Returns:
        フォーマットされたデバッグメッセージ
    """
    if not context.enabled:
        return ""

    parts = [f"Optimization {optimization_type}"]

    if 'original_edges' in stats and 'optimized_edges' in stats:
        original = stats['original_edges']
        optimized = stats['optimized_edges']
        reduction = original - optimized
        percentage = (reduction / original * 100) if original > 0 else 0
        parts.append(f"edges: {original} -> {optimized} (-{reduction}, -{percentage:.1f}%)")

    if 'removed_redundant' in stats:
        parts.append(f"redundant_removed: {stats['removed_redundant']}")

    if 'execution_time_ms' in stats:
        parts.append(f"time: {stats['execution_time_ms']}ms")

    return " | ".join(parts)


def format_debug_summary(events: List[DebugEvent]) -> str:
    """デバッグイベントサマリーをフォーマット（純粋関数）

    Args:
        events: デバッグイベントリスト

    Returns:
        フォーマットされたサマリー
    """
    if not events:
        return "No debug events recorded"

    from .debug_context import aggregate_debug_statistics
    stats = aggregate_debug_statistics(events)

    lines = [
        "Debug Session Summary",
        "=" * 50,
        f"Total Events: {stats['total_events']}",
        f"Duration: {stats['duration_seconds']:.2f} seconds",
        ""
    ]

    # レベル別統計
    if stats['by_level']:
        lines.append("Events by Level:")
        for level, count in sorted(stats['by_level'].items()):
            lines.append(f"  {level}: {count}")
        lines.append("")

    # コンポーネント別統計
    if stats['by_component']:
        lines.append("Events by Component:")
        for component, count in sorted(stats['by_component'].items()):
            lines.append(f"  {component}: {count}")
        lines.append("")

    # イベントタイプ別統計
    if stats['by_event_type']:
        lines.append("Events by Type:")
        for event_type, count in sorted(stats['by_event_type'].items()):
            lines.append(f"  {event_type}: {count}")

    return "\n".join(lines)


def format_debug_timeline(events: List[DebugEvent], max_events: int = 20) -> str:
    """デバッグイベントタイムラインをフォーマット（純粋関数）

    Args:
        events: デバッグイベントリスト
        max_events: 表示する最大イベント数

    Returns:
        フォーマットされたタイムライン
    """
    if not events:
        return "No events in timeline"

    # 最新のイベントを表示
    recent_events = sorted(events, key=lambda e: e.timestamp)[-max_events:]

    lines = [
        "Debug Timeline (most recent)",
        "=" * 50
    ]

    for event in recent_events:
        timestamp = event.timestamp.strftime("%H:%M:%S.%f")[:-3]
        level_marker = {
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'debug': '🔍'
        }.get(event.level, '📝')

        line = f"{timestamp} {level_marker} {event.component}.{event.event_type}: {event.message}"
        lines.append(line)

    return "\n".join(lines)
