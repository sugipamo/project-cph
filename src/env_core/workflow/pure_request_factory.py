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
from src.operations.docker.docker_request import DockerRequest, DockerOpType


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
            elif step.type == StepType.DOCKER_EXEC:
                return PureRequestFactory._create_docker_exec_request(step, context)
            elif step.type == StepType.DOCKER_CP:
                return PureRequestFactory._create_docker_cp_request(step, context)
            elif step.type == StepType.DOCKER_RUN:
                return PureRequestFactory._create_docker_run_request(step, context)
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
    
    @staticmethod
    def _create_docker_exec_request(step: Step, context) -> DockerRequest:
        """docker exec requestを生成"""
        if len(step.cmd) < 2:
            raise ValueError("docker_exec step requires container and command")
        
        container_name = step.cmd[0]
        command = ' '.join(step.cmd[1:])  # Join remaining arguments as command
        
        request = DockerRequest(
            op=DockerOpType.EXEC,
            container=container_name,
            command=command
        )
        request.allow_failure = step.allow_failure
        request.show_output = step.show_output
        return request
    
    @staticmethod
    def _create_docker_cp_request(step: Step, context) -> DockerRequest:
        """docker cp requestを生成"""
        if len(step.cmd) < 2:
            raise ValueError("docker_cp step requires source and destination")
        
        # Docker cp can be either:
        # - local_path container:remote_path (to container)
        # - container:remote_path local_path (from container)
        src = step.cmd[0]
        dst = step.cmd[1]
        
        # Determine direction and extract container name
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
            raise ValueError("docker_cp step requires container:path format in src or dst")
        
        # Use options to pass cp-specific parameters
        options = {
            'local_path': local_path,
            'remote_path': remote_path,
            'to_container': to_container
        }
        
        request = DockerRequest(
            op=DockerOpType.CP,
            container=container_name,
            options=options
        )
        request.allow_failure = step.allow_failure
        request.show_output = step.show_output
        return request
    
    @staticmethod
    def _create_docker_run_request(step: Step, context) -> DockerRequest:
        """docker run requestを生成"""
        if not step.cmd:
            raise ValueError("docker_run step requires image name")
        
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
        
        # Get container name from context if available
        container_name = None
        if context and hasattr(context, 'get_docker_names'):
            docker_names = context.get_docker_names()
            if 'ojtools' in image_name.lower():
                container_name = docker_names.get('oj_container_name')
            else:
                container_name = docker_names.get('container_name')
        
        request = DockerRequest(
            op=DockerOpType.RUN,
            image=image_name,
            container=container_name,
            options=options
        )
        request.allow_failure = step.allow_failure
        request.show_output = step.show_output
        return request