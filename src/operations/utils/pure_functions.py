"""
純粋関数ユーティリティモジュール

副作用がなく、同一入力に対して常に同一出力を返す純粋関数を集約。
関数型プログラミングの原則に従い、テスタビリティと再利用性を向上させる。
"""
from typing import Dict, List, Optional, Tuple, Any, Union
from functools import reduce
import re
from pathlib import Path


# =============================================================================
# 文字列・パス操作の純粋関数
# =============================================================================

def format_string_pure(value: str, context_dict: Dict[str, str]) -> str:
    """
    文字列フォーマットの純粋関数版
    
    Args:
        value: フォーマットする文字列
        context_dict: フォーマット用の変数辞書
        
    Returns:
        フォーマット済みの文字列
    """
    if not isinstance(value, str):
        return value
    
    result = value
    for key, val in context_dict.items():
        result = result.replace(f"{{{key}}}", str(val))
    return result


def extract_missing_keys_pure(template: str, available_keys: set) -> List[str]:
    """
    テンプレート文字列から未解決のキーを抽出する純粋関数
    
    Args:
        template: テンプレート文字列（{key}形式）
        available_keys: 利用可能なキーのセット
        
    Returns:
        未解決のキーのリスト
    """
    import re
    pattern = r'\{([^}]+)\}'
    found_keys = re.findall(pattern, template)
    return [key for key in found_keys if key not in available_keys]


def is_potential_script_path_pure(code_or_file: List[str], script_extensions: List[str] = None) -> bool:
    """
    入力がスクリプトファイルパスらしいかを判定する純粋関数
    
    Args:
        code_or_file: 入力リスト
        script_extensions: スクリプトファイルの拡張子リスト
        
    Returns:
        スクリプトファイルパスらしいかのブール値
    """
    if script_extensions is None:
        script_extensions = ['.py', '.js', '.sh', '.rb', '.go']
    
    return (len(code_or_file) == 1 and 
            any(code_or_file[0].endswith(ext) for ext in script_extensions))


def validate_file_path_format_pure(path: str) -> Tuple[bool, Optional[str]]:
    """
    ファイルパス形式の検証純粋関数
    
    Args:
        path: 検証するパス
        
    Returns:
        (有効かどうか, エラーメッセージ)のタプル
    """
    import os
    
    if not path:
        return False, "Path cannot be empty"
    
    # パスを正規化してトラバーサル攻撃を検出
    normalized = os.path.normpath(path)
    
    # 正規化されたパスが親ディレクトリへの参照を含むか確認
    if normalized.startswith('..') or '/..' in normalized:
        return False, "Path traversal detected"
    
    # 絶対パスで'..'を含む場合も拒否
    if os.path.isabs(path) and '..' in path:
        return False, "Absolute paths with '..' are not allowed"
    
    # 危険な文字のチェック（拡張版）
    dangerous_chars = ['|', ';', '&', '$', '`', '\n', '\r', '\0']
    if any(char in path for char in dangerous_chars):
        return False, f"Path contains dangerous characters"
    
    return True, None


# =============================================================================
# Docker関連の純粋関数
# =============================================================================

def build_docker_run_command_pure(image: str, name: Optional[str] = None, 
                                 options: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    docker runコマンドを構築する純粋関数
    
    Args:
        image: Dockerイメージ名
        name: コンテナ名
        options: 追加オプション
        
    Returns:
        構築されたコマンドリスト
    """
    cmd = ["docker", "run", "-d"]
    
    if name:
        cmd.extend(["--name", name])
    
    if options:
        for key, value in options.items():
            if len(key) == 1:
                cmd.append(f"-{key}")
            else:
                cmd.append(f"--{key.replace('_', '-')}")
            
            if value is not None and value != "":
                cmd.append(str(value))
    
    cmd.extend([image, "tail", "-f", "/dev/null"])
    return cmd


def build_docker_build_command_pure(tag: Optional[str] = None, 
                                   dockerfile_content: Optional[str] = None,
                                   options: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    docker buildコマンドを構築する純粋関数
    
    Args:
        tag: イメージタグ
        dockerfile_content: Dockerfileの内容
        options: 追加オプション
        
    Returns:
        構築されたコマンドリスト
    """
    cmd = ["docker", "build", "-f", "-"]
    
    if tag:
        cmd.extend(["-t", tag])
    
    if options:
        for key, value in options.items():
            if key in ("f", "t"):  # 既に処理済みのオプションをスキップ
                continue
            
            if len(key) == 1:
                cmd.append(f"-{key}")
            else:
                cmd.append(f"--{key.replace('_', '-')}")
            
            if value is not None:
                cmd.append(str(value))
    
    cmd.append('.')
    return cmd


def validate_docker_image_name_pure(image_name: str) -> Tuple[bool, Optional[str]]:
    """
    Dockerイメージ名の形式を検証する純粋関数
    
    Args:
        image_name: 検証するイメージ名
        
    Returns:
        (有効かどうか, エラーメッセージ)のタプル
    """
    if not image_name:
        return False, "Image name cannot be empty"
    
    # Docker image name format validation
    pattern = r'^[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*(?::[a-zA-Z0-9._-]+)?$'
    if not re.match(pattern, image_name.lower()):
        return False, f"Invalid image name format: {image_name}"
    
    return True, None


def parse_container_names_pure(docker_ps_output: str) -> List[str]:
    """
    docker psの出力からコンテナ名を抽出する純粋関数
    
    Args:
        docker_ps_output: docker psコマンドの出力
        
    Returns:
        コンテナ名のリスト
    """
    if not docker_ps_output or not docker_ps_output.strip():
        return []
    
    return [line.strip() for line in docker_ps_output.strip().split("\n") if line.strip()]


def build_docker_stop_command_pure(container_name: str) -> List[str]:
    """
    docker stopコマンドを構築する純粋関数
    
    Args:
        container_name: 停止するコンテナ名
        
    Returns:
        構築されたコマンドリスト
    """
    return ["docker", "stop", container_name]


def build_docker_remove_command_pure(container_name: str, force: bool = False) -> List[str]:
    """
    docker rmコマンドを構築する純粋関数
    
    Args:
        container_name: 削除するコンテナ名
        force: 強制削除フラグ
        
    Returns:
        構築されたコマンドリスト
    """
    cmd = ["docker", "rm"]
    if force:
        cmd.append("-f")
    cmd.append(container_name)
    return cmd


def build_docker_ps_command_pure(all_containers: bool = False, names_only: bool = False) -> List[str]:
    """
    docker psコマンドを構築する純粋関数
    
    Args:
        all_containers: 全コンテナを表示するかどうか
        names_only: 名前のみを表示するかどうか
        
    Returns:
        構築されたコマンドリスト
    """
    cmd = ["docker", "ps"]
    if all_containers:
        cmd.append("-a")
    if names_only:
        cmd.extend(["--format", "{{.Names}}"])
    return cmd


def build_docker_inspect_command_pure(target: str, type_: Optional[str] = None) -> List[str]:
    """
    docker inspectコマンドを構築する純粋関数
    
    Args:
        target: 検査対象
        type_: 検査タイプ
        
    Returns:
        構築されたコマンドリスト
    """
    cmd = ["docker", "inspect"]
    if type_:
        cmd.extend(["--type", type_])
    cmd.append(target)
    return cmd


def build_docker_cp_command_pure(src: str, dst: str, container: str, to_container: bool = True) -> List[str]:
    """
    docker cpコマンドを構築する純粋関数
    
    Args:
        src: ソースパス
        dst: デスティネーションパス
        container: コンテナ名
        to_container: コンテナにファイルをコピーするかどうか
        
    Returns:
        構築されたコマンドリスト
    """
    cmd = ["docker", "cp"]
    if to_container:
        cmd.extend([src, f"{container}:{dst}"])
    else:
        cmd.extend([f"{container}:{src}", dst])
    return cmd


# =============================================================================
# 設定・検証の純粋関数
# =============================================================================

def format_value_with_config_pure(value: Any, node_value: Any, initial_values: Dict[str, str]) -> Any:
    """
    設定ノードを使って値をフォーマットする純粋関数
    状態変更を行わずに一時的なノード値でフォーマットを実行
    
    Args:
        value: フォーマットする値
        node_value: ノードの値（一時的に使用）
        initial_values: 初期値辞書
        
    Returns:
        フォーマット済みの値
    """
    if not isinstance(value, str):
        return value
    
    # 文字列の場合のみフォーマット処理を実行
    # ここでは単純な置換を行う（config_resolverの複雑なロジックは使用しない）
    result = value
    for key, val in initial_values.items():
        result = result.replace(f"{{{key}}}", str(val))
    
    return result


# =============================================================================
# 設定・検証の純粋関数
# =============================================================================

def validate_step_configuration_pure(step_dict: dict) -> Tuple[bool, List[str]]:
    """
    ステップ設定を検証する純粋関数
    
    Args:
        step_dict: ステップ設定辞書
        
    Returns:
        (有効かどうか, エラーメッセージリスト)のタプル
    """
    errors = []
    required_fields = ['type', 'cmd']
    valid_types = ['shell', 'python', 'copy', 'move', 'mkdir', 'rmtree', 'remove', 'touch']
    
    for field in required_fields:
        if field not in step_dict:
            errors.append(f"Missing required field: {field}")
    
    if 'type' in step_dict and step_dict['type'] not in valid_types:
        errors.append(f"Invalid step type: {step_dict['type']}. Valid types: {valid_types}")
    
    if 'cmd' in step_dict and not step_dict['cmd']:
        errors.append("Command field cannot be empty")
    
    return len(errors) == 0, errors


def merge_configurations_pure(configs: List[dict]) -> dict:
    """
    複数の設定辞書をマージする純粋関数
    
    Args:
        configs: マージする設定辞書のリスト
        
    Returns:
        マージ済みの設定辞書
    """
    def merge_two_dicts(dict1: dict, dict2: dict) -> dict:
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_two_dicts(result[key], value)
            else:
                result[key] = value
        return result
    
    return reduce(merge_two_dicts, configs, {})


# =============================================================================
# 時間・計算の純粋関数
# =============================================================================

def calculate_duration_seconds_pure(start_time: float, end_time: float) -> float:
    """
    期間を秒で計算する純粋関数
    
    Args:
        start_time: 開始時刻
        end_time: 終了時刻
        
    Returns:
        期間（秒）
    """
    return max(0.0, end_time - start_time)


def format_duration_human_readable_pure(duration_seconds: float) -> str:
    """
    期間を人間が読みやすい形式でフォーマットする純粋関数
    
    Args:
        duration_seconds: 期間（秒）
        
    Returns:
        フォーマット済みの期間文字列
    """
    if duration_seconds < 0:
        return "0s"
    elif duration_seconds < 1:
        return f"{duration_seconds*1000:.1f}ms"
    elif duration_seconds < 60:
        return f"{duration_seconds:.1f}s"
    else:
        minutes = int(duration_seconds // 60)
        seconds = duration_seconds % 60
        return f"{minutes}m{seconds:.1f}s"


def calculate_success_rate_pure(success_count: int, total_count: int) -> float:
    """
    成功率を計算する純粋関数
    
    Args:
        success_count: 成功数
        total_count: 総数
        
    Returns:
        成功率（0.0-1.0）
    """
    if total_count <= 0:
        return 0.0
    return min(1.0, max(0.0, success_count / total_count))


# =============================================================================
# データ変換の純粋関数
# =============================================================================

def flatten_nested_lists_pure(nested_lists: List[List[Any]]) -> List[Any]:
    """
    ネストしたリストを平坦化する純粋関数
    
    Args:
        nested_lists: ネストしたリスト
        
    Returns:
        平坦化されたリスト
    """
    result = []
    for item in nested_lists:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result


def group_by_key_pure(items: List[dict], key: str) -> Dict[str, List[dict]]:
    """
    辞書のリストを指定キーでグループ化する純粋関数
    
    Args:
        items: 辞書のリスト
        key: グループ化のキー
        
    Returns:
        グループ化された辞書
    """
    groups = {}
    for item in items:
        group_key = item.get(key, 'unknown')
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(item)
    return groups


def filter_by_criteria_pure(items: List[dict], criteria: Dict[str, Any]) -> List[dict]:
    """
    条件に基づいてアイテムをフィルタリングする純粋関数
    
    Args:
        items: フィルタリング対象のアイテムリスト
        criteria: フィルタリング条件の辞書
        
    Returns:
        フィルタリングされたアイテムリスト
    """
    def matches_criteria(item: dict) -> bool:
        for key, expected_value in criteria.items():
            if key not in item:
                return False
            if item[key] != expected_value:
                return False
        return True
    
    return [item for item in items if matches_criteria(item)]


# =============================================================================
# 関数合成ユーティリティ
# =============================================================================

def compose(*functions):
    """
    複数の関数を合成して単一の関数にする
    
    Args:
        *functions: 合成する関数群
        
    Returns:
        合成された関数
    """
    return reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)


def pipe(initial_value, *functions):
    """
    初期値に対して関数を順次適用するパイプライン
    
    Args:
        initial_value: 初期値
        *functions: 適用する関数群
        
    Returns:
        最終的な処理結果
    """
    return reduce(lambda value, func: func(value), functions, initial_value)