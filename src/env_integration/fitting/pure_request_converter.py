"""
純粋なリクエストデータ構造をoperationsリクエストに変換するコンバーター
env.jsonステップの実行時の状況に応じてリクエストを適切に変換する
"""
from typing import List, Optional, Any, Dict
import logging

from src.env_core.step.request_converter import PureStepRequest, PureStepSequence
from src.env_core.workflow.pure_request_factory import PureRequest
from src.operations.base_request import BaseRequest
from src.operations.file.file_request import FileRequest
from src.operations.file.file_op_type import FileOpType
from src.operations.shell.shell_request import ShellRequest
from src.operations.python.python_request import PythonRequest
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.operations.composite.driver_bound_request import DriverBoundRequest
from src.operations.composite.composite_request import CompositeRequest
from src.context.execution_context import ExecutionContext


class PureRequestConverter:
    """
    純粋なリクエストをoperationsリクエストに変換するコンバーター
    現在の環境状態（Docker状態等）を考慮して適切なリクエストを生成
    """
    
    def __init__(self, operations, context: ExecutionContext):
        """
        Args:
            operations: Operations container for driver access
            context: Execution context with current environment state
        """
        self.operations = operations
        self.context = context
        self.logger = logging.getLogger(__name__)
    
    def convert_pure_requests_to_operations(self, pure_requests: List[PureRequest]) -> CompositeRequest:
        """
        PureRequestのリストをoperationsリクエストに変換
        
        Args:
            pure_requests: 純粋なリクエストのリスト
            
        Returns:
            CompositeRequest: 変換されたコンポジットリクエスト
        """
        operations_requests = []
        
        for pure_request in pure_requests:
            op_request = self._convert_single_pure_request(pure_request)
            if op_request:
                # DriverBoundRequestでラップが必要なものは対応
                if isinstance(op_request, FileRequest):
                    file_driver = self.operations.resolve('file_driver')
                    op_request = DriverBoundRequest(op_request, file_driver)
                
                operations_requests.append(op_request)
        
        return CompositeRequest.make_composite_request(operations_requests)
    
    def convert_pure_step_sequence_to_operations(self, step_sequence: PureStepSequence) -> CompositeRequest:
        """
        PureStepSequenceをoperationsリクエストに変換
        
        Args:
            step_sequence: 純粋なステップシーケンス
            
        Returns:
            CompositeRequest: 変換されたコンポジットリクエスト
        """
        operations_requests = []
        
        for pure_step in step_sequence.steps:
            op_request = self._convert_single_pure_step_request(pure_step)
            if op_request:
                # DriverBoundRequestでラップが必要なものは対応
                if isinstance(op_request, FileRequest):
                    file_driver = self.operations.resolve('file_driver')
                    op_request = DriverBoundRequest(op_request, file_driver)
                
                operations_requests.append(op_request)
        
        return CompositeRequest.make_composite_request(operations_requests)
    
    def _convert_single_pure_request(self, pure_request: PureRequest) -> Optional[BaseRequest]:
        """
        単一のPureRequestをoperationsリクエストに変換
        
        Args:
            pure_request: 変換する純粋リクエスト
            
        Returns:
            BaseRequest: 変換されたoperationsリクエスト
        """
        try:
            if pure_request.type == "file":
                return self._convert_file_request(pure_request)
            elif pure_request.type == "shell":
                return self._convert_shell_request(pure_request)
            elif pure_request.type == "python":
                return self._convert_python_request(pure_request)
            elif pure_request.type == "docker":
                return self._convert_docker_request(pure_request)
            else:
                self.logger.warning(f"Unknown pure request type: {pure_request.type}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to convert pure request {pure_request.type}: {str(e)}")
            return None
    
    def _convert_single_pure_step_request(self, pure_step: PureStepRequest) -> Optional[BaseRequest]:
        """
        単一のPureStepRequestをoperationsリクエストに変換
        
        Args:
            pure_step: 変換する純粋ステップリクエスト
            
        Returns:
            BaseRequest: 変換されたoperationsリクエスト
        """
        try:
            if pure_step.step_type == "file":
                return self._convert_file_step_request(pure_step)
            elif pure_step.step_type == "shell":
                return self._convert_shell_step_request(pure_step)
            elif pure_step.step_type == "python":
                return self._convert_python_step_request(pure_step)
            elif pure_step.step_type == "docker":
                return self._convert_docker_step_request(pure_step)
            elif pure_step.step_type == "special":
                return self._convert_special_step_request(pure_step)
            else:
                self.logger.warning(f"Unknown pure step type: {pure_step.step_type}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to convert pure step {pure_step.step_type}: {str(e)}")
            return None
    
    def _convert_file_request(self, pure_request: PureRequest) -> FileRequest:
        """ファイル操作リクエストの変換"""
        params = pure_request.params
        
        if pure_request.operation == "mkdir":
            request = FileRequest(op=FileOpType.MKDIR, path=params["path"])
        elif pure_request.operation == "touch":
            request = FileRequest(op=FileOpType.TOUCH, path=params["path"])
        elif pure_request.operation == "copy":
            request = FileRequest(op=FileOpType.COPY, path=params["path"], dst_path=params["dst_path"])
        elif pure_request.operation == "move":
            request = FileRequest(op=FileOpType.MOVE, path=params["path"], dst_path=params["dst_path"])
        elif pure_request.operation == "copytree":
            request = FileRequest(op=FileOpType.COPYTREE, path=params["path"], dst_path=params["dst_path"])
        elif pure_request.operation == "remove":
            request = FileRequest(op=FileOpType.REMOVE, path=params["path"])
        elif pure_request.operation == "rmtree":
            request = FileRequest(op=FileOpType.RMTREE, path=params["path"])
        else:
            raise ValueError(f"Unknown file operation: {pure_request.operation}")
        
        request.allow_failure = pure_request.allow_failure
        request.show_output = pure_request.show_output
        return request
    
    def _convert_file_step_request(self, pure_step: PureStepRequest) -> FileRequest:
        """ファイル操作ステップリクエストの変換"""
        params = pure_step.parameters
        
        if pure_step.action == "mkdir":
            request = FileRequest(op=FileOpType.MKDIR, path=params["path"])
        elif pure_step.action == "touch":
            request = FileRequest(op=FileOpType.TOUCH, path=params["path"])
        elif pure_step.action == "copy":
            request = FileRequest(op=FileOpType.COPY, 
                                path=params["source_path"], 
                                dst_path=params["destination_path"])
        elif pure_step.action == "move":
            request = FileRequest(op=FileOpType.MOVE, 
                                path=params["source_path"], 
                                dst_path=params["destination_path"])
        elif pure_step.action == "copytree":
            request = FileRequest(op=FileOpType.COPYTREE, 
                                path=params["source_path"], 
                                dst_path=params["destination_path"])
        elif pure_step.action == "remove":
            request = FileRequest(op=FileOpType.REMOVE, path=params["path"])
        elif pure_step.action == "rmtree":
            request = FileRequest(op=FileOpType.RMTREE, path=params["path"])
        else:
            raise ValueError(f"Unknown file action: {pure_step.action}")
        
        request.allow_failure = pure_step.allow_failure
        request.show_output = pure_step.show_output
        return request
    
    def _convert_shell_request(self, pure_request: PureRequest) -> ShellRequest:
        """シェルリクエストの変換"""
        params = pure_request.params
        
        request = ShellRequest(
            cmd=params["cmd"], 
            cwd=params.get("cwd"),
            show_output=pure_request.show_output
        )
        request.allow_failure = pure_request.allow_failure
        return request
    
    def _convert_shell_step_request(self, pure_step: PureStepRequest) -> ShellRequest:
        """シェルステップリクエストの変換"""
        params = pure_step.parameters
        
        request = ShellRequest(
            cmd=params["cmd"], 
            cwd=params.get("cwd"),
            show_output=pure_step.show_output
        )
        request.allow_failure = pure_step.allow_failure
        return request
    
    def _convert_python_request(self, pure_request: PureRequest) -> PythonRequest:
        """Pythonリクエストの変換"""
        params = pure_request.params
        
        request = PythonRequest(
            code_or_file=params["code_or_file"],
            cwd=params.get("cwd"),
            show_output=pure_request.show_output
        )
        request.allow_failure = pure_request.allow_failure
        return request
    
    def _convert_python_step_request(self, pure_step: PureStepRequest) -> PythonRequest:
        """Pythonステップリクエストの変換"""
        params = pure_step.parameters
        
        request = PythonRequest(
            code_or_file=params["code_or_file"],
            cwd=params.get("cwd"),
            show_output=pure_step.show_output
        )
        request.allow_failure = pure_step.allow_failure
        return request
    
    def _convert_docker_request(self, pure_request: PureRequest) -> DockerRequest:
        """Dockerリクエストの変換（環境状態を考慮）"""
        params = pure_request.params
        
        if pure_request.operation == "exec":
            # Docker exec: 現在の環境状態に応じてコンテナ名を解決
            container_name = self._resolve_container_name(params["container"])
            request = DockerRequest(
                op=DockerOpType.EXEC,
                container=container_name,
                command=params["command"]
            )
        elif pure_request.operation == "cp":
            # Docker cp: 現在の環境状態に応じてコンテナ名を解決
            container_name = self._resolve_container_name(params["container"])
            request = DockerRequest(
                op=DockerOpType.CP,
                container=container_name,
                options={
                    'local_path': params["local_path"],
                    'remote_path': params["remote_path"],
                    'to_container': params["to_container"]
                }
            )
        elif pure_request.operation == "run":
            # Docker run: 環境状態に応じてイメージ名とコンテナ名を解決
            image_name = self._resolve_image_name(params["image"])
            container_name = self._resolve_container_name(params.get("container"))
            request = DockerRequest(
                op=DockerOpType.RUN,
                image=image_name,
                container=container_name,
                options=params.get("options", {})
            )
        else:
            raise ValueError(f"Unknown docker operation: {pure_request.operation}")
        
        request.allow_failure = pure_request.allow_failure
        request.show_output = pure_request.show_output
        return request
    
    def _convert_docker_step_request(self, pure_step: PureStepRequest) -> DockerRequest:
        """Dockerステップリクエストの変換（環境状態を考慮）"""
        params = pure_step.parameters
        
        if pure_step.action == "exec":
            # Docker exec: 現在の環境状態に応じてコンテナ名を解決
            container_name = self._resolve_container_name(params["container"])
            request = DockerRequest(
                op=DockerOpType.EXEC,
                container=container_name,
                command=params["command"]
            )
        elif pure_step.action == "cp":
            # Docker cp: 現在の環境状態に応じてコンテナ名を解決
            container_name = self._resolve_container_name(params["container"])
            request = DockerRequest(
                op=DockerOpType.CP,
                container=container_name,
                options={
                    'local_path': params["local_path"],
                    'remote_path': params["remote_path"],
                    'to_container': params["to_container"]
                }
            )
        elif pure_step.action == "run":
            # Docker run: 環境状態に応じてイメージ名とコンテナ名を解決
            image_name = self._resolve_image_name(params["image"])
            container_name = self._resolve_container_name(params.get("container"))
            request = DockerRequest(
                op=DockerOpType.RUN,
                image=image_name,
                container=container_name,
                options=params.get("options", {})
            )
        else:
            raise ValueError(f"Unknown docker action: {pure_step.action}")
        
        request.allow_failure = pure_step.allow_failure
        request.show_output = pure_step.show_output
        return request
    
    def _convert_special_step_request(self, pure_step: PureStepRequest) -> ShellRequest:
        """特殊ステップリクエストの変換（OJ, TEST, BUILD, RESULT）"""
        params = pure_step.parameters
        
        # 特殊コマンドは基本的にシェルコマンドとして実行
        # 環境に応じて調整可能
        if hasattr(self.context, 'env_type') and self.context.env_type == 'docker':
            # Docker環境では特殊な処理が必要かもしれない
            # しかし今回はシンプルにShellRequestとして扱う
            pass
        
        request = ShellRequest(
            cmd=params["cmd"],
            cwd=params.get("cwd"),
            show_output=pure_step.show_output
        )
        request.allow_failure = pure_step.allow_failure
        return request
    
    def _resolve_container_name(self, container_name: Optional[str]) -> str:
        """
        コンテナ名を現在の環境状態に応じて解決
        
        Args:
            container_name: 元のコンテナ名
            
        Returns:
            str: 解決されたコンテナ名
        """
        if not container_name:
            # デフォルトコンテナ名を使用
            if hasattr(self.context, 'get_docker_names'):
                docker_names = self.context.get_docker_names()
                return docker_names.get('container_name', 'cph_container')
            return 'cph_container'
        
        # 既存のコンテナ名をそのまま使用
        # 必要に応じて環境状態に基づく変換ロジックを追加
        return container_name
    
    def _resolve_image_name(self, image_name: Optional[str]) -> str:
        """
        イメージ名を現在の環境状態に応じて解決
        
        Args:
            image_name: 元のイメージ名
            
        Returns:
            str: 解決されたイメージ名
        """
        if not image_name:
            # デフォルトイメージ名を使用
            if hasattr(self.context, 'get_docker_names'):
                docker_names = self.context.get_docker_names()
                return docker_names.get('image_name', 'python:3.10')
            return 'python:3.10'
        
        # 既存のイメージ名をそのまま使用
        # 必要に応じて環境状態に基づく変換ロジックを追加
        return image_name
    
    def analyze_environment_requirements(self, pure_requests: List[PureRequest]) -> Dict[str, Any]:
        """
        純粋リクエストから環境要件を分析
        
        Args:
            pure_requests: 純粋なリクエストのリスト
            
        Returns:
            Dict: 環境要件の分析結果
        """
        requirements = {
            'needs_docker': False,
            'needed_containers': set(),
            'needed_images': set(),
            'needed_directories': set(),
            'file_operations': [],
            'shell_commands': []
        }
        
        for request in pure_requests:
            if request.type == "docker":
                requirements['needs_docker'] = True
                if 'container' in request.params:
                    requirements['needed_containers'].add(request.params['container'])
                if 'image' in request.params:
                    requirements['needed_images'].add(request.params['image'])
            elif request.type == "file":
                requirements['file_operations'].append(request.operation)
                if request.operation in ['mkdir']:
                    requirements['needed_directories'].add(request.params.get('path'))
            elif request.type == "shell":
                requirements['shell_commands'].append(request.params.get('cmd', []))
        
        # リストに変換（JSONシリアライズ可能にするため）
        requirements['needed_containers'] = list(requirements['needed_containers'])
        requirements['needed_images'] = list(requirements['needed_images'])
        requirements['needed_directories'] = list(requirements['needed_directories'])
        
        return requirements