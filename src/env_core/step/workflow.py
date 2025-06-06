"""
完全な純粋関数ベースのワークフロー生成・実行パイプライン
"""
from typing import List, Dict, Any, Tuple
from src.operations.composite.composite_request import CompositeRequest
from .step import Step, StepContext, StepGenerationResult
from .core import generate_steps_from_json, validate_step_sequence, optimize_step_sequence
from .dependency import resolve_dependencies, optimize_mkdir_steps
def steps_to_requests(steps: List[Step], operations) -> CompositeRequest:
    """
    Convert a list of steps to a CompositeRequest using RequestFactoryV2
    
    Args:
        steps: List of Step objects to convert
        operations: Operations object (contains context)
        
    Returns:
        CompositeRequest: Composite request containing all converted steps
    """
    from src.operations.factory.unified_request_factory import UnifiedRequestFactory
    
    requests = []
    factory = UnifiedRequestFactory()
    
    for step in steps:
        request = factory.create_request(step, context=operations)
        if request is not None:
            requests.append(request)
    
    return CompositeRequest(requests, debug_tag="workflow")


def generate_workflow_from_json(
    json_steps: List[Dict[str, Any]], 
    context: StepContext,
    operations
) -> Tuple[CompositeRequest, List[str], List[str]]:
    """
    JSONステップからCompositeRequestまでの完全なパイプラインを実行する純粋関数
    
    Args:
        json_steps: JSONから読み込んだステップのリスト
        context: ステップ生成に必要なコンテキスト情報
        operations: DIコンテナ（ドライバ取得用）
        
    Returns:
        Tuple[CompositeRequest, List[str], List[str]]: 
            (実行可能リクエスト, エラーリスト, 警告リスト)
    """
    # 1. JSON から Step オブジェクトを生成
    generation_result = generate_steps_from_json(json_steps, context)
    
    if not generation_result.is_success:
        # エラーがある場合は空のリクエストを返す
        empty_request = CompositeRequest.make_composite_request([])
        return empty_request, generation_result.errors, generation_result.warnings
    
    steps = generation_result.steps
    errors = list(generation_result.errors)
    warnings = list(generation_result.warnings)
    
    # 2. ステップシーケンスの検証
    validation_errors = validate_step_sequence(steps)
    if validation_errors:
        errors.extend(validation_errors)
        empty_request = CompositeRequest.make_composite_request([])
        return empty_request, errors, warnings
    
    # 3. 依存関係の解決（必要な準備ステップを挿入）
    resolved_steps = resolve_dependencies(steps, context)
    
    # 4. ステップの最適化
    optimized_steps = optimize_workflow_steps(resolved_steps)
    
    # 5. Step から Request への変換
    composite_request = steps_to_requests(optimized_steps, operations)
    
    return composite_request, errors, warnings


def optimize_workflow_steps(steps: List[Step]) -> List[Step]:
    """
    ワークフローステップ全体を最適化する純粋関数
    
    Args:
        steps: 最適化対象のステップリスト
        
    Returns:
        List[Step]: 最適化されたステップリスト
    """
    # 1. 基本的なシーケンス最適化
    optimized = optimize_step_sequence(steps)
    
    # 2. mkdir ステップの最適化
    optimized = optimize_mkdir_steps(optimized)
    
    # 3. 追加の最適化（将来拡張可能）
    # - 冗長なコピー操作の除去
    # - 一時ファイルの最適化
    # - パラレル実行可能なステップの特定
    
    return optimized


def create_step_context_from_env_context(env_context) -> StepContext:
    """
    EnvContext から StepContext を作成するヘルパー関数
    
    Args:
        env_context: 既存の環境コンテキスト
        
    Returns:
        StepContext: 新しいステップコンテキスト
    """
    return StepContext(
        contest_name=env_context.contest_name,
        problem_name=env_context.problem_name,
        language=env_context.language,
        env_type=env_context.env_type,
        command_type=env_context.command_type,
        workspace_path=getattr(env_context, 'workspace_path', ''),
        contest_current_path=getattr(env_context, 'contest_current_path', ''),
        contest_stock_path=getattr(env_context, 'contest_stock_path', None),
        contest_template_path=getattr(env_context, 'contest_template_path', None),
        contest_temp_path=getattr(env_context, 'contest_temp_path', None),
        source_file_name=getattr(env_context, 'source_file_name', None),
        language_id=getattr(env_context, 'language_id', None),
        previous_contest_name=getattr(env_context, 'previous_contest_name', None),
        previous_problem_name=getattr(env_context, 'previous_problem_name', None)
    )


def validate_workflow_execution(
    composite_request: CompositeRequest,
    errors: List[str],
    warnings: List[str]
) -> Tuple[bool, List[str]]:
    """
    ワークフロー実行前の最終検証を行う純粋関数
    
    Args:
        composite_request: 実行予定のコンポジットリクエスト
        errors: これまでに発生したエラーリスト
        warnings: これまでに発生した警告リスト
        
    Returns:
        Tuple[bool, List[str]]: (実行可能かどうか, 検証メッセージ)
    """
    messages = []
    
    # エラーがある場合は実行不可
    if errors:
        messages.append(f"Found {len(errors)} errors:")
        messages.extend([f"  - {error}" for error in errors])
        return False, messages
    
    # 警告がある場合は報告
    if warnings:
        messages.append(f"Found {len(warnings)} warnings:")
        messages.extend([f"  - {warning}" for warning in warnings])
    
    # リクエストが空の場合
    if not composite_request.requests:
        messages.append("No executable requests generated")
        return False, messages
    
    # 成功
    messages.append(f"Generated {len(composite_request.requests)} executable requests")
    
    return True, messages


def debug_workflow_generation(
    json_steps: List[Dict[str, Any]], 
    context: StepContext
) -> Dict[str, Any]:
    """
    ワークフロー生成の各段階をデバッグ情報として返す純粋関数
    
    Args:
        json_steps: JSONから読み込んだステップのリスト
        context: ステップ生成に必要なコンテキスト情報
        
    Returns:
        Dict[str, Any]: 各段階のデバッグ情報
    """
    debug_info = {
        'input_steps': len(json_steps),
        'stages': {}
    }
    
    # 1. JSON から Step オブジェクトを生成
    generation_result = generate_steps_from_json(json_steps, context)
    debug_info['stages']['step_generation'] = {
        'generated_steps': len(generation_result.steps),
        'errors': generation_result.errors,
        'warnings': generation_result.warnings,
        'steps': [{'type': step.type.value, 'cmd': step.cmd} for step in generation_result.steps]
    }
    
    if generation_result.is_success:
        # 2. 依存関係の解決
        resolved_steps = resolve_dependencies(generation_result.steps, context)
        debug_info['stages']['dependency_resolution'] = {
            'original_steps': len(generation_result.steps),
            'resolved_steps': len(resolved_steps),
            'added_steps': len(resolved_steps) - len(generation_result.steps),
            'steps': [{'type': step.type.value, 'cmd': step.cmd} for step in resolved_steps]
        }
        
        # 3. 最適化
        optimized_steps = optimize_workflow_steps(resolved_steps)
        debug_info['stages']['optimization'] = {
            'pre_optimization': len(resolved_steps),
            'post_optimization': len(optimized_steps),
            'removed_steps': len(resolved_steps) - len(optimized_steps),
            'steps': [{'type': step.type.value, 'cmd': step.cmd} for step in optimized_steps]
        }
    
    return debug_info