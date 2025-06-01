"""
Step オブジェクトから純粋なリクエストデータ構造への変換を行う純粋関数群
env.jsonステップの再現に集中し、operations依存を排除
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from .step import Step, StepType


@dataclass
class PureStepRequest:
    """
    純粋なステップリクエストデータ構造
    env.jsonのstepを忠実に再現するためのシンプルなデータ表現
    """
    step_type: str  # ステップの種類（shell, python, file等）
    action: str  # 具体的なアクション（exec, mkdir, copy等）
    parameters: Dict[str, Any]  # パラメータ辞書
    allow_failure: bool = False
    show_output: bool = True
    original_cmd: List[str] = None  # 元のコマンド情報を保持
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式での表現を提供"""
        return {
            'step_type': self.step_type,
            'action': self.action,
            'parameters': self.parameters,
            'allow_failure': self.allow_failure,
            'show_output': self.show_output,
            'original_cmd': self.original_cmd
        }


@dataclass
class PureStepSequence:
    """
    純粋なステップシーケンス
    env.jsonのstepsを表現するためのデータ構造
    """
    steps: List[PureStepRequest]
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """ステップリストを辞書のリストとして返す"""
        return [step.to_dict() for step in self.steps]


def steps_to_pure_sequence(steps: List[Step]) -> PureStepSequence:
    """
    Stepリストを PureStepSequence に変換する純粋関数
    
    Args:
        steps: 変換対象のStepリスト
        
    Returns:
        PureStepSequence: 変換されたピュアステップシーケンス
    """
    pure_requests = []
    
    for step in steps:
        pure_request = step_to_pure_request(step)
        if pure_request:
            pure_requests.append(pure_request)
    
    return PureStepSequence(steps=pure_requests)


def step_to_pure_request(step: Step) -> Optional[PureStepRequest]:
    """
    単一の Step を PureStepRequest に変換する純粋関数
    
    Args:
        step: 変換対象のStep
        
    Returns:
        Optional[PureStepRequest]: 変換されたリクエスト、変換できない場合はNone
    """
    if step.type == StepType.SHELL:
        return create_shell_pure_request(step)
    
    elif step.type == StepType.PYTHON:
        return create_python_pure_request(step)
    
    elif step.type == StepType.COPY:
        return create_copy_pure_request(step)
    
    elif step.type == StepType.MOVE:
        return create_move_pure_request(step)
    
    elif step.type == StepType.MOVETREE:
        return create_movetree_pure_request(step)
    
    elif step.type == StepType.MKDIR:
        return create_mkdir_pure_request(step)
    
    elif step.type == StepType.TOUCH:
        return create_touch_pure_request(step)
    
    elif step.type == StepType.REMOVE:
        return create_remove_pure_request(step)
    
    elif step.type == StepType.RMTREE:
        return create_rmtree_pure_request(step)
    
    elif step.type == StepType.DOCKER_EXEC:
        return create_docker_exec_pure_request(step)
    
    elif step.type == StepType.DOCKER_CP:
        return create_docker_cp_pure_request(step)
    
    elif step.type == StepType.DOCKER_RUN:
        return create_docker_run_pure_request(step)
    
    elif step.type in [StepType.OJ, StepType.TEST, StepType.BUILD, StepType.RESULT]:
        # これらは特殊なコマンドとして扱う
        return create_special_command_pure_request(step)
    
    return None


def create_shell_pure_request(step: Step) -> PureStepRequest:
    """
    Shell用のピュアリクエストを作成する純粋関数
    
    Args:
        step: Shell Step
        
    Returns:
        PureStepRequest: 作成されたシェルリクエスト
    """
    if not step.cmd:
        raise ValueError("Shell step must have non-empty cmd")
    
    return PureStepRequest(
        step_type="shell",
        action="exec",
        parameters={
            "cmd": step.cmd,
            "cwd": step.cwd,
            "command_string": ' '.join(step.cmd)
        },
        allow_failure=step.allow_failure,
        show_output=step.show_output,
        original_cmd=step.cmd.copy() if step.cmd else []
    )


def create_python_pure_request(step: Step) -> PureStepRequest:
    """
    Python用のピュアリクエストを作成する純粋関数
    
    Args:
        step: Python Step
        
    Returns:
        PureStepRequest: 作成されたPythonリクエスト
    """
    if not step.cmd:
        raise ValueError("Python step must have non-empty cmd")
    
    return PureStepRequest(
        step_type="python",
        action="exec",
        parameters={
            "code_or_file": step.cmd,
            "cwd": step.cwd
        },
        allow_failure=step.allow_failure,
        show_output=step.show_output,
        original_cmd=step.cmd.copy() if step.cmd else []
    )


def create_copy_pure_request(step: Step) -> PureStepRequest:
    """
    Copy用のピュアリクエストを作成する純粋関数
    
    Args:
        step: Copy Step
        
    Returns:
        PureStepRequest: 作成されたファイルリクエスト
    """
    if len(step.cmd) < 2:
        raise ValueError("Copy step requires at least 2 arguments (src, dst)")
    
    src = step.cmd[0]
    dst = step.cmd[1]
    
    return PureStepRequest(
        step_type="file",
        action="copy",
        parameters={
            "source_path": src,
            "destination_path": dst
        },
        allow_failure=step.allow_failure,
        show_output=step.show_output,
        original_cmd=step.cmd.copy() if step.cmd else []
    )


def create_move_pure_request(step: Step) -> PureStepRequest:
    """
    Move用のピュアリクエストを作成する純粋関数
    
    Args:
        step: Move Step
        
    Returns:
        PureStepRequest: 作成されたファイルリクエスト
    """
    if len(step.cmd) < 2:
        raise ValueError("Move step requires at least 2 arguments (src, dst)")
    
    src = step.cmd[0]
    dst = step.cmd[1]
    
    return PureStepRequest(
        step_type="file",
        action="move",
        parameters={
            "source_path": src,
            "destination_path": dst
        },
        allow_failure=step.allow_failure,
        show_output=step.show_output,
        original_cmd=step.cmd.copy() if step.cmd else []
    )


def create_movetree_pure_request(step: Step) -> PureStepRequest:
    """
    Movetree用のピュアリクエストを作成する純粋関数
    movetree は実際には copytree として実装される
    
    Args:
        step: Movetree Step
        
    Returns:
        PureStepRequest: 作成されたファイルリクエスト
    """
    if len(step.cmd) < 2:
        raise ValueError("Movetree step requires at least 2 arguments (src, dst)")
    
    src = step.cmd[0]
    dst = step.cmd[1]
    
    return PureStepRequest(
        step_type="file",
        action="copytree",
        parameters={
            "source_path": src,
            "destination_path": dst
        },
        allow_failure=step.allow_failure,
        show_output=step.show_output,
        original_cmd=step.cmd.copy() if step.cmd else []
    )


def create_mkdir_pure_request(step: Step) -> PureStepRequest:
    """
    Mkdir用のピュアリクエストを作成する純粋関数
    
    Args:
        step: Mkdir Step
        
    Returns:
        PureStepRequest: 作成されたファイルリクエスト
    """
    if len(step.cmd) < 1:
        raise ValueError("Mkdir step requires at least 1 argument (path)")
    
    path = step.cmd[0]
    
    return PureStepRequest(
        step_type="file",
        action="mkdir",
        parameters={
            "path": path
        },
        allow_failure=step.allow_failure,
        show_output=step.show_output,
        original_cmd=step.cmd.copy() if step.cmd else []
    )


def create_touch_pure_request(step: Step) -> PureStepRequest:
    """
    Touch用のピュアリクエストを作成する純粋関数
    
    Args:
        step: Touch Step
        
    Returns:
        PureStepRequest: 作成されたファイルリクエスト
    """
    if len(step.cmd) < 1:
        raise ValueError("Touch step requires at least 1 argument (path)")
    
    path = step.cmd[0]
    
    return PureStepRequest(
        step_type="file",
        action="touch",
        parameters={
            "path": path
        },
        allow_failure=step.allow_failure,
        show_output=step.show_output,
        original_cmd=step.cmd.copy() if step.cmd else []
    )


def create_remove_pure_request(step: Step) -> PureStepRequest:
    """
    Remove用のピュアリクエストを作成する純粋関数
    
    Args:
        step: Remove Step
        
    Returns:
        PureStepRequest: 作成されたファイルリクエスト
    """
    if len(step.cmd) < 1:
        raise ValueError("Remove step requires at least 1 argument (path)")
    
    path = step.cmd[0]
    
    return PureStepRequest(
        step_type="file",
        action="remove",
        parameters={
            "path": path
        },
        allow_failure=step.allow_failure,
        show_output=step.show_output,
        original_cmd=step.cmd.copy() if step.cmd else []
    )


def create_rmtree_pure_request(step: Step) -> PureStepRequest:
    """
    Rmtree用のピュアリクエストを作成する純粋関数
    
    Args:
        step: Rmtree Step
        
    Returns:
        PureStepRequest: 作成されたファイルリクエスト
    """
    if len(step.cmd) < 1:
        raise ValueError("Rmtree step requires at least 1 argument (path)")
    
    path = step.cmd[0]
    
    return PureStepRequest(
        step_type="file",
        action="rmtree",
        parameters={
            "path": path
        },
        allow_failure=step.allow_failure,
        show_output=step.show_output,
        original_cmd=step.cmd.copy() if step.cmd else []
    )


def create_docker_exec_pure_request(step: Step) -> PureStepRequest:
    """
    Docker exec用のピュアリクエストを作成する純粋関数
    
    Args:
        step: Docker exec Step
        
    Returns:
        PureStepRequest: 作成されたDockerリクエスト
    """
    if len(step.cmd) < 2:
        raise ValueError("Docker exec step requires at least 2 arguments (container, command)")
    
    container_name = step.cmd[0]
    command = ' '.join(step.cmd[1:])
    
    return PureStepRequest(
        step_type="docker",
        action="exec",
        parameters={
            "container": container_name,
            "command": command,
            "command_args": step.cmd[1:]
        },
        allow_failure=step.allow_failure,
        show_output=step.show_output,
        original_cmd=step.cmd.copy() if step.cmd else []
    )


def create_docker_cp_pure_request(step: Step) -> PureStepRequest:
    """
    Docker cp用のピュアリクエストを作成する純粋関数
    
    Args:
        step: Docker cp Step
        
    Returns:
        PureStepRequest: 作成されたDockerリクエスト
    """
    if len(step.cmd) < 2:
        raise ValueError("Docker cp step requires at least 2 arguments (src, dst)")
    
    src = step.cmd[0]
    dst = step.cmd[1]
    
    # Docker cp の方向を判定
    if ':' in src:
        # Copy FROM container
        container_name = src.split(':')[0]
        remote_path = src.split(':', 1)[1]
        local_path = dst
        to_container = False
    elif ':' in dst:
        # Copy TO container
        container_name = dst.split(':')[0]
        remote_path = dst.split(':', 1)[1]
        local_path = src
        to_container = True
    else:
        raise ValueError("Docker cp step requires container:path format in src or dst")
    
    return PureStepRequest(
        step_type="docker",
        action="cp",
        parameters={
            "container": container_name,
            "local_path": local_path,
            "remote_path": remote_path,
            "to_container": to_container,
            "source": src,
            "destination": dst
        },
        allow_failure=step.allow_failure,
        show_output=step.show_output,
        original_cmd=step.cmd.copy() if step.cmd else []
    )


def create_docker_run_pure_request(step: Step) -> PureStepRequest:
    """
    Docker run用のピュアリクエストを作成する純粋関数
    
    Args:
        step: Docker run Step
        
    Returns:
        PureStepRequest: 作成されたDockerリクエスト
    """
    if len(step.cmd) < 1:
        raise ValueError("Docker run step requires at least 1 argument (image)")
    
    image_name = step.cmd[0]
    
    # Additional options from step.cmd[1:]
    options = {}
    if len(step.cmd) > 1:
        # Parse additional run options
        for i in range(1, len(step.cmd), 2):
            if i + 1 < len(step.cmd):
                key = step.cmd[i].lstrip('-')  # Remove leading dashes
                value = step.cmd[i + 1]
                options[key] = value
    
    return PureStepRequest(
        step_type="docker",
        action="run",
        parameters={
            "image": image_name,
            "options": options,
            "run_args": step.cmd[1:] if len(step.cmd) > 1 else []
        },
        allow_failure=step.allow_failure,
        show_output=step.show_output,
        original_cmd=step.cmd.copy() if step.cmd else []
    )


def create_special_command_pure_request(step: Step) -> PureStepRequest:
    """
    特殊コマンド（OJ, TEST, BUILD, RESULT）用のピュアリクエストを作成する純粋関数
    
    Args:
        step: 特殊コマンドStep
        
    Returns:
        PureStepRequest: 作成された特殊コマンドリクエスト
    """
    if not step.cmd:
        raise ValueError("Special command step must have non-empty cmd")
    
    # ステップタイプを文字列に変換
    step_type_str = step.type.value.lower() if hasattr(step.type, 'value') else str(step.type).lower()
    
    return PureStepRequest(
        step_type="special",
        action=step_type_str,
        parameters={
            "cmd": step.cmd,
            "cwd": step.cwd,
            "command_string": ' '.join(step.cmd),
            "step_type_original": step_type_str
        },
        allow_failure=step.allow_failure,
        show_output=step.show_output,
        original_cmd=step.cmd.copy() if step.cmd else []
    )