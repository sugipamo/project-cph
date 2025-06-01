from src.operations.constants.operation_type import OperationType
from src.operations.file.local_file_driver import LocalFileDriver
from src.operations.result import OperationResult
from src.operations.base_request import BaseRequest
from src.operations.file.strategies.strategy_factory import FileOperationStrategyFactory
from src.operations.file.file_op_type import FileOpType
import inspect
import os
import time

class FileRequest(BaseRequest):
    # Class-level strategy cache for better performance
    _strategy_cache = {}
    
    def __init__(self, op: FileOpType, path, content=None, dst_path=None, debug_tag=None, name=None):
        super().__init__(name=name, debug_tag=debug_tag)
        self.op = op  # FileOpType
        self.path = path
        self.content = content
        self.dst_path = dst_path  # move/copy/copytree用
        self._executed = False
        self._result = None

    def set_name(self, name: str):
        self.name = name
        return self

    @property
    def operation_type(self):
        return OperationType.FILE

    def execute(self, driver):
        return super().execute(driver)

    def _execute_core(self, driver):
        """
        コア実行ロジック
        
        パフォーマンス最適化:
        - ストラテジーインスタンスのキャッシング
        - より精密な時間計測
        """
        self._start_time = time.time()  # Use time.time() for consistency
        try:
            # Use cached strategy for better performance
            strategy = self._strategy_cache.get(self.op)
            if strategy is None:
                strategy = FileOperationStrategyFactory.get_strategy(self.op)
                self._strategy_cache[self.op] = strategy
            
            # If driver is UnifiedDriver, get the file driver specifically
            from src.operations.composite.unified_driver import UnifiedDriver
            if isinstance(driver, UnifiedDriver):
                actual_driver = driver._get_cached_driver("file_driver")
            else:
                actual_driver = driver
            
            return strategy.execute(actual_driver, self)
        except Exception as e:
            raise RuntimeError(f"FileRequest failed: {str(e)}")

    def __repr__(self):
        return f"<FileRequest name={self.name} op={self.op} path={self.path} dst={getattr(self, 'dst_path', None)} content={getattr(self, 'content', None)} >" 