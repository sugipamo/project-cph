"""
Python request builder
"""
from typing import Dict, Any
from .base_builder import RequestBuilder
from src.operations.python.python_request import PythonRequest


class PythonRequestBuilder(RequestBuilder):
    """Python execution request builder"""
    
    def build_from_step(self, run_step, factory):
        """Build PythonRequest from run step"""
        step_data = run_step.to_dict() if hasattr(run_step, 'to_dict') else run_step
        
        script_path = step_data.get('script_path', '')
        args = step_data.get('args', [])
        show_output = step_data.get('show_output', True)
        allow_failure = step_data.get('allow_failure', False)
        working_dir = step_data.get('working_dir')
        env_vars = step_data.get('env_vars', {})
        python_executable = step_data.get('python_executable', 'python')
        
        # Format paths if formatting context is available
        format_context = getattr(factory, '_format_context', {})
        if format_context:
            script_path = self._format_string(script_path, **format_context)
            args = self._format_cmd_array(args, **format_context)
            if working_dir:
                working_dir = self._format_string(working_dir, **format_context)
        
        request = PythonRequest(
            script_path=script_path,
            args=args,
            show_output=show_output,
            working_dir=working_dir,
            env_vars=env_vars,
            python_executable=python_executable,
            name=step_data.get('name', 'python_script')
        )
        
        if allow_failure:
            request.allow_failure = True
        
        return request
    
    def build_from_node(self, node, factory):
        """Build PythonRequest from ConfigNode"""
        if hasattr(node, 'to_dict'):
            step_data = node.to_dict()
        else:
            # シンプルなスクリプトパスの場合
            step_data = {'script_path': str(node.value)}
        
        return self.build_from_step(step_data, factory)
    
    def build_from_kwargs(self, kwargs: Dict[str, Any], factory):
        """Build PythonRequest from keyword arguments"""
        request = PythonRequest(
            script_path=kwargs.get('script_path', ''),
            args=kwargs.get('args', []),
            show_output=kwargs.get('show_output', True),
            working_dir=kwargs.get('working_dir'),
            env_vars=kwargs.get('env_vars', {}),
            python_executable=kwargs.get('python_executable', 'python'),
            name=kwargs.get('name', 'python_script')
        )
        
        if kwargs.get('allow_failure', False):
            request.allow_failure = True
        
        return request