"""
Step オブジェクトからoperationsリクエストへの変換を行う純粋関数群
env.jsonステップからoperationsリクエストを直接生成
"""
from typing import List, Optional, Dict, Any
from src.operations.base_request import BaseRequest
from src.operations.file.file_request import FileRequest
from src.operations.file.file_op_type import FileOpType
from src.operations.shell.shell_request import ShellRequest
from src.operations.python.python_request import PythonRequest
from src.operations.composite.driver_bound_request import DriverBoundRequest
from src.operations.composite.composite_request import CompositeRequest
from .step import Step, StepType


def steps_to_requests(steps: List[Step], operations, context=None) -> CompositeRequest:
    """
    Stepリストを CompositeRequest に変換する純粋関数
    
    Args:
        steps: 変換対象のStepリスト
        operations: DIコンテナ（ドライバ取得用）
        context: 実行コンテキスト（OJ/TEST/BUILD等の特殊なステップ用）
        
    Returns:
        CompositeRequest: 変換されたコンポジットリクエスト
    """
    requests = []
    
    for step in steps:
        # OJ, TEST, BUILD ステップは PureRequestFactory を使用（遅延インポート）
        if step.type in [StepType.OJ, StepType.TEST, StepType.BUILD] and context:
            from src.env_core.workflow.pure_request_factory import PureRequestFactory
            request = PureRequestFactory.create_request_from_step(step, context)
        else:
            request = step_to_request(step)
            
        if request:
            # FileRequest の場合は DriverBoundRequest でラップ
            if isinstance(request, FileRequest):
                file_driver = operations.resolve('file_driver')
                request = DriverBoundRequest(request, file_driver)
            
            requests.append(request)
    
    return CompositeRequest.make_composite_request(requests)


def step_to_request(step: Step) -> Optional[BaseRequest]:
    """
    単一の Step を BaseRequest に変換する純粋関数
    
    Args:
        step: 変換対象のStep
        
    Returns:
        Optional[BaseRequest]: 変換されたリクエスト、変換できない場合はNone
    """
    if step.type == StepType.SHELL:
        return create_shell_request(step)
    
    elif step.type == StepType.PYTHON:
        return create_python_request(step)
    
    elif step.type == StepType.COPY:
        return create_copy_request(step)
    
    elif step.type == StepType.MOVE:
        return create_move_request(step)
    
    elif step.type == StepType.MOVETREE:
        return create_movetree_request(step)
    
    elif step.type == StepType.MKDIR:
        return create_mkdir_request(step)
    
    elif step.type == StepType.TOUCH:
        return create_touch_request(step)
    
    elif step.type == StepType.REMOVE:
        return create_remove_request(step)
    
    elif step.type == StepType.RMTREE:
        return create_rmtree_request(step)
    
    elif step.type in [StepType.OJ, StepType.TEST, StepType.BUILD]:
        # これらは特殊なシェルコマンドとして扱う
        return create_shell_request(step)
    
    return None


def create_shell_request(step: Step) -> ShellRequest:
    """
    Shell用のリクエストを作成する純粋関数
    
    Args:
        step: Shell Step
        
    Returns:
        ShellRequest: 作成されたシェルリクエスト
    """
    if not step.cmd:
        raise ValueError("Shell step must have non-empty cmd")
    
    # cmdリストを文字列に結合
    command = ' '.join(step.cmd)
    
    request = ShellRequest(command, cwd=step.cwd, show_output=step.show_output)
    request.allow_failure = step.allow_failure
    
    return request


def create_python_request(step: Step) -> PythonRequest:
    """
    Python用のリクエストを作成する純粋関数
    
    Args:
        step: Python Step
        
    Returns:
        PythonRequest: 作成されたPythonリクエスト
    """
    if not step.cmd:
        raise ValueError("Python step must have non-empty cmd")
    
    # PythonRequestはcode_or_fileとしてリストを受け取る
    code_or_file = step.cmd
    
    request = PythonRequest(code_or_file, cwd=step.cwd, show_output=step.show_output)
    request.allow_failure = step.allow_failure
    
    return request


def create_copy_request(step: Step) -> FileRequest:
    """
    Copy用のFileRequestを作成する純粋関数
    
    Args:
        step: Copy Step
        
    Returns:
        FileRequest: 作成されたファイルリクエスト
    """
    if len(step.cmd) < 2:
        raise ValueError("Copy step requires at least 2 arguments (src, dst)")
    
    src = step.cmd[0]
    dst = step.cmd[1]
    
    request = FileRequest(FileOpType.COPY, src, dst_path=dst)
    request.allow_failure = step.allow_failure
    request.show_output = step.show_output
    
    return request


def create_move_request(step: Step) -> FileRequest:
    """
    Move用のFileRequestを作成する純粋関数
    
    Args:
        step: Move Step
        
    Returns:
        FileRequest: 作成されたファイルリクエスト
    """
    if len(step.cmd) < 2:
        raise ValueError("Move step requires at least 2 arguments (src, dst)")
    
    src = step.cmd[0]
    dst = step.cmd[1]
    
    request = FileRequest(FileOpType.MOVE, src, dst_path=dst)
    request.allow_failure = step.allow_failure
    request.show_output = step.show_output
    
    return request


def create_movetree_request(step: Step) -> FileRequest:
    """
    Movetree用のFileRequestを作成する純粋関数
    movetree は実際には copytree として実装される
    
    Args:
        step: Movetree Step
        
    Returns:
        FileRequest: 作成されたファイルリクエスト
    """
    if len(step.cmd) < 2:
        raise ValueError("Movetree step requires at least 2 arguments (src, dst)")
    
    src = step.cmd[0]
    dst = step.cmd[1]
    
    # MOVETREEは実際にはCOPYTREEとして実装される
    request = FileRequest(FileOpType.COPYTREE, src, dst_path=dst)
    request.allow_failure = step.allow_failure
    request.show_output = step.show_output
    
    return request


def create_mkdir_request(step: Step) -> FileRequest:
    """
    Mkdir用のFileRequestを作成する純粋関数
    
    Args:
        step: Mkdir Step
        
    Returns:
        FileRequest: 作成されたファイルリクエスト
    """
    if len(step.cmd) < 1:
        raise ValueError("Mkdir step requires at least 1 argument (path)")
    
    path = step.cmd[0]
    
    request = FileRequest(FileOpType.MKDIR, path)
    request.allow_failure = step.allow_failure
    request.show_output = step.show_output
    
    return request


def create_touch_request(step: Step) -> FileRequest:
    """
    Touch用のFileRequestを作成する純粋関数
    
    Args:
        step: Touch Step
        
    Returns:
        FileRequest: 作成されたファイルリクエスト
    """
    if len(step.cmd) < 1:
        raise ValueError("Touch step requires at least 1 argument (path)")
    
    path = step.cmd[0]
    
    request = FileRequest(FileOpType.TOUCH, path)
    request.allow_failure = step.allow_failure
    request.show_output = step.show_output
    
    return request


def create_remove_request(step: Step) -> FileRequest:
    """
    Remove用のFileRequestを作成する純粋関数
    
    Args:
        step: Remove Step
        
    Returns:
        FileRequest: 作成されたファイルリクエスト
    """
    if len(step.cmd) < 1:
        raise ValueError("Remove step requires at least 1 argument (path)")
    
    path = step.cmd[0]
    
    request = FileRequest(FileOpType.REMOVE, path)
    request.allow_failure = step.allow_failure
    request.show_output = step.show_output
    
    return request


def create_rmtree_request(step: Step) -> FileRequest:
    """
    Rmtree用のFileRequestを作成する純粋関数
    
    Args:
        step: Rmtree Step
        
    Returns:
        FileRequest: 作成されたファイルリクエスト
    """
    if len(step.cmd) < 1:
        raise ValueError("Rmtree step requires at least 1 argument (path)")
    
    path = step.cmd[0]
    
    request = FileRequest(FileOpType.RMTREE, path)
    request.allow_failure = step.allow_failure
    request.show_output = step.show_output
    
    return request