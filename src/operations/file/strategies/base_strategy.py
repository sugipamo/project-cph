"""
Base strategy for file operations
"""
from abc import ABC, abstractmethod
import time
from src.operations.result import OperationResult


class BaseFileOperationStrategy(ABC):
    """ファイル操作戦略の基底クラス"""
    
    @abstractmethod
    def execute(self, driver, request):
        """
        ファイル操作を実行する
        
        Args:
            driver: ファイルドライバー
            request: ファイルリクエスト
            
        Returns:
            OperationResult: 実行結果
        """
        pass
    
    def _create_result(self, request, success=True, **kwargs):
        """
        操作結果を作成する
        
        Args:
            request: ファイルリクエスト
            success: 成功フラグ
            **kwargs: 追加の結果データ
            
        Returns:
            OperationResult: 操作結果
        """
        return OperationResult(
            success=success,
            path=request.path,
            op=request.op,
            request=request,
            start_time=getattr(request, '_start_time', time.time()),
            end_time=time.time(),
            **kwargs
        )