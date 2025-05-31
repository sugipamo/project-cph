"""
Docker request builder
"""
from typing import Dict, Any
from .base_builder import RequestBuilder
from src.operations.docker.docker_request import DockerRequest, DockerOpType


class DockerRequestBuilder(RequestBuilder):
    """Docker operation request builder"""
    
    def build_from_step(self, run_step, factory):
        """Build DockerRequest from run step"""
        step_data = run_step.to_dict() if hasattr(run_step, 'to_dict') else run_step
        
        operation = step_data.get('operation', 'run')
        image = step_data.get('image', '')
        container_name = step_data.get('container_name')
        show_output = step_data.get('show_output', True)
        allow_failure = step_data.get('allow_failure', False)
        command = step_data.get('command')
        options = step_data.get('options', {})
        dockerfile_text = step_data.get('dockerfile_text')
        tag = step_data.get('tag')
        
        # Format values if formatting context is available
        format_context = getattr(factory, '_format_context', {})
        if format_context:
            image = self._format_string(image, **format_context)
            if container_name:
                container_name = self._format_string(container_name, **format_context)
            if command:
                command = self._format_cmd_array(command, **format_context)
            if tag:
                tag = self._format_string(tag, **format_context)
        
        # Map operation string to DockerOpType
        op_type = self._get_docker_op_type(operation)
        
        request = DockerRequest(
            op=op_type,
            image=image,
            container_name=container_name,
            command=command,
            options=options,
            dockerfile_text=dockerfile_text,
            tag=tag,
            show_output=show_output,
            name=step_data.get('name', f'docker_{operation}')
        )
        
        if allow_failure:
            request.allow_failure = True
        
        return request
    
    def build_from_node(self, node, factory):
        """Build DockerRequest from ConfigNode"""
        if hasattr(node, 'to_dict'):
            step_data = node.to_dict()
        else:
            # シンプルなイメージ名の場合
            step_data = {'image': str(node.value), 'operation': 'run'}
        
        return self.build_from_step(step_data, factory)
    
    def build_from_kwargs(self, kwargs: Dict[str, Any], factory):
        """Build DockerRequest from keyword arguments"""
        operation = kwargs.get('operation', 'run')
        op_type = self._get_docker_op_type(operation)
        
        request = DockerRequest(
            op=op_type,
            image=kwargs.get('image', ''),
            container_name=kwargs.get('container_name'),
            command=kwargs.get('command'),
            options=kwargs.get('options', {}),
            dockerfile_text=kwargs.get('dockerfile_text'),
            tag=kwargs.get('tag'),
            show_output=kwargs.get('show_output', True),
            name=kwargs.get('name', f'docker_{operation}')
        )
        
        if kwargs.get('allow_failure', False):
            request.allow_failure = True
        
        return request
    
    def _get_docker_op_type(self, operation: str) -> DockerOpType:
        """Convert operation string to DockerOpType"""
        operation_map = {
            'run': DockerOpType.RUN,
            'build': DockerOpType.BUILD,
            'stop': DockerOpType.STOP,
            'remove': DockerOpType.REMOVE,
            'exec': DockerOpType.EXEC,
            'logs': DockerOpType.LOGS,
            'ps': DockerOpType.PS,
            'images': DockerOpType.IMAGES,
            'inspect': DockerOpType.INSPECT,
            'cp': DockerOpType.CP,
        }
        return operation_map.get(operation.lower(), DockerOpType.RUN)