"""
Shell request builder
"""
from typing import Dict, Any
from .base_builder import RequestBuilder
from src.operations.shell.shell_request import ShellRequest


class ShellRequestBuilder(RequestBuilder):
    """Shell command request builder"""
    
    def build_from_step(self, run_step, factory):
        """Build ShellRequest from run step"""
        step_data = run_step.to_dict() if hasattr(run_step, 'to_dict') else run_step
        
        cmd = step_data.get('cmd', [])
        show_output = step_data.get('show_output', True)
        allow_failure = step_data.get('allow_failure', False)
        working_dir = step_data.get('working_dir')
        env_vars = step_data.get('env_vars', {})
        input_data = step_data.get('input_data')
        
        # Format command if formatting context is available
        format_context = getattr(factory, '_format_context', {})
        if format_context:
            cmd = self._format_cmd_array(cmd, **format_context)
            if working_dir:
                working_dir = self._format_string(working_dir, **format_context)
            if input_data:
                input_data = self._format_string(input_data, **format_context)
        
        request = ShellRequest(
            cmd=cmd,
            show_output=show_output,
            working_dir=working_dir,
            env_vars=env_vars,
            inputdata=input_data,
            name=step_data.get('name', 'shell_command')
        )
        
        if allow_failure:
            request.allow_failure = True
        
        return request
    
    def build_from_node(self, node, factory):
        """Build ShellRequest from ConfigNode"""
        # ConfigNodeから値を抽出
        if hasattr(node, 'to_dict'):
            step_data = node.to_dict()
        else:
            # シンプルなコマンド文字列の場合
            cmd = str(node.value).split() if isinstance(node.value, str) else node.value
            step_data = {'cmd': cmd}
        
        return self.build_from_step(step_data, factory)
    
    def build_from_kwargs(self, kwargs: Dict[str, Any], factory):
        """Build ShellRequest from keyword arguments"""
        cmd = kwargs.get('cmd', [])
        
        request = ShellRequest(
            cmd=cmd,
            show_output=kwargs.get('show_output', True),
            working_dir=kwargs.get('working_dir'),
            env_vars=kwargs.get('env_vars', {}),
            inputdata=kwargs.get('input_data'),
            name=kwargs.get('name', 'shell_command')
        )
        
        if kwargs.get('allow_failure', False):
            request.allow_failure = True
        
        return request