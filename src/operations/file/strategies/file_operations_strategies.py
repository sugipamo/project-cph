"""
File operation strategies for various file operations
"""
from .base_strategy import BaseFileOperationStrategy


class ExistsStrategy(BaseFileOperationStrategy):
    """ファイル存在確認戦略"""
    
    def execute(self, driver, request):
        exists = driver.exists(request.path)
        return self._create_result(request, exists=exists)


class MoveStrategy(BaseFileOperationStrategy):
    """ファイル移動戦略"""
    
    def execute(self, driver, request):
        driver.move(request.path, request.dst_path)
        return self._create_result(request)


class CopyStrategy(BaseFileOperationStrategy):
    """ファイルコピー戦略"""
    
    def execute(self, driver, request):
        driver.copy(request.path, request.dst_path)
        return self._create_result(request)


class CopyTreeStrategy(BaseFileOperationStrategy):
    """ディレクトリツリーコピー戦略"""
    
    def execute(self, driver, request):
        driver.copytree(request.path, request.dst_path)
        return self._create_result(request)


class RemoveStrategy(BaseFileOperationStrategy):
    """ファイル削除戦略"""
    
    def execute(self, driver, request):
        driver.remove(request.path)
        return self._create_result(request)


class RmTreeStrategy(BaseFileOperationStrategy):
    """ディレクトリツリー削除戦略"""
    
    def execute(self, driver, request):
        driver.rmtree(request.path)
        return self._create_result(request)


class MkdirStrategy(BaseFileOperationStrategy):
    """ディレクトリ作成戦略"""
    
    def execute(self, driver, request):
        driver.mkdir(request.path)
        return self._create_result(request)


class TouchStrategy(BaseFileOperationStrategy):
    """ファイル作成戦略"""
    
    def execute(self, driver, request):
        driver.touch(request.path)
        return self._create_result(request)