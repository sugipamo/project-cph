"""
OutputManager フォーマッタ純粋関数のテスト
"""
import pytest
from src.pure_functions.output_manager_formatter_pure import (
    SimpleOutputData, extract_output_data, should_show_output,
    format_output_content, decide_output_action
)


class TestSimpleOutputData:
    """SimpleOutputDataのテスト"""
    
    def test_immutable(self):
        """イミュータブル性のテスト"""
        data = SimpleOutputData(stdout="test output", stderr="test error")
        
        # 変更を試みるとエラーになることを確認
        with pytest.raises(AttributeError):
            data.stdout = "new output"


class TestExtractOutputData:
    """extract_output_data関数のテスト"""
    
    def test_with_both_outputs(self):
        """stdout/stderr両方がある場合"""
        class MockResult:
            stdout = "standard output"
            stderr = "standard error"
        
        result = extract_output_data(MockResult())
        
        assert result.stdout == "standard output"
        assert result.stderr == "standard error"
    
    def test_with_stdout_only(self):
        """stdoutのみの場合"""
        class MockResult:
            stdout = "standard output"
        
        result = extract_output_data(MockResult())
        
        assert result.stdout == "standard output"
        assert result.stderr is None
    
    def test_with_stderr_only(self):
        """stderrのみの場合"""
        class MockResult:
            stderr = "standard error"
        
        result = extract_output_data(MockResult())
        
        assert result.stdout is None
        assert result.stderr == "standard error"
    
    def test_with_no_output_attributes(self):
        """出力属性がない場合"""
        class MockResult:
            pass
        
        result = extract_output_data(MockResult())
        
        assert result.stdout is None
        assert result.stderr is None
    
    def test_with_empty_strings(self):
        """空文字列の場合"""
        class MockResult:
            stdout = ""
            stderr = ""
        
        result = extract_output_data(MockResult())
        
        assert result.stdout == ""
        assert result.stderr == ""


class TestShouldShowOutput:
    """should_show_output関数のテスト"""
    
    def test_with_show_output_true(self):
        """show_outputがTrueの場合"""
        class MockRequest:
            show_output = True
        
        assert should_show_output(MockRequest()) is True
    
    def test_with_show_output_false(self):
        """show_outputがFalseの場合"""
        class MockRequest:
            show_output = False
        
        assert should_show_output(MockRequest()) is False
    
    def test_without_show_output_attribute(self):
        """show_output属性がない場合"""
        class MockRequest:
            pass
        
        assert should_show_output(MockRequest()) is False
    
    def test_with_none_value(self):
        """show_outputがNoneの場合"""
        class MockRequest:
            show_output = None
        
        assert should_show_output(MockRequest()) is False


class TestFormatOutputContent:
    """format_output_content関数のテスト"""
    
    def test_both_outputs(self):
        """両方の出力がある場合"""
        data = SimpleOutputData(stdout="Hello\n", stderr="Error\n")
        result = format_output_content(data)
        
        assert result == "Hello\nError\n"
    
    def test_stdout_only(self):
        """stdoutのみの場合"""
        data = SimpleOutputData(stdout="Hello World\n", stderr=None)
        result = format_output_content(data)
        
        assert result == "Hello World\n"
    
    def test_stderr_only(self):
        """stderrのみの場合"""
        data = SimpleOutputData(stdout=None, stderr="Error occurred\n")
        result = format_output_content(data)
        
        assert result == "Error occurred\n"
    
    def test_empty_outputs(self):
        """両方空の場合"""
        data = SimpleOutputData(stdout=None, stderr=None)
        result = format_output_content(data)
        
        assert result == ""
    
    def test_empty_strings(self):
        """空文字列の場合"""
        data = SimpleOutputData(stdout="", stderr="")
        result = format_output_content(data)
        
        assert result == ""
    
    def test_no_newline_concatenation(self):
        """改行なしの連結"""
        data = SimpleOutputData(stdout="Hello", stderr="World")
        result = format_output_content(data)
        
        assert result == "HelloWorld"


class TestDecideOutputAction:
    """decide_output_action関数のテスト"""
    
    def test_show_output_false(self):
        """出力フラグがFalseの場合"""
        data = SimpleOutputData(stdout="test", stderr="error")
        should_output, output_text = decide_output_action(False, data)
        
        assert should_output is False
        assert output_text == ""
    
    def test_no_output_data(self):
        """出力データがない場合"""
        data = SimpleOutputData(stdout=None, stderr=None)
        should_output, output_text = decide_output_action(True, data)
        
        assert should_output is False
        assert output_text == ""
    
    def test_with_stdout_only(self):
        """stdoutのみある場合"""
        data = SimpleOutputData(stdout="Hello World", stderr=None)
        should_output, output_text = decide_output_action(True, data)
        
        assert should_output is True
        assert output_text == "Hello World"
    
    def test_with_stderr_only(self):
        """stderrのみある場合"""
        data = SimpleOutputData(stdout=None, stderr="Error message")
        should_output, output_text = decide_output_action(True, data)
        
        assert should_output is True
        assert output_text == "Error message"
    
    def test_with_both_outputs(self):
        """両方の出力がある場合"""
        data = SimpleOutputData(stdout="Output\n", stderr="Error\n")
        should_output, output_text = decide_output_action(True, data)
        
        assert should_output is True
        assert output_text == "Output\nError\n"
    
    def test_empty_strings(self):
        """空文字列の場合"""
        data = SimpleOutputData(stdout="", stderr="")
        should_output, output_text = decide_output_action(True, data)
        
        assert should_output is False
        assert output_text == ""


class TestPureFunctionProperties:
    """純粋関数の性質をテスト"""
    
    def test_deterministic(self):
        """同じ入力に対して同じ出力を返すこと"""
        data = SimpleOutputData(stdout="test", stderr="error")
        
        # 複数回実行して同じ結果が返ることを確認
        result1 = format_output_content(data)
        result2 = format_output_content(data)
        result3 = format_output_content(data)
        
        assert result1 == result2 == result3
        
        # decide_output_actionも同様
        action1 = decide_output_action(True, data)
        action2 = decide_output_action(True, data)
        action3 = decide_output_action(True, data)
        
        assert action1 == action2 == action3
    
    def test_no_side_effects(self):
        """副作用がないことを確認"""
        # モック作成
        class MockRequest:
            show_output = True
        
        class MockResult:
            stdout = "original stdout"
            stderr = "original stderr"
        
        request = MockRequest()
        result = MockResult()
        
        # 関数実行
        should_show_output(request)
        extract_output_data(result)
        
        # 元のオブジェクトが変更されていないことを確認
        assert request.show_output is True
        assert result.stdout == "original stdout"
        assert result.stderr == "original stderr"
    
    def test_composability(self):
        """関数の組み合わせが可能なこと"""
        class MockRequest:
            show_output = True
        
        class MockResult:
            stdout = "Hello"
            stderr = "World"
        
        # 関数を組み合わせて使用
        show_flag = should_show_output(MockRequest())
        output_data = extract_output_data(MockResult())
        should_output, output_text = decide_output_action(show_flag, output_data)
        
        assert should_output is True
        assert output_text == "HelloWorld"