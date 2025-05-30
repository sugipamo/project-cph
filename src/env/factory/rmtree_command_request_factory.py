from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_rmtree import RmtreeRunStep
from src.operations.file.file_request import FileRequest, FileOpType

class RmtreeCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, RmtreeRunStep):
            raise TypeError(f"RmtreeCommandRequestFactory expects RmtreeRunStep, got {type(run_step).__name__}")
        target = run_step.target
        return FileRequest(FileOpType.RMTREE, target)
    
    def create_request_from_node(self, node):
        """ConfigNodeからFileRequestを生成"""
        if not node.value or not isinstance(node.value, dict):
            raise ValueError("Invalid node value for RmtreeCommandRequestFactory")
            
        target = node.value.get('target')
        if not target:
            raise ValueError("target is required for rmtree operation")
        
        # targetフィールドのConfigNodeを探す
        target_node = None
        for child in node.next_nodes:
            if child.key == 'target':
                target_node = child
                break
        
        # フォーマット済みのtargetを作成
        formatted_target = self.format_value(target, target_node if target_node else node)
        
        return FileRequest(FileOpType.RMTREE, formatted_target) 