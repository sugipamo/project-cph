from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_copy import CopyRunStep
from src.operations.file.file_request import FileRequest, FileOpType

class CopyCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, CopyRunStep):
            raise TypeError(f"CopyCommandRequestFactory expects CopyRunStep, got {type(run_step).__name__}")
        if len(run_step.cmd) < 2:
            raise ValueError("CopyRunStep: cmdにはsrcとdstの2つが必要です")
        src = self.format_string(run_step.cmd[0])
        dst = self.format_string(run_step.cmd[1])
        return FileRequest(FileOpType.COPY, src, dst_path=dst)
    
    def create_request_from_node(self, node):
        """ConfigNodeからFileRequestを生成"""
        if not node.value or not isinstance(node.value, dict):
            raise ValueError("Invalid node value for CopyCommandRequestFactory")
            
        cmd = node.value.get('cmd', [])
        if len(cmd) < 2:
            raise ValueError("CopyRunStep: cmdにはsrcとdstの2つが必要です")
        
        # cmdフィールドのConfigNodeを探す
        cmd_node = None
        for child in node.next_nodes:
            if child.key == 'cmd':
                cmd_node = child
                break
        
        if cmd_node and len(cmd_node.next_nodes) >= 2:
            # cmd配列の各要素のnodeを使ってフォーマット
            src_node = cmd_node.next_nodes[0]  # cmd[0]のnode
            dst_node = cmd_node.next_nodes[1]  # cmd[1]のnode
            
            src = self.format_value(cmd[0], src_node)
            dst = self.format_value(cmd[1], dst_node)
        else:
            # nodeが見つからない場合は値をそのまま使用
            src = self.format_value(cmd[0], node)
            dst = self.format_value(cmd[1], node)
        
        return FileRequest(FileOpType.COPY, src, dst_path=dst) 