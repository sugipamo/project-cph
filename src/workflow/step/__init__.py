"""純粋関数ベースのステップ生成モジュール

このモジュールは、JSONワークフロー定義から実行可能なCompositeRequestまでの
完全な変換パイプラインを提供します。

主な特徴:
- 純粋関数によるステップ生成（副作用なし）
- 不変データ構造の使用
- 依存関係の自動解決
- ステップの最適化
- 包括的な検証とエラーハンドリング
"""

from .condition_evaluator import evaluate_when_condition, validate_when_clause
from .core import (
    create_step_from_json,
    format_template,
    generate_steps_from_json,
    optimize_step_sequence,
    validate_step_sequence,
)
from .dependency import analyze_step_dependencies, optimize_mkdir_steps, resolve_dependencies
from .step import Step, StepContext, StepGenerationResult, StepType
from .workflow import (
    create_step_context_from_env_context,
    debug_workflow_generation,
    generate_workflow_from_json,
    validate_workflow_execution,
)

__all__ = [
    # Core data structures
    'Step',
    'StepContext',
    'StepGenerationResult',
    'StepType',
    'analyze_step_dependencies',
    'create_step_context_from_env_context',
    'create_step_from_json',
    'debug_workflow_generation',
    'evaluate_when_condition',
    'format_template',
    # Core step generation
    'generate_steps_from_json',
    # High-level workflow API
    'generate_workflow_from_json',
    'optimize_mkdir_steps',
    'optimize_step_sequence',
    # Dependency resolution
    'resolve_dependencies',
    'validate_step_sequence',
    'validate_when_clause',
    'validate_workflow_execution',
]
