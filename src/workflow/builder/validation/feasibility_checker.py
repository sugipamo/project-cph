"""実行可能性チェッカー

ワークフローの実行可能性を検証する純粋関数群
"""
from typing import Any, Dict, List

from .connectivity_analyzer import ValidationResult


def validate_execution_feasibility(graph: Any) -> ValidationResult:
    """実行可能性を検証（純粋関数）

    Args:
        graph: RequestExecutionGraph

    Returns:
        検証結果
    """
    errors = []
    warnings = []
    suggestions = []

    try:
        # 各種検証を個別の関数で実行
        cycle_errors, cycle_suggestions = _validate_cycles(graph)
        order_errors, order_warnings, order_suggestions = _validate_execution_order(graph)
        parallel_warnings, parallel_suggestions, max_parallelism = _validate_parallel_execution(graph)

        # 結果をマージ
        errors.extend(cycle_errors)
        errors.extend(order_errors)
        warnings.extend(order_warnings)
        warnings.extend(parallel_warnings)
        suggestions.extend(cycle_suggestions)
        suggestions.extend(order_suggestions)
        suggestions.extend(parallel_suggestions)

        # 統計情報を作成
        statistics = _create_feasibility_statistics(graph, max_parallelism)

    except Exception as e:
        errors.append(f"Validation failed with exception: {e!s}")
        statistics = {}

    if errors:
        return ValidationResult.failure(errors, warnings, suggestions, statistics)
    return ValidationResult.success(warnings, suggestions, statistics)


def _validate_cycles(graph: Any) -> tuple[List[str], List[str]]:
    """循環依存の検証"""
    errors = []
    suggestions = []

    cycles = graph.detect_cycles() if hasattr(graph, 'detect_cycles') else []
    if cycles:
        errors.append(f"Circular dependencies detected: {cycles}")
        suggestions.append("Remove circular dependencies to enable execution")

    return errors, suggestions


def _validate_execution_order(graph: Any) -> tuple[List[str], List[str], List[str]]:
    """実行順序の検証"""
    errors = []
    warnings = []
    suggestions = []

    try:
        execution_order = graph.get_execution_order() if hasattr(graph, 'get_execution_order') else []
        if not execution_order:
            warnings.append("Cannot determine execution order")
        else:
            suggestions.append(f"Execution order determined with {len(execution_order)} steps")
    except Exception as e:
        errors.append(f"Cannot determine execution order: {e!s}")

    return errors, warnings, suggestions


def _validate_parallel_execution(graph: Any) -> tuple[List[str], List[str], int]:
    """並列実行の検証"""
    warnings = []
    suggestions = []
    max_parallelism = 0

    try:
        parallel_groups = graph.get_parallel_groups() if hasattr(graph, 'get_parallel_groups') else []
        max_parallelism = max(len(group) for group in parallel_groups) if parallel_groups else 0

        if max_parallelism == 1:
            warnings.append("No parallelism possible - all steps must run sequentially")
            suggestions.append("Consider reducing dependencies to enable parallelism")
        else:
            suggestions.append(f"Maximum parallelism: {max_parallelism} concurrent steps")
    except Exception as e:
        warnings.append(f"Cannot determine parallel execution groups: {e!s}")

    return warnings, suggestions, max_parallelism


def _create_feasibility_statistics(graph: Any, max_parallelism: int) -> Dict[str, Any]:
    """実行可能性統計の作成"""
    try:
        cycles = graph.detect_cycles() if hasattr(graph, 'detect_cycles') else []
        parallel_groups = graph.get_parallel_groups() if hasattr(graph, 'get_parallel_groups') else []

        return {
            'has_cycles': len(cycles) > 0,
            'cycle_count': len(cycles),
            'max_parallelism': max_parallelism,
            'execution_groups': len(parallel_groups)
        }
    except Exception:
        return {
            'has_cycles': False,
            'cycle_count': 0,
            'max_parallelism': 0,
            'execution_groups': 0
        }
