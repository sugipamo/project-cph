from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_remove import RemoveRunStep
from src.operations.file.file_request import FileRequest, FileOpType

class RemoveCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, RemoveRunStep):
            raise TypeError(f"RemoveCommandRequestFactory expects RemoveRunStep, got {type(run_step).__name__}")
        target = run_step.target
        return FileRequest(FileOpType.REMOVE, target)
    
    def create_request_from_node(self, node):
        """ConfigNodeからFileRequestを生成"""
        if not node.value or not isinstance(node.value, dict):
            raise ValueError("Invalid node value for RemoveCommandRequestFactory")
            
        target = node.value.get('target')
        if not target:
            raise ValueError("target is required for remove operation")
        
        # targetフィールドのConfigNodeを探す
        target_node = None
        for child in node.next_nodes:
            if child.key == 'target':
                target_node = child
                break
        
        # フォーマット済みのtargetを作成
        formatted_target = self.format_value(target, target_node if target_node else node)
        
        return FileRequest(FileOpType.REMOVE, formatted_target) 