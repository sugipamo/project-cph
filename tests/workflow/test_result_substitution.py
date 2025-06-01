#!/usr/bin/env python3
"""
結果置換機能のテスト
"""
import pytest
from src.env_core.workflow.request_execution_graph import RequestExecutionGraph, RequestNode
from src.operations.shell.shell_request import ShellRequest
from src.operations.result.result import OperationResult
from src.env_core.step.step import StepType
from src.env_core.workflow.pure_request_factory import PureRequestFactory


class TestResultSubstitution:
    """結果置換機能のテストクラス"""
    
    def test_basic_result_substitution(self):
        """基本的な結果置換のテスト"""
        graph = RequestExecutionGraph()
        
        # テスト結果をセット
        test_result = OperationResult(
            success=True,
            returncode=0,
            stdout="Test passed: 5/5",
            stderr=""
        )
        graph.execution_results["test"] = test_result
        
        # 置換テスト
        test_cases = [
            ("{{step_test.stdout}}", "Test passed: 5/5"),
            ("{{step_test.returncode}}", "0"),
            ("{{step_test.success}}", "True"),
            ("Result: {{step_test.stdout}}", "Result: Test passed: 5/5"),
            ("Code {{step_test.returncode}} means {{step_test.success}}", "Code 0 means True")
        ]
        
        for input_text, expected in test_cases:
            result = graph.substitute_result_placeholders(input_text)
            assert result == expected, f"Expected '{expected}', got '{result}'"
    
    def test_result_format_patterns(self):
        """結果形式パターンのテスト"""
        graph = RequestExecutionGraph()
        
        # テスト結果をセット
        test_result = OperationResult(
            success=True,
            returncode=0,
            stdout="output",
            stderr="error"
        )
        graph.execution_results["test"] = test_result
        
        # 両方の形式をテスト
        test_cases = [
            ("{{step_test.result.stdout}}", "output"),  # .result.形式
            ("{{step_test.stdout}}", "output"),         # 直接形式
            ("{{step_test.result.returncode}}", "0"),
            ("{{step_test.returncode}}", "0")
        ]
        
        for input_text, expected in test_cases:
            result = graph.substitute_result_placeholders(input_text)
            assert result == expected
    
    def test_multiple_step_substitution(self):
        """複数ステップの置換テスト"""
        graph = RequestExecutionGraph()
        
        # 複数の結果をセット
        graph.execution_results["compile"] = OperationResult(
            success=True, returncode=0, stdout="Compilation successful"
        )
        graph.execution_results["test"] = OperationResult(
            success=True, returncode=0, stdout="5 tests passed"
        )
        
        input_text = "Compile: {{step_compile.stdout}}, Test: {{step_test.stdout}}"
        expected = "Compile: Compilation successful, Test: 5 tests passed"
        result = graph.substitute_result_placeholders(input_text)
        
        assert result == expected
    
    def test_nonexistent_step_substitution(self):
        """存在しないステップの置換テスト"""
        graph = RequestExecutionGraph()
        
        input_text = "Result: {{step_nonexistent.stdout}}"
        result = graph.substitute_result_placeholders(input_text)
        
        # 置換できない場合は元のまま
        assert result == input_text
    
    def test_request_substitution_application(self):
        """リクエストへの置換適用テスト"""
        graph = RequestExecutionGraph()
        
        # テスト結果をセット
        graph.execution_results["test"] = OperationResult(
            success=True, returncode=0, stdout="success"
        )
        
        # ShellRequestに置換を適用
        request = ShellRequest(cmd=["echo", "{{step_test.stdout}}"])
        graph.apply_result_substitution_to_request(request, "current")
        
        assert request.cmd == ["echo", "success"]
    
    def test_result_step_type_creation(self):
        """RESULTステップタイプの作成テスト"""
        from src.env_core.step.step import Step, StepType
        
        # RESULTステップを作成
        step = Step(type=StepType.RESULT, cmd=["echo", "Test result: {{step_test.stdout}}"])
        
        # PureRequestFactoryで変換
        request = PureRequestFactory.create_request_from_step(step, None)
        
        assert request is not None
        assert hasattr(request, 'cmd')
        assert request.cmd == ["echo", "Test result: {{step_test.stdout}}"]
        assert request.show_output is True  # RESULTは常に出力表示
    
    def test_sorted_sample_test_execution(self):
        """ソートされたサンプルテストの実行テスト"""
        from src.env_core.step.step import Step, StepType
        
        # TESTステップのbashスクリプト内容を確認
        step = Step(type=StepType.TEST, cmd=["python", "main.py"])
        request = PureRequestFactory.create_request_from_step(step, None)
        
        # bashスクリプトにsortコマンドが含まれていることを確認
        bash_script = " ".join(request.cmd)
        assert "sort" in bash_script
        assert "ls" in bash_script
        assert "sample-*.in" in bash_script
    
    def test_none_value_substitution(self):
        """None値の置換テスト"""
        graph = RequestExecutionGraph()
        
        # None値を含む結果をセット
        test_result = OperationResult(
            success=True,
            returncode=0,
            stdout=None,  # None値
            stderr="error"
        )
        graph.execution_results["test"] = test_result
        
        result = graph.substitute_result_placeholders("Output: {{step_test.stdout}}")
        assert result == "Output: "  # None値は空文字列に変換


if __name__ == "__main__":
    pytest.main([__file__])