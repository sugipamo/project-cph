#!/usr/bin/env python3
"""
テスト結果のステップ間受け渡し実装案
"""

class ResultSubstitution:
    """結果の動的置換機能"""
    
    @staticmethod
    def substitute_placeholders(command: str, previous_results: dict) -> str:
        """
        コマンド内のプレースホルダーを前のステップの結果で置換
        
        例:
        - {{step_0.result.stdout}} -> 前のステップの標準出力
        - {{step_test.result.returncode}} -> テストステップの戻り値
        """
        import re
        
        # {{step_X.result.Y}}形式のパターンを検索
        pattern = r'\{\{step_(\w+)\.result\.(\w+)\}\}'
        
        def replacer(match):
            step_id = match.group(1)
            field_name = match.group(2)
            
            if step_id in previous_results:
                result = previous_results[step_id]
                if hasattr(result, field_name):
                    value = getattr(result, field_name)
                    return str(value) if value is not None else ""
            
            return match.group(0)  # 置換できない場合は元のまま
        
        return re.sub(pattern, replacer, command)

# 使用例
def example_usage():
    """結果受け渡しの使用例"""
    
    # ステップ1: テストを実行して結果を保存
    test_result = {
        'stdout': 'All tests passed: 10/10',
        'returncode': 0,
        'stderr': '',
        'success': True
    }
    
    # ステップ2: テスト結果に基づいて次のコマンドを実行
    command_template = "echo 'Test result: {{step_test.result.stdout}}'"
    actual_command = ResultSubstitution.substitute_placeholders(
        command_template, 
        {'test': test_result}
    )
    
    print(f"Template: {command_template}")
    print(f"Actual: {actual_command}")
    # -> "echo 'Test result: All tests passed: 10/10'"

if __name__ == "__main__":
    example_usage()