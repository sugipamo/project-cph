from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_oj import OjRunStep
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.operations.shell.shell_request import ShellRequest
from src.operations.composite.composite_request import CompositeRequest
from src.env.resource.utils.docker_naming import get_oj_container_name

class OjCommandRequestFactory(BaseCommandRequestFactory):
    def __init__(self, controller, DockerRequestClass, DockerOpTypeClass):
        super().__init__(controller)
        self.DockerRequest = DockerRequestClass
        self.DockerOpType = DockerOpTypeClass

    def create_request(self, run_step):
        if not isinstance(run_step, OjRunStep):
            raise TypeError(f"OjCommandRequestFactory expects OjRunStep, got {type(run_step).__name__}")
        if not run_step.cmd:
            raise ValueError("OjRunStep: cmdは必須です")
        cmd = [self.format_string(arg) for arg in run_step.cmd]
        cwd = self.format_string(run_step.cwd) if getattr(run_step, 'cwd', None) else None
        env_type = self.controller.env_context.env_type.lower()
        if env_type == "docker":
            oj_dockerfile_text = getattr(self.controller.env_context, 'oj_dockerfile', None)
            container_name = get_oj_container_name(oj_dockerfile_text)
            # BUILDやRUNリクエストは生成しない
            exec_req = self.DockerRequest(
                self.DockerOpType.EXEC,
                container=container_name,
                command=" ".join(cmd),
                show_output=getattr(run_step, 'show_output', True)
            )
            exec_req.allow_failure = getattr(run_step, 'allow_failure', False)
            return exec_req
        else:
            request = ShellRequest(cmd, cwd=cwd, show_output=getattr(run_step, 'show_output', True))
            request.allow_failure = getattr(run_step, 'allow_failure', False)
            return request
    
    def create_request_from_node(self, node):
        """ConfigNodeからリクエストを生成"""
        if not node.value or not isinstance(node.value, dict):
            raise ValueError("Invalid node value for OjCommandRequestFactory")
            
        cmd = node.value.get('cmd', [])
        if not cmd:
            raise ValueError("OjRunStep: cmdは必須です")
            
        cwd = node.value.get('cwd')
        show_output = node.value.get('show_output', True)
        allow_failure = node.value.get('allow_failure', False)
        env_type = self.controller.env_context.env_type.lower()
        
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
        
        if env_type == "docker":
            oj_dockerfile_text = getattr(self.controller.env_context, 'oj_dockerfile', None)
            container_name = get_oj_container_name(oj_dockerfile_text)
            # BUILDやRUNリクエストは生成しない
            exec_req = self.DockerRequest(
                self.DockerOpType.EXEC,
                container=container_name,
                command=" ".join(formatted_cmd),
                show_output=show_output
            )
            exec_req.allow_failure = allow_failure
            return exec_req
        else:
            request = ShellRequest(formatted_cmd, cwd=formatted_cwd, show_output=show_output)
            request.allow_failure = allow_failure
            return request 