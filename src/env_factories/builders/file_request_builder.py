"""
File request builder
"""
from typing import Dict, Any
from .base_builder import RequestBuilder
from src.operations.file.file_request import FileRequest
from src.operations.file.file_op_type import FileOpType


class FileRequestBuilder(RequestBuilder):
    """File operation request builder"""
    
    def build_from_step(self, run_step, factory):
        """Build FileRequest from run step"""
        step_data = run_step.to_dict() if hasattr(run_step, 'to_dict') else run_step
        
        operation = step_data.get('operation', 'read')
        path = step_data.get('path', '')
        content = step_data.get('content')
        dst_path = step_data.get('dst_path')
        
        # Format paths if formatting context is available
        format_context = getattr(factory, '_format_context', {})
        if format_context:
            path = self._format_string(path, **format_context)
            if dst_path:
                dst_path = self._format_string(dst_path, **format_context)
            if content:
                content = self._format_string(content, **format_context)
        
        # Map operation string to FileOpType
        op_type = self._get_file_op_type(operation)
        
        return FileRequest(
            op=op_type,
            path=path,
            content=content,
            dst_path=dst_path,
            name=step_data.get('name', f'file_{operation}')
        )
    
    def build_from_node(self, node, factory):
        """Build FileRequest from ConfigNode"""
        # ConfigNodeの値を辞書として取得
        step_data = node.to_dict() if hasattr(node, 'to_dict') else {'path': str(node.value)}
        return self.build_from_step(step_data, factory)
    
    def build_from_kwargs(self, kwargs: Dict[str, Any], factory):
        """Build FileRequest from keyword arguments"""
        operation = kwargs.get('operation', 'read')
        op_type = self._get_file_op_type(operation)
        
        return FileRequest(
            op=op_type,
            path=kwargs.get('path', ''),
            content=kwargs.get('content'),
            dst_path=kwargs.get('dst_path'),
            name=kwargs.get('name', f'file_{operation}')
        )
    
    def _get_file_op_type(self, operation: str) -> FileOpType:
        """Convert operation string to FileOpType"""
        operation_map = {
            'read': FileOpType.READ,
            'write': FileOpType.WRITE,
            'exists': FileOpType.EXISTS,
            'move': FileOpType.MOVE,
            'copy': FileOpType.COPY,
            'copytree': FileOpType.COPYTREE,
            'remove': FileOpType.REMOVE,
            'rmtree': FileOpType.RMTREE,
            'mkdir': FileOpType.MKDIR,
            'touch': FileOpType.TOUCH,
        }
        return operation_map.get(operation.lower(), FileOpType.READ)