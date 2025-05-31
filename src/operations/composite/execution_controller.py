"""
実行制御を担当するクラス
"""
from src.operations.exceptions.composite_step_failure import CompositeStepFailure


class ExecutionController:
    """リクエスト実行の制御を担当"""
    
    def execute_requests(self, requests, driver):
        """
        リクエストのリストを順次実行する
        
        Args:
            requests: 実行するリクエストのリスト
            driver: 実行ドライバー
            
        Returns:
            実行結果のリスト
        """
        results = []
        for req in requests:
            result = req.execute(driver=driver)
            results.append(result)
            self._check_failure(req, result)
        
        return results
    
    def _check_failure(self, request, result):
        """
        実行結果の失敗をチェックし、必要に応じて例外を発生させる
        
        Args:
            request: 実行されたリクエスト
            result: 実行結果
        """
        # allow_failureがFalseまたは未指定、かつ失敗した場合は即停止
        allow_failure = getattr(request, 'allow_failure', False)
        if not allow_failure and not (hasattr(result, 'success') and result.success):
            raise CompositeStepFailure(
                f"Step failed: {request} (allow_failure=False)\nResult: {result}", 
                result=result
            )