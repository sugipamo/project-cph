from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_touch import TouchRunStep
from src.operations.file.file_request import FileRequest, FileOpType

class TouchCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, TouchRunStep):
            raise TypeError(f"TouchCommandRequestFactory expects TouchRunStep, got {type(run_step).__name__}")
        target = self.format_string(run_step.target)
        return FileRequest(FileOpType.TOUCH, target)
    
    def create_request_from_node(self, node):
        """ConfigNodeからFileRequestを生成"""
        if not node.value or not isinstance(node.value, dict):
            raise ValueError("Invalid node value for TouchCommandRequestFactory")
            
        target = node.value.get('target')
        if not target:
            raise ValueError("target is required for touch operation")
        
        # targetフィールドのConfigNodeを探す
        target_node = None
        for child in node.next_nodes:
            if child.key == 'target':
                target_node = child
                break
        
        # フォーマット済みのtargetを作成
        formatted_target = self.format_value(target, target_node if target_node else node)
        
        return FileRequest(FileOpType.TOUCH, formatted_target) 