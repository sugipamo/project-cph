from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_shell import ShellRunStep
from src.operations.shell.shell_request import ShellRequest

class ShellCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, ShellRunStep):
            raise TypeError(f"ShellCommandRequestFactory expects ShellRunStep, got {type(run_step).__name__}")
        cmd = [self.format_string(arg) for arg in run_step.cmd]
        cwd = self.format_string(run_step.cwd) if getattr(run_step, 'cwd', None) else None
        return ShellRequest(cmd, cwd=cwd, show_output=getattr(run_step, 'show_output', True))
    
    def create_request_from_node(self, node):
        """ConfigNodeからShellRequestを生成"""
        if not node.value or not isinstance(node.value, dict):
            raise ValueError("Invalid node value for ShellCommandRequestFactory")
            
        cmd = node.value.get('cmd', [])
        cwd = node.value.get('cwd')
        show_output = node.value.get('show_output', True)
        
        # cmdフィールドのConfigNodeを探す
        cmd_node = None
        for child in node.next_nodes:
            if child.key == 'cmd':
                cmd_node = child
                break
        
        # フォーマット済みのcmdを作成
        formatted_cmd = []
        if cmd_node and cmd_node.next_nodes:
            # cmd配列の各要素のnodeを使ってフォーマット
            for i, arg in enumerate(cmd):
                arg_node = None
                for child in cmd_node.next_nodes:
                    if child.key == i:
                        arg_node = child
                        break
                if arg_node:
                    formatted_cmd.append(self.format_value(arg, arg_node))
                else:
                    formatted_cmd.append(self.format_value(arg, node))
        else:
            # nodeが見つからない場合は親nodeを使用
            formatted_cmd = [self.format_value(arg, node) for arg in cmd]
        
        # cwdのフォーマット
        formatted_cwd = None
        if cwd:
            cwd_node = None
            for child in node.next_nodes:
                if child.key == 'cwd':
                    cwd_node = child
                    break
            formatted_cwd = self.format_value(cwd, cwd_node if cwd_node else node)
        
        return ShellRequest(formatted_cmd, cwd=formatted_cwd, show_output=show_output) 