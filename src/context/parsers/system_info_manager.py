"""
System information management
"""
import json
from typing import Dict, Any


class SystemInfoManager:
    """システム情報の読み書きを管理"""
    
    def __init__(self, operations, path="system_info.json"):
        self.operations = operations
        self.path = path
    
    def load_system_info(self) -> Dict[str, Any]:
        """
        システム情報を読み込む
        
        Returns:
            Dict[str, Any]: システム情報
        """
        file_driver = self.operations.resolve("file_driver")
        from src.operations.file.file_request import FileRequest
        from src.operations.file.file_op_type import FileOpType
        
        req = FileRequest(FileOpType.EXISTS, self.path)
        result = req.execute(driver=file_driver)
        
        if not result.exists:
            return {
                "command": None,
                "language": None,
                "env_type": None,
                "contest_name": None,
                "problem_name": None,
                "env_json": None,
            }
        
        req = FileRequest(FileOpType.READ, self.path)
        result = req.execute(driver=file_driver)
        return json.loads(result.content)
    
    def save_system_info(self, info: Dict[str, Any]):
        """
        システム情報を保存する
        
        Args:
            info: 保存するシステム情報
        """
        file_driver = self.operations.resolve("file_driver")
        from src.operations.file.file_request import FileRequest
        from src.operations.file.file_op_type import FileOpType
        
        req = FileRequest(
            FileOpType.WRITE, 
            self.path, 
            content=json.dumps(info, ensure_ascii=False, indent=2)
        )
        req.execute(driver=file_driver)