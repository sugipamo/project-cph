"""
純粋関数ベースのステップ生成の核となる関数群
"""
from typing import List, Dict, Any, Optional
from .step import Step, StepType, StepContext, StepGenerationResult


def generate_steps_from_json(
    json_steps: List[Dict[str, Any]], 
    context: StepContext
) -> StepGenerationResult:
    """
    JSONステップリストから実行可能ステップを生成する純粋関数
    
    Args:
        json_steps: JSONから読み込んだステップのリスト
        context: ステップ生成に必要なコンテキスト情報
        
    Returns:
        StepGenerationResult: 生成されたステップとエラー/警告情報
    """
    steps = []
    errors = []
    warnings = []
    
    for i, json_step in enumerate(json_steps):
        try:
            step = create_step_from_json(json_step, context)
            steps.append(step)
        except ValueError as e:
            errors.append(f"Step {i}: {str(e)}")
        except Exception as e:
            errors.append(f"Step {i}: Unexpected error - {str(e)}")
    
    return StepGenerationResult(steps, errors, warnings)


def create_step_from_json(json_step: Dict[str, Any], context: StepContext) -> Step:
    """
    単一のJSONステップから実行可能ステップを生成する純粋関数
    
    Args:
        json_step: JSONステップの辞書
        context: ステップ生成コンテキスト
        
    Returns:
        Step: 生成されたステップ
        
    Raises:
        ValueError: 無効なステップ定義の場合
    """
    step_type_str = json_step.get('type')
    if not step_type_str:
        raise ValueError("Step must have 'type' field")
    
    try:
        step_type = StepType(step_type_str)
    except ValueError:
        raise ValueError(f"Unknown step type: {step_type_str}")
    
    raw_cmd = json_step.get('cmd', [])
    if not isinstance(raw_cmd, list):
        raise ValueError("Step 'cmd' must be a list")
    
    # コマンドの文字列フォーマット
    formatted_cmd = [format_template(arg, context) for arg in raw_cmd]
    
    # オプション属性の処理
    allow_failure = json_step.get('allow_failure', False)
    show_output = json_step.get('show_output', False)
    
    cwd = format_template(json_step.get('cwd'), context) if json_step.get('cwd') else None
    force_env_type = json_step.get('force_env_type')
    format_options = json_step.get('format_options')
    output_format = json_step.get('output_format')
    format_preset = json_step.get('format_preset')
    
    return Step(
        type=step_type,
        cmd=formatted_cmd,
        allow_failure=allow_failure,
        show_output=show_output,
        cwd=cwd,
        force_env_type=force_env_type,
        format_options=format_options,
        output_format=output_format,
        format_preset=format_preset
    )


def format_template(template: Any, context: StepContext) -> str:
    """
    テンプレート文字列をコンテキスト情報でフォーマットする純粋関数
    
    Args:
        template: フォーマット対象の値
        context: フォーマット用のコンテキスト
        
    Returns:
        str: フォーマット済みの文字列
    """
    if not isinstance(template, str):
        return str(template) if template is not None else ""
    
    format_dict = context.to_format_dict()
    
    result = template
    for key, value in format_dict.items():
        placeholder = f'{{{key}}}'
        if placeholder in result:
            result = result.replace(placeholder, str(value))
    
    return result


def validate_step_sequence(steps: List[Step]) -> List[str]:
    """
    ステップシーケンスの妥当性を検証する純粋関数
    
    Args:
        steps: 検証対象のステップリスト
        
    Returns:
        List[str]: 検証エラーのリスト（空の場合は妥当）
    """
    errors = []
    
    for i, step in enumerate(steps):
        # 各ステップの基本検証
        step_errors = validate_single_step(step)
        for error in step_errors:
            errors.append(f"Step {i} ({step.type.value}): {error}")
    
    return errors


def validate_single_step(step: Step) -> List[str]:
    """
    単一ステップの妥当性を検証する純粋関数
    
    Args:
        step: 検証対象のステップ
        
    Returns:
        List[str]: 検証エラーのリスト
    """
    errors = []
    
    # コマンドの空チェック
    if not step.cmd:
        errors.append("Command cannot be empty")
        return errors
    
    # 各ステップタイプ固有の検証
    if step.type in [StepType.COPY, StepType.MOVE, StepType.MOVETREE]:
        if len(step.cmd) < 2:
            errors.append(f"Requires at least 2 arguments (src, dst), got {len(step.cmd)}")
        elif not step.cmd[0] or not step.cmd[1]:
            errors.append("Source and destination paths cannot be empty")
    
    elif step.type in [StepType.MKDIR, StepType.TOUCH, StepType.REMOVE, StepType.RMTREE]:
        if len(step.cmd) < 1:
            errors.append("Requires at least 1 argument (path)")
        elif not step.cmd[0]:
            errors.append("Path cannot be empty")
    
    elif step.type in [StepType.SHELL, StepType.PYTHON, StepType.OJ, StepType.TEST, StepType.BUILD]:
        if not step.cmd[0]:
            errors.append("Command cannot be empty")
    
    return errors


def optimize_step_sequence(steps: List[Step]) -> List[Step]:
    """
    ステップシーケンスを最適化する純粋関数
    
    Args:
        steps: 最適化対象のステップリスト
        
    Returns:
        List[Step]: 最適化されたステップリスト
    """
    # 連続する同じディレクトリのmkdirを統合
    optimized = []
    i = 0
    
    while i < len(steps):
        step = steps[i]
        
        if step.type == StepType.MKDIR:
            # 連続するmkdirステップを収集
            mkdir_paths = [step.cmd[0]]
            j = i + 1
            
            while j < len(steps) and steps[j].type == StepType.MKDIR:
                mkdir_paths.append(steps[j].cmd[0])
                j += 1
            
            # 重複を除去して追加
            unique_paths = list(dict.fromkeys(mkdir_paths))  # 順序を保持して重複除去
            for path in unique_paths:
                optimized.append(Step(
                    type=StepType.MKDIR,
                    cmd=[path],
                    allow_failure=step.allow_failure,
                    show_output=step.show_output
                ))
            
            i = j
        else:
            optimized.append(step)
            i += 1
    
    return optimized