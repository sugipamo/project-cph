"""
Read operation strategy
"""
from .base_strategy import BaseFileOperationStrategy


class ReadStrategy(BaseFileOperationStrategy):
    """ファイル読み込み戦略"""
    
    def execute(self, driver, request):
        with driver.open(request.path, "r", encoding="utf-8") as f:
            content = f.read()
        return self._create_result(request, content=content)