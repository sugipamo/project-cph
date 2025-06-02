"""
出力表示制御を担当するクラス
"""
from src.pure_functions.output_manager_formatter_pure import (
    extract_output_data, should_show_output, 
    decide_output_action
)


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
        # 純粋関数を使用して出力決定
        show_output_flag = should_show_output(request)
        output_data = extract_output_data(result)
        should_output, output_text = decide_output_action(show_output_flag, output_data)
        
        # 出力が必要な場合のみprint（副作用）
        if should_output:
            print(output_text, end="")
    
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