from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_build import BuildRunStep
from src.operations.shell.shell_request import ShellRequest

class BuildCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, BuildRunStep):
            raise TypeError(f"BuildCommandRequestFactory expects BuildRunStep, got {type(run_step).__name__}")
        cmd = run_step.cmd or ["make"]  # デフォルトでmakeを実行（必要に応じて変更）
        return ShellRequest(cmd)
    
    def create_request_from_node(self, node):
        """ConfigNodeからShellRequestを生成"""
        if node.value is None or not isinstance(node.value, dict):
            raise ValueError("Invalid node value for BuildCommandRequestFactory")
            
        cmd = node.value.get('cmd', ["make"])  # デフォルトでmake
        
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
        
        return ShellRequest(formatted_cmd) 