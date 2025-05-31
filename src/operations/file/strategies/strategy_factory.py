"""
Strategy factory for file operations
"""
from ..file_op_type import FileOpType
from .read_strategy import ReadStrategy
from .write_strategy import WriteStrategy
from .file_operations_strategies import (
    ExistsStrategy, MoveStrategy, CopyStrategy, CopyTreeStrategy,
    RemoveStrategy, RmTreeStrategy, MkdirStrategy, TouchStrategy
)


class FileOperationStrategyFactory:
    """ファイル操作戦略のファクトリー"""
    
    _strategies = {
        FileOpType.READ: ReadStrategy(),
        FileOpType.WRITE: WriteStrategy(),
        FileOpType.EXISTS: ExistsStrategy(),
        FileOpType.MOVE: MoveStrategy(),
        FileOpType.COPY: CopyStrategy(),
        FileOpType.COPYTREE: CopyTreeStrategy(),
        FileOpType.REMOVE: RemoveStrategy(),
        FileOpType.RMTREE: RmTreeStrategy(),
        FileOpType.MKDIR: MkdirStrategy(),
        FileOpType.TOUCH: TouchStrategy(),
    }
    
    @classmethod
    def get_strategy(cls, op_type: FileOpType):
        """
        操作タイプに応じた戦略を取得する
        
        Args:
            op_type: ファイル操作タイプ
            
        Returns:
            BaseFileOperationStrategy: 対応する戦略
            
        Raises:
            ValueError: 未対応の操作タイプの場合
        """
        if op_type not in cls._strategies:
            raise ValueError(f"Unsupported operation type: {op_type}")
        return cls._strategies[op_type]