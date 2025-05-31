"""
Write operation strategy
"""
from .base_strategy import BaseFileOperationStrategy


class WriteStrategy(BaseFileOperationStrategy):
    """ファイル書き込み戦略"""
    
    def execute(self, driver, request):
        with driver.open(request.path, "w", encoding="utf-8") as f:
            f.write(request.content or "")
        return self._create_result(request)