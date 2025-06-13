"""結果プレースホルダー置換の純粋関数 - RequestExecutionGraphから分離"""
import re
from typing import Any, Dict, List, Tuple


def substitute_placeholders(text: str, execution_results: Dict[str, Any]) -> str:
    """テキスト内の結果プレースホルダーを実際の値で置換（純粋関数）

    形式: {{step_X.result.Y}} または {{step_X.Y}}
    例: {{step_0.result.stdout}}, {{step_test.returncode}}

    Args:
        text: 置換対象のテキスト
        execution_results: 実行結果辞書

    Returns:
        置換済みのテキスト
    """
    if not isinstance(text, str):
        return text

    # {{step_X.result.Y}}形式のパターンを検索
    pattern1 = r'\{\{step_(\w+)\.result\.(\w+)\}\}'
    # {{step_X.Y}}形式のパターンも対応
    pattern2 = r'\{\{step_(\w+)\.(\w+)\}\}'

    def replacer(match):
        step_id = match.group(1)
        field_name = match.group(2)

        if step_id in execution_results:
            result = execution_results[step_id]
            if hasattr(result, field_name):
                value = getattr(result, field_name)
                return str(value) if value is not None else ""

        # 置換できない場合は元のまま
        return match.group(0)

    # 両方のパターンを置換
    text = re.sub(pattern1, replacer, text)
    text = re.sub(pattern2, replacer, text)

    return text


def apply_substitution_to_request(request: Any, execution_results: Dict[str, Any],
                                 node_id: str) -> Any:
    """リクエストオブジェクトに結果置換を適用（純粋関数風）

    注意: この関数は実際にはrequestオブジェクトを変更するため、厳密には純粋関数ではない

    Args:
        request: 置換対象のリクエストオブジェクト
        execution_results: 実行結果辞書
        node_id: リクエストのノードID

    Returns:
        変更されたリクエストオブジェクト（副作用あり）
    """
    # ShellRequestのcmdを置換
    if hasattr(request, 'cmd') and request.cmd:
        if isinstance(request.cmd, list):
            # リスト内の各要素が文字列の場合のみ置換
            new_cmd = []
            for cmd in request.cmd:
                new_cmd.append(substitute_placeholders(cmd, execution_results))
            request.cmd = new_cmd
        else:
            request.cmd = substitute_placeholders(request.cmd, execution_results)

    # DockerRequestのcommandを置換
    if hasattr(request, 'command') and request.command:
        request.command = substitute_placeholders(request.command, execution_results)

    # その他のテキストフィールドも置換
    if hasattr(request, 'path') and request.path:
        request.path = substitute_placeholders(request.path, execution_results)
    if hasattr(request, 'dst_path') and request.dst_path:
        request.dst_path = substitute_placeholders(request.dst_path, execution_results)

    return request


def extract_placeholder_variables(text: str) -> List[Tuple[str, str]]:
    """テキストからプレースホルダー変数を抽出（純粋関数）

    Args:
        text: 解析対象のテキスト

    Returns:
        (step_id, field_name)のタプルリスト
    """
    if not isinstance(text, str):
        return []

    variables = []

    # {{step_X.result.Y}}形式のパターン
    pattern1 = r'\{\{step_(\w+)\.result\.(\w+)\}\}'
    for match in re.finditer(pattern1, text):
        step_id = match.group(1)
        field_name = match.group(2)
        variables.append((step_id, field_name))

    # {{step_X.Y}}形式のパターン
    pattern2 = r'\{\{step_(\w+)\.(\w+)\}\}'
    for match in re.finditer(pattern2, text):
        step_id = match.group(1)
        field_name = match.group(2)
        # result.Y形式と重複しないようにチェック
        if (step_id, field_name) not in variables:
            variables.append((step_id, field_name))

    return variables


def validate_placeholders(text: str, available_results: Dict[str, Any]) -> List[str]:
    """プレースホルダーの妥当性を検証（純粋関数）

    Args:
        text: 検証対象のテキスト
        available_results: 利用可能な実行結果辞書

    Returns:
        エラーメッセージリスト
    """
    errors = []
    variables = extract_placeholder_variables(text)

    for step_id, field_name in variables:
        # ステップIDが存在するかチェック
        if step_id not in available_results:
            errors.append(f"Unknown step_id in placeholder: step_{step_id}")
            continue

        # フィールドが存在するかチェック
        result = available_results[step_id]
        if not hasattr(result, field_name):
            errors.append(f"Unknown field in placeholder: step_{step_id}.{field_name}")

    return errors


def find_missing_dependencies(text: str, completed_steps: set[str]) -> List[str]:
    """プレースホルダーで参照されているが未完了のステップを検出（純粋関数）

    Args:
        text: 解析対象のテキスト
        completed_steps: 完了済みステップID集合

    Returns:
        未完了ステップIDリスト
    """
    variables = extract_placeholder_variables(text)
    referenced_steps = {step_id for step_id, _ in variables}
    missing_steps = referenced_steps - completed_steps
    return list(missing_steps)


def substitute_with_defaults(text: str, execution_results: Dict[str, Any],
                           defaults: Dict[str, str]) -> str:
    """デフォルト値を使用してプレースホルダーを置換（純粋関数）

    Args:
        text: 置換対象のテキスト
        execution_results: 実行結果辞書
        defaults: デフォルト値辞書（key: "step_id.field_name", value: default_value）

    Returns:
        置換済みのテキスト
    """
    if not isinstance(text, str):
        return text

    # {{step_X.result.Y}}形式のパターン
    pattern1 = r'\{\{step_(\w+)\.result\.(\w+)\}\}'
    # {{step_X.Y}}形式のパターン
    pattern2 = r'\{\{step_(\w+)\.(\w+)\}\}'

    def replacer(match):
        step_id = match.group(1)
        field_name = match.group(2)

        # 実行結果から値を取得を試行
        if step_id in execution_results:
            result = execution_results[step_id]
            if hasattr(result, field_name):
                value = getattr(result, field_name)
                if value is not None:
                    return str(value)

        # デフォルト値を使用
        default_key = f"{step_id}.{field_name}"
        if default_key in defaults:
            return defaults[default_key]

        # デフォルト値もない場合は元のまま
        return match.group(0)

    # 両方のパターンを置換
    text = re.sub(pattern1, replacer, text)
    text = re.sub(pattern2, replacer, text)

    return text


def create_substitution_preview(text: str, execution_results: Dict[str, Any]) -> Dict[str, Any]:
    """置換プレビューを作成（純粋関数）

    Args:
        text: 置換対象のテキスト
        execution_results: 実行結果辞書

    Returns:
        置換プレビュー情報
    """
    variables = extract_placeholder_variables(text)
    substitutions = []

    for step_id, field_name in variables:
        placeholder = f"{{{{step_{step_id}.{field_name}}}}}"

        if step_id in execution_results:
            result = execution_results[step_id]
            if hasattr(result, field_name):
                value = getattr(result, field_name)
                substitutions.append({
                    'placeholder': placeholder,
                    'value': str(value) if value is not None else 'None',
                    'status': 'available'
                })
            else:
                substitutions.append({
                    'placeholder': placeholder,
                    'value': None,
                    'status': 'field_not_found'
                })
        else:
            substitutions.append({
                'placeholder': placeholder,
                'value': None,
                'status': 'step_not_found'
            })

    return {
        'original_text': text,
        'substituted_text': substitute_placeholders(text, execution_results),
        'substitutions': substitutions,
        'total_placeholders': len(variables)
    }


def batch_substitute_requests(requests: List[Any], execution_results: Dict[str, Any]) -> List[Any]:
    """複数のリクエストに一括で置換を適用（純粋関数風）

    Args:
        requests: リクエストリスト
        execution_results: 実行結果辞書

    Returns:
        置換済みリクエストリスト（元のリストは変更される）
    """
    for i, request in enumerate(requests):
        node_id = f"step_{i}"  # デフォルトのノードID
        apply_substitution_to_request(request, execution_results, node_id)

    return requests


def get_substitution_dependencies(text: str) -> Dict[str, List[str]]:
    """プレースホルダーから依存関係を抽出（純粋関数）

    Args:
        text: 解析対象のテキスト

    Returns:
        ステップID -> 参照フィールドリストの辞書
    """
    variables = extract_placeholder_variables(text)
    dependencies = {}

    for step_id, field_name in variables:
        if step_id not in dependencies:
            dependencies[step_id] = []
        if field_name not in dependencies[step_id]:
            dependencies[step_id].append(field_name)

    return dependencies
