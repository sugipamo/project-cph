"""完全な純粋関数ベースのワークフロー生成・実行パイプライン

クリーンアーキテクチャ準拠: workflow層からinfrastructure層への直接依存を削除
"""
from typing import Any, Optional, Protocol
from domain.dependency import optimize_copy_steps, optimize_mkdir_steps, resolve_dependencies
from workflow.step.step import Step, StepContext
from workflow.step.step_generation_service import generate_steps_from_json, optimize_step_sequence, validate_step_sequence

class CompositeRequestInterface(Protocol):
    """Composite request interface for dependency inversion"""
    requests: list

    def __init__(self, requests: list, debug_tag: Optional[str], name: Optional[str], execution_controller):
        ...

    @classmethod
    def make_composite_request(cls, requests: list, debug_tag: Optional[str], name: Optional[str]):
        ...

def steps_to_requests(steps: list[Step], context: StepContext, operations, composite_request_factory) -> CompositeRequestInterface:
    """Convert a list of steps to a CompositeRequest using RequestFactoryV2

    Args:
        steps: List of Step objects to convert
        context: Step context for creating requests
        operations: Operations object (DI container)
        composite_request_factory: Factory for creating composite requests

    Returns:
        CompositeRequestInterface: Composite request containing all converted steps
    """
    requests = []
    factory = operations.get_request_factory()
    for step in steps:
        request = factory.create_request_from_step(step, context, operations)
        if request is not None:
            requests.append(request)
    return composite_request_factory(requests, debug_tag='workflow', name=None, execution_controller=None)

def generate_workflow_from_json(json_steps: list[dict[str, Any]], context: StepContext, operations, composite_request_factory) -> tuple[CompositeRequestInterface, list[str], list[str]]:
    """JSONステップからCompositeRequestまでの完全なパイプラインを実行する純粋関数

    Args:
        json_steps: JSONから読み込んだステップのリスト
        context: ステップ生成に必要なコンテキスト情報
        operations: DIコンテナ（ドライバ取得用）

    Returns:
        Tuple[CompositeRequest, List[str], List[str]]:
            (実行可能リクエスト, エラーリスト, 警告リスト)
    """
    generation_result = generate_steps_from_json(json_steps, context)
    if not generation_result.is_success:
        empty_request = composite_request_factory([], debug_tag=None, name=None)
        return (empty_request, generation_result.errors, generation_result.warnings)
    steps = generation_result.steps
    errors = list(generation_result.errors)
    warnings = list(generation_result.warnings)
    validation_errors = validate_step_sequence(steps)
    if validation_errors:
        errors.extend(validation_errors)
        empty_request = composite_request_factory([], debug_tag=None, name=None)
        return (empty_request, errors, warnings)
    resolved_steps = resolve_dependencies(steps, context)
    optimized_steps = optimize_workflow_steps(resolved_steps)
    composite_request = steps_to_requests(optimized_steps, context, operations, composite_request_factory)
    return (composite_request, errors, warnings)

def optimize_workflow_steps(steps: list[Step]) -> list[Step]:
    """ワークフローステップ全体を最適化する純粋関数

    Args:
        steps: 最適化対象のステップリスト

    Returns:
        List[Step]: 最適化されたステップリスト
    """
    optimized = optimize_step_sequence(steps)
    optimized = optimize_mkdir_steps(optimized)
    optimized = optimize_copy_steps(optimized)
    return optimized

def create_step_context_from_env_context(env_context) -> StepContext:
    """EnvContext から StepContext を作成するヘルパー関数

    Args:
        env_context: 既存の環境コンテキスト

    Returns:
        StepContext: 新しいステップコンテキスト
    """
    return StepContext(contest_name=env_context.contest_name, problem_name=env_context.problem_name, language=env_context.language, env_type=env_context.env_type, command_type=env_context.command_type, local_workspace_path=env_context.local_workspace_path if hasattr(env_context, 'local_workspace_path') else env_context.workspace_path if hasattr(env_context, 'workspace_path') else '', contest_current_path=env_context.contest_current_path if hasattr(env_context, 'contest_current_path') else '', contest_stock_path=env_context.contest_stock_path if hasattr(env_context, 'contest_stock_path') else None, contest_template_path=env_context.contest_template_path if hasattr(env_context, 'contest_template_path') else None, contest_temp_path=env_context.contest_temp_path if hasattr(env_context, 'contest_temp_path') else None, source_file_name=env_context.source_file_name if hasattr(env_context, 'source_file_name') else None, language_id=env_context.language_id if hasattr(env_context, 'language_id') else None, file_patterns=env_context.file_patterns if hasattr(env_context, 'file_patterns') else None)

def validate_workflow_execution(composite_request: CompositeRequestInterface, errors: list[str], warnings: list[str]) -> tuple[bool, list[str]]:
    """ワークフロー実行前の最終検証を行う純粋関数

    Args:
        composite_request: 実行予定のコンポジットリクエスト
        errors: これまでに発生したエラーリスト
        warnings: これまでに発生した警告リスト

    Returns:
        Tuple[bool, List[str]]: (実行可能かどうか, 検証メッセージ)
    """
    messages = []
    if errors:
        messages.append(f'Found {len(errors)} errors:')
        messages.extend([f'  - {error}' for error in errors])
        return (False, messages)
    if warnings:
        messages.append(f'Found {len(warnings)} warnings:')
        messages.extend([f'  - {warning}' for warning in warnings])
    if not composite_request.requests:
        messages.append('No executable requests generated')
        return (False, messages)
    messages.append(f'Generated {len(composite_request.requests)} executable requests')
    return (True, messages)

def debug_workflow_generation(json_steps: list[dict[str, Any]], context: StepContext) -> dict[str, Any]:
    """ワークフロー生成の各段階をデバッグ情報として返す純粋関数

    Args:
        json_steps: JSONから読み込んだステップのリスト
        context: ステップ生成に必要なコンテキスト情報

    Returns:
        Dict[str, Any]: 各段階のデバッグ情報
    """
    debug_info = {'input_steps': len(json_steps), 'stages': {}}
    generation_result = generate_steps_from_json(json_steps, context)
    debug_info['stages']['step_generation'] = {'generated_steps': len(generation_result.steps), 'errors': generation_result.errors, 'warnings': generation_result.warnings, 'steps': [{'type': step.type.value, 'cmd': step.cmd} for step in generation_result.steps]}
    if generation_result.is_success:
        resolved_steps = resolve_dependencies(generation_result.steps, context)
        debug_info['stages']['dependency_resolution'] = {'original_steps': len(generation_result.steps), 'resolved_steps': len(resolved_steps), 'added_steps': len(resolved_steps) - len(generation_result.steps), 'steps': [{'type': step.type.value, 'cmd': step.cmd} for step in resolved_steps]}
        optimized_steps = optimize_workflow_steps(resolved_steps)
        debug_info['stages']['optimization'] = {'pre_optimization': len(resolved_steps), 'post_optimization': len(optimized_steps), 'removed_steps': len(resolved_steps) - len(optimized_steps), 'steps': [{'type': step.type.value, 'cmd': step.cmd} for step in optimized_steps]}
    return debug_info