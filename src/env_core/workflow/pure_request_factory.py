"""
純粋なRequest生成Factory

operationsに依存しない、ユーザー入力からRequestを生成する純粋関数的Factory
"""
from typing import Optional, Any
from src.env_core.step.step import Step, StepType
from src.operations.file.file_request import FileRequest
from src.operations.file.file_op_type import FileOpType
from src.operations.shell.shell_request import ShellRequest
from src.operations.python.python_request import PythonRequest


class PureRequestFactory:
    """
    純粋なRequest生成Factory
    
    operationsに依存せず、Step情報からRequestを直接生成
    """
    
    @staticmethod
    def create_request_from_step(step: Step, context=None) -> Optional[Any]:
        """
        StepからRequestを純粋に生成
        
        Args:
            step: 変換するStep
            context: フォーマット用のコンテキスト（オプション）
            
        Returns:
            生成されたRequest、または None
        """
        try:
            if step.type == StepType.MKDIR:
                return PureRequestFactory._create_mkdir_request(step, context)
            elif step.type == StepType.TOUCH:
                return PureRequestFactory._create_touch_request(step, context)
            elif step.type == StepType.COPY:
                return PureRequestFactory._create_copy_request(step, context)
            elif step.type == StepType.MOVE:
                return PureRequestFactory._create_move_request(step, context)
            elif step.type == StepType.REMOVE:
                return PureRequestFactory._create_remove_request(step, context)
            elif step.type == StepType.RMTREE:
                return PureRequestFactory._create_rmtree_request(step, context)
            elif step.type == StepType.SHELL:
                return PureRequestFactory._create_shell_request(step, context)
            elif step.type == StepType.PYTHON:
                return PureRequestFactory._create_python_request(step, context)
            else:
                # 未知のステップタイプ
                return None
        except Exception:
            # 生成エラーの場合はNoneを返す
            return None
    
    @staticmethod
    def _create_mkdir_request(step: Step, context) -> FileRequest:
        """mkdir requestを生成"""
        if not step.cmd:
            raise ValueError("mkdir step requires target path in cmd")
        target_path = step.cmd[0]
        request = FileRequest(op=FileOpType.MKDIR, path=target_path)
        request.allow_failure = step.allow_failure
        return request
    
    @staticmethod
    def _create_touch_request(step: Step, context) -> FileRequest:
        """touch requestを生成"""
        if not step.cmd:
            raise ValueError("touch step requires target path in cmd")
        target_path = step.cmd[0]
        request = FileRequest(op=FileOpType.TOUCH, path=target_path)
        request.allow_failure = step.allow_failure
        return request
    
    @staticmethod
    def _create_copy_request(step: Step, context) -> FileRequest:
        """copy requestを生成"""
        if len(step.cmd) < 2:
            raise ValueError("copy step requires source and destination paths")
        source_path = step.cmd[0]
        dest_path = step.cmd[1]
        request = FileRequest(op=FileOpType.COPY, path=source_path, dst_path=dest_path)
        request.allow_failure = step.allow_failure
        return request
    
    @staticmethod
    def _create_move_request(step: Step, context) -> FileRequest:
        """move requestを生成"""
        if len(step.cmd) < 2:
            raise ValueError("move step requires source and destination paths")
        source_path = step.cmd[0]
        dest_path = step.cmd[1]
        request = FileRequest(op=FileOpType.MOVE, path=source_path, dst_path=dest_path)
        request.allow_failure = step.allow_failure
        return request
    
    @staticmethod
    def _create_remove_request(step: Step, context) -> FileRequest:
        """remove requestを生成"""
        if not step.cmd:
            raise ValueError("remove step requires target path in cmd")
        target_path = step.cmd[0]
        request = FileRequest(op=FileOpType.REMOVE, path=target_path)
        request.allow_failure = step.allow_failure
        return request
    
    @staticmethod
    def _create_rmtree_request(step: Step, context) -> FileRequest:
        """rmtree requestを生成"""
        if not step.cmd:
            raise ValueError("rmtree step requires target path in cmd")
        target_path = step.cmd[0]
        request = FileRequest(op=FileOpType.RMTREE, path=target_path)
        request.allow_failure = step.allow_failure
        return request
    
    @staticmethod
    def _create_shell_request(step: Step, context) -> ShellRequest:
        """shell requestを生成"""
        if not step.cmd:
            raise ValueError("shell step requires command")
        request = ShellRequest(cmd=step.cmd, cwd=step.cwd, show_output=step.show_output)
        request.allow_failure = step.allow_failure
        return request
    
    @staticmethod
    def _create_python_request(step: Step, context) -> PythonRequest:
        """python requestを生成"""
        if not step.cmd:
            raise ValueError("python step requires code")
        
        # Python codeの結合
        python_code = '\n'.join(step.cmd)
        
        request = PythonRequest(code_or_file=python_code, cwd=step.cwd, show_output=step.show_output)
        request.allow_failure = step.allow_failure
        return request