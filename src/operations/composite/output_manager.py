"""
出力表示制御を担当するクラス
"""


class OutputManager:
    """リクエスト実行結果の出力制御を担当"""
    
    @staticmethod
    def handle_request_output(request, result):
        """
        リクエストの実行結果の出力を処理する
        
        Args:
            request: 実行されたリクエスト
            result: 実行結果
        """
        # show_output属性がTrueなら出力を表示
        if hasattr(request, 'show_output') and request.show_output:
            if hasattr(result, 'stdout') and result.stdout:
                print(result.stdout, end="")
            if hasattr(result, 'stderr') and result.stderr:
                print(result.stderr, end="")
    
    @classmethod
    def execute_with_output_handling(cls, requests, execution_func, driver):
        """
        出力処理付きでリクエストを実行する
        
        Args:
            requests: 実行するリクエストのリスト
            execution_func: 実行関数
            driver: 実行ドライバー
            
        Returns:
            実行結果のリスト
        """
        results = []
        for req in requests:
            result = execution_func(req, driver)
            cls.handle_request_output(req, result)
            results.append(result)
        
        return results