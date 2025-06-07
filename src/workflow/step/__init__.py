"""
純粋関数ベースのステップ生成モジュール

このモジュールは、JSONワークフロー定義から実行可能なCompositeRequestまでの
完全な変換パイプラインを提供します。

主な特徴:
- 純粋関数によるステップ生成（副作用なし）
- 不変データ構造の使用
- 依存関係の自動解決
- ステップの最適化
- 包括的な検証とエラーハンドリング
"""

from .step import Step, StepType, StepContext, StepGenerationResult
from .core import (
    generate_steps_from_json,
    create_step_from_json,
    format_template,
    validate_step_sequence,
    optimize_step_sequence
)
from .dependency import (
    resolve_dependencies,
    optimize_mkdir_steps,
    analyze_step_dependencies
)
from .workflow import (
    generate_workflow_from_json,
    create_step_context_from_env_context,
    validate_workflow_execution,
    debug_workflow_generation
)

__all__ = [
    # Core data structures
    'Step',
    'StepType', 
    'StepContext',
    'StepGenerationResult',
    
    # Core step generation
    'generate_steps_from_json',
    'create_step_from_json',
    'format_template',
    'validate_step_sequence',
    'optimize_step_sequence',
    
    # Dependency resolution
    'resolve_dependencies',
    'optimize_mkdir_steps',
    'analyze_step_dependencies',
    
    
    # High-level workflow API
    'generate_workflow_from_json',
    'create_step_context_from_env_context',
    'validate_workflow_execution',
    'debug_workflow_generation',
]