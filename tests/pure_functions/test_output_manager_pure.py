"""
出力表示制御純粋関数のテスト
モック不要で実際の動作をテスト
"""
import pytest
from src.pure_functions.output_manager_pure import (
    OutputType,
    OutputContent,
    RequestInfo,
    OutputDecision,
    OutputAction,
    OutputProcessingResult,
    should_show_output_pure,
    create_output_actions_pure,
    filter_output_content_pure,
    process_multiple_outputs_pure,
    analyze_output_patterns_pure,
    create_output_summary_pure,
    optimize_output_display_pure,
    validate_output_configuration_pure
)


class TestOutputType:
    """OutputType列挙型のテスト"""
    
    def test_output_type_values(self):
        """出力タイプの値テスト"""
        assert OutputType.STDOUT.value == "stdout"
        assert OutputType.STDERR.value == "stderr"
        assert OutputType.COMBINED.value == "combined"
        assert OutputType.NONE.value == "none"


class TestOutputContent:
    """OutputContentのテスト"""
    
    def test_create_output_content(self):
        """出力内容作成のテスト"""
        content = OutputContent(
            stdout="Hello World",
            stderr="Error message"
        )
        
        assert content.stdout == "Hello World"
        assert content.stderr == "Error message"
    
    def test_has_stdout(self):
        """標準出力判定のテスト"""
        content = OutputContent(stdout="Hello", stderr="")
        assert content.has_stdout() is True
        
        content = OutputContent(stdout="", stderr="Error")
        assert content.has_stdout() is False
        
        content = OutputContent(stdout="   ", stderr="")
        assert content.has_stdout() is False
    
    def test_has_stderr(self):
        """標準エラー判定のテスト"""
        content = OutputContent(stdout="", stderr="Error")
        assert content.has_stderr() is True
        
        content = OutputContent(stdout="Hello", stderr="")
        assert content.has_stderr() is False
        
        content = OutputContent(stdout="", stderr="   ")
        assert content.has_stderr() is False
    
    def test_has_any_output(self):
        """出力存在判定のテスト"""
        content = OutputContent(stdout="Hello", stderr="")
        assert content.has_any_output() is True
        
        content = OutputContent(stdout="", stderr="Error")
        assert content.has_any_output() is True
        
        content = OutputContent(stdout="Hello", stderr="Error")
        assert content.has_any_output() is True
        
        content = OutputContent(stdout="", stderr="")
        assert content.has_any_output() is False
    
    def test_get_combined(self):
        """結合出力取得のテスト"""
        content = OutputContent(stdout="Hello", stderr="Error")
        assert content.get_combined() == "HelloError"
        
        content = OutputContent(stdout="Hello", stderr="")
        assert content.get_combined() == "Hello"
        
        content = OutputContent(stdout="", stderr="Error")
        assert content.get_combined() == "Error"
        
        content = OutputContent(stdout="", stderr="")
        assert content.get_combined() == ""
    
    def test_output_content_immutability(self):
        """出力内容の不変性テスト"""
        content = OutputContent(stdout="Hello", stderr="Error")
        
        with pytest.raises(AttributeError):
            content.stdout = "Changed"


class TestRequestInfo:
    """RequestInfoのテスト"""
    
    def test_create_request_info(self):
        """リクエスト情報作成のテスト"""
        info = RequestInfo(
            show_output=True,
            request_type="shell",
            allow_failure=False,
            name="test_request"
        )
        
        assert info.show_output is True
        assert info.request_type == "shell"
        assert info.allow_failure is False
        assert info.name == "test_request"
    
    def test_request_info_defaults(self):
        """リクエスト情報デフォルト値のテスト"""
        info = RequestInfo()
        
        assert info.show_output is False
        assert info.request_type == "unknown"
        assert info.allow_failure is False
        assert info.name is None
    
    def test_from_request(self):
        """リクエストオブジェクトからの作成テスト"""
        # モックリクエストオブジェクト
        class MockRequest:
            def __init__(self):
                self.show_output = True
                self.request_type = "docker"
                self.allow_failure = True
                self.name = "mock_request"
        
        mock_request = MockRequest()
        info = RequestInfo.from_request(mock_request)
        
        assert info.show_output is True
        assert info.request_type == "docker"
        assert info.allow_failure is True
        assert info.name == "mock_request"
    
    def test_from_request_missing_attributes(self):
        """属性なしリクエストからの作成テスト"""
        class MockRequest:
            pass
        
        mock_request = MockRequest()
        info = RequestInfo.from_request(mock_request)
        
        assert info.show_output is False
        assert info.request_type == "unknown"
        assert info.allow_failure is False
        assert info.name is None


class TestOutputDecision:
    """OutputDecisionのテスト"""
    
    def test_create_output_decision(self):
        """出力判定結果作成のテスト"""
        decision = OutputDecision(
            should_show_stdout=True,
            should_show_stderr=False,
            output_type=OutputType.STDOUT,
            reason="stdout available",
            filter_applied=True
        )
        
        assert decision.should_show_stdout is True
        assert decision.should_show_stderr is False
        assert decision.output_type == OutputType.STDOUT
        assert decision.reason == "stdout available"
        assert decision.filter_applied is True
    
    def test_output_decision_defaults(self):
        """出力判定結果デフォルト値のテスト"""
        decision = OutputDecision(
            should_show_stdout=True,
            should_show_stderr=False,
            output_type=OutputType.STDOUT,
            reason="test"
        )
        
        assert decision.filter_applied is False


class TestShouldShowOutputPure:
    """出力表示判定関数のテスト"""
    
    def test_show_output_disabled(self):
        """出力表示無効時のテスト"""
        request_info = RequestInfo(show_output=False)
        output_content = OutputContent(stdout="Hello", stderr="Error")
        
        decision = should_show_output_pure(request_info, output_content)
        
        assert decision.should_show_stdout is False
        assert decision.should_show_stderr is False
        assert decision.output_type == OutputType.NONE
        assert decision.reason == "show_output is disabled"
    
    def test_no_output_content(self):
        """出力内容なし時のテスト"""
        request_info = RequestInfo(show_output=True)
        output_content = OutputContent(stdout="", stderr="")
        
        decision = should_show_output_pure(request_info, output_content)
        
        assert decision.should_show_stdout is False
        assert decision.should_show_stderr is False
        assert decision.output_type == OutputType.NONE
        assert decision.reason == "no output content"
    
    def test_stdout_only(self):
        """標準出力のみの場合のテスト"""
        request_info = RequestInfo(show_output=True)
        output_content = OutputContent(stdout="Hello", stderr="")
        
        decision = should_show_output_pure(request_info, output_content)
        
        assert decision.should_show_stdout is True
        assert decision.should_show_stderr is False
        assert decision.output_type == OutputType.STDOUT
        assert decision.reason == "stdout available"
    
    def test_stderr_only(self):
        """標準エラーのみの場合のテスト"""
        request_info = RequestInfo(show_output=True)
        output_content = OutputContent(stdout="", stderr="Error")
        
        decision = should_show_output_pure(request_info, output_content)
        
        assert decision.should_show_stdout is False
        assert decision.should_show_stderr is True
        assert decision.output_type == OutputType.STDERR
        assert decision.reason == "stderr available"
    
    def test_both_outputs(self):
        """両方の出力がある場合のテスト"""
        request_info = RequestInfo(show_output=True)
        output_content = OutputContent(stdout="Hello", stderr="Error")
        
        decision = should_show_output_pure(request_info, output_content)
        
        assert decision.should_show_stdout is True
        assert decision.should_show_stderr is True
        assert decision.output_type == OutputType.COMBINED
        assert decision.reason == "both stdout and stderr available"
    
    def test_whitespace_only_output(self):
        """空白のみの出力のテスト"""
        request_info = RequestInfo(show_output=True)
        output_content = OutputContent(stdout="   ", stderr="  \n  ")
        
        decision = should_show_output_pure(request_info, output_content)
        
        assert decision.should_show_stdout is False
        assert decision.should_show_stderr is False
        assert decision.output_type == OutputType.NONE
        assert decision.reason == "no output content"


class TestCreateOutputActionsPure:
    """出力アクション作成関数のテスト"""
    
    def test_create_stdout_action(self):
        """標準出力アクション作成のテスト"""
        content = OutputContent(stdout="Hello World", stderr="")
        decision = OutputDecision(
            should_show_stdout=True,
            should_show_stderr=False,
            output_type=OutputType.STDOUT,
            reason="stdout available"
        )
        
        actions = create_output_actions_pure(content, decision)
        
        assert len(actions) == 1
        assert actions[0].content == "Hello World"
        assert actions[0].output_type == OutputType.STDOUT
        assert actions[0].metadata["source"] == "stdout"
        assert actions[0].metadata["length"] == 11
    
    def test_create_stderr_action(self):
        """標準エラーアクション作成のテスト"""
        content = OutputContent(stdout="", stderr="Error message")
        decision = OutputDecision(
            should_show_stdout=False,
            should_show_stderr=True,
            output_type=OutputType.STDERR,
            reason="stderr available"
        )
        
        actions = create_output_actions_pure(content, decision)
        
        assert len(actions) == 1
        assert actions[0].content == "Error message"
        assert actions[0].output_type == OutputType.STDERR
        assert actions[0].metadata["source"] == "stderr"
        assert actions[0].metadata["length"] == 13
    
    def test_create_both_actions(self):
        """両方のアクション作成のテスト"""
        content = OutputContent(stdout="Hello", stderr="Error")
        decision = OutputDecision(
            should_show_stdout=True,
            should_show_stderr=True,
            output_type=OutputType.COMBINED,
            reason="both outputs available"
        )
        
        actions = create_output_actions_pure(content, decision)
        
        assert len(actions) == 2
        
        stdout_action = next(a for a in actions if a.output_type == OutputType.STDOUT)
        stderr_action = next(a for a in actions if a.output_type == OutputType.STDERR)
        
        assert stdout_action.content == "Hello"
        assert stderr_action.content == "Error"
    
    def test_create_no_actions(self):
        """アクション作成なしのテスト"""
        content = OutputContent(stdout="Hello", stderr="Error")
        decision = OutputDecision(
            should_show_stdout=False,
            should_show_stderr=False,
            output_type=OutputType.NONE,
            reason="output disabled"
        )
        
        actions = create_output_actions_pure(content, decision)
        
        assert len(actions) == 0
    
    def test_create_actions_empty_content(self):
        """空内容でのアクション作成テスト"""
        content = OutputContent(stdout="", stderr="")
        decision = OutputDecision(
            should_show_stdout=True,
            should_show_stderr=True,
            output_type=OutputType.COMBINED,
            reason="both requested"
        )
        
        actions = create_output_actions_pure(content, decision)
        
        assert len(actions) == 0  # 実際に内容がないため


class TestFilterOutputContentPure:
    """出力フィルタリング関数のテスト"""
    
    def test_filter_no_filters(self):
        """フィルタなしのテスト"""
        content = "Hello World Error"
        result, applied = filter_output_content_pure(content, [])
        
        assert result == "Hello World Error"
        assert applied is False
    
    def test_filter_single_pattern(self):
        """単一フィルタパターンのテスト"""
        content = "Hello World Error"
        result, applied = filter_output_content_pure(content, ["Error"])
        
        assert result == "Hello World "
        assert applied is True
    
    def test_filter_multiple_patterns(self):
        """複数フィルタパターンのテスト"""
        content = "Hello World Error Warning"
        result, applied = filter_output_content_pure(content, ["Error", "Warning"])
        
        assert result == "Hello World  "
        assert applied is True
    
    def test_filter_no_matches(self):
        """マッチなしフィルタのテスト"""
        content = "Hello World"
        result, applied = filter_output_content_pure(content, ["Error", "Warning"])
        
        assert result == "Hello World"
        assert applied is False
    
    def test_filter_empty_content(self):
        """空内容フィルタのテスト"""
        result, applied = filter_output_content_pure("", ["Error"])
        
        assert result == ""
        assert applied is False
    
    def test_filter_none_filters(self):
        """Noneフィルタのテスト"""
        content = "Hello World"
        result, applied = filter_output_content_pure(content, None)
        
        assert result == "Hello World"
        assert applied is False


class TestProcessMultipleOutputsPure:
    """複数出力処理関数のテスト"""
    
    def test_process_single_output(self):
        """単一出力処理のテスト"""
        request_info = RequestInfo(show_output=True)
        output_content = OutputContent(stdout="Hello", stderr="")
        
        result = process_multiple_outputs_pure([(request_info, output_content)])
        
        assert len(result.actions) == 1
        assert len(result.decisions) == 1
        assert result.summary["total_requests"] == 1
        assert result.summary["requests_with_output"] == 1
        assert result.summary["stdout_actions"] == 1
        assert result.summary["stderr_actions"] == 0
    
    def test_process_multiple_outputs(self):
        """複数出力処理のテスト"""
        requests_and_results = [
            (RequestInfo(show_output=True), OutputContent(stdout="Hello", stderr="")),
            (RequestInfo(show_output=True), OutputContent(stdout="", stderr="Error")),
            (RequestInfo(show_output=False), OutputContent(stdout="Hidden", stderr="")),
        ]
        
        result = process_multiple_outputs_pure(requests_and_results)
        
        assert len(result.decisions) == 3
        assert result.summary["total_requests"] == 3
        assert result.summary["requests_with_output"] == 3
        assert result.summary["stdout_actions"] == 1
        assert result.summary["stderr_actions"] == 1
    
    def test_process_with_global_filters(self):
        """グローバルフィルタ付き処理のテスト"""
        request_info = RequestInfo(show_output=True)
        output_content = OutputContent(stdout="Hello DEBUG World", stderr="Error DEBUG Info")
        
        result = process_multiple_outputs_pure(
            [(request_info, output_content)],
            global_filters=["DEBUG"]
        )
        
        assert len(result.actions) == 2
        assert result.decisions[0].filter_applied is True
        assert result.summary["filtered_outputs"] == 1
    
    def test_process_empty_list(self):
        """空リスト処理のテスト"""
        result = process_multiple_outputs_pure([])
        
        assert len(result.actions) == 0
        assert len(result.decisions) == 0
        assert result.summary["total_requests"] == 0
        assert result.summary["requests_with_output"] == 0


class TestAnalyzeOutputPatternsPure:
    """出力パターン分析関数のテスト"""
    
    def test_analyze_empty_outputs(self):
        """空出力リスト分析のテスト"""
        result = analyze_output_patterns_pure([])
        
        assert result["total_outputs"] == 0
        assert result["has_stdout"] == 0
        assert result["has_stderr"] == 0
        assert result["avg_stdout_length"] == 0
        assert result["avg_stderr_length"] == 0
        assert result["common_patterns"] == []
    
    def test_analyze_mixed_outputs(self):
        """混合出力分析のテスト"""
        outputs = [
            OutputContent(stdout="Hello World", stderr=""),
            OutputContent(stdout="", stderr="Error message"),
            OutputContent(stdout="Hello again", stderr="Warning"),
            OutputContent(stdout="", stderr=""),
        ]
        
        result = analyze_output_patterns_pure(outputs)
        
        assert result["total_outputs"] == 4
        assert result["has_stdout"] == 2
        assert result["has_stderr"] == 2
        assert result["avg_stdout_length"] > 0
        assert result["avg_stderr_length"] > 0
    
    def test_analyze_common_patterns(self):
        """共通パターン分析のテスト"""
        outputs = [
            OutputContent(stdout="Test line 1\nCommon pattern\n", stderr=""),
            OutputContent(stdout="Test line 2\nCommon pattern\n", stderr=""),
            OutputContent(stdout="Different content\nCommon pattern\n", stderr=""),
        ]
        
        result = analyze_output_patterns_pure(outputs)
        
        assert "Common pattern" in result["common_patterns"]
    
    def test_analyze_stdout_stderr_ratio(self):
        """標準出力/標準エラー比率分析のテスト"""
        outputs = [
            OutputContent(stdout="Hello", stderr=""),
            OutputContent(stdout="World", stderr=""),
            OutputContent(stdout="", stderr="Error"),
        ]
        
        result = analyze_output_patterns_pure(outputs)
        
        assert result["stdout_stderr_ratio"] == 2.0  # 2 stdout / 1 stderr
    
    def test_analyze_no_stderr_ratio(self):
        """標準エラーなし時の比率テスト"""
        outputs = [
            OutputContent(stdout="Hello", stderr=""),
            OutputContent(stdout="World", stderr=""),
        ]
        
        result = analyze_output_patterns_pure(outputs)
        
        assert result["stdout_stderr_ratio"] == float('inf')


class TestCreateOutputSummaryPure:
    """出力サマリー作成関数のテスト"""
    
    def test_create_empty_summary(self):
        """空サマリー作成のテスト"""
        result = create_output_summary_pure([])
        
        assert result["total_actions"] == 0
        assert result["by_type"] == {}
        assert result["total_content_length"] == 0
        assert result["content_sample"] == "not_included"
    
    def test_create_summary_with_actions(self):
        """アクション付きサマリー作成のテスト"""
        actions = [
            OutputAction("Hello World", OutputType.STDOUT, {}),
            OutputAction("Error", OutputType.STDERR, {}),
            OutputAction("Another message", OutputType.STDOUT, {}),
        ]
        
        result = create_output_summary_pure(actions)
        
        assert result["total_actions"] == 3
        assert result["by_type"]["stdout"]["count"] == 2
        assert result["by_type"]["stderr"]["count"] == 1
        assert result["total_content_length"] > 0
        assert result["avg_content_length"] > 0
    
    def test_create_summary_with_content_sample(self):
        """内容サンプル付きサマリー作成のテスト"""
        actions = [
            OutputAction("A" * 150, OutputType.STDOUT, {}),
        ]
        
        result = create_output_summary_pure(actions, include_content_sample=True)
        
        assert len(result["content_sample"]) <= 103  # 100文字 + "..."
        assert result["content_sample"].endswith("...")
    
    def test_create_summary_short_content(self):
        """短い内容のサマリー作成テスト"""
        actions = [
            OutputAction("Short", OutputType.STDOUT, {}),
        ]
        
        result = create_output_summary_pure(actions, include_content_sample=True)
        
        assert result["content_sample"] == "Short"


class TestOptimizeOutputDisplayPure:
    """出力表示最適化関数のテスト"""
    
    def test_optimize_empty_actions(self):
        """空アクション最適化のテスト"""
        result = optimize_output_display_pure([])
        
        assert result == []
    
    def test_optimize_with_deduplication(self):
        """重複除去最適化のテスト"""
        actions = [
            OutputAction("Hello", OutputType.STDOUT, {}),
            OutputAction("Hello", OutputType.STDOUT, {}),
            OutputAction("World", OutputType.STDOUT, {}),
        ]
        
        result = optimize_output_display_pure(actions, deduplicate=True)
        
        assert len(result) == 2
        unique_contents = {action.content for action in result}
        assert unique_contents == {"Hello", "World"}
    
    def test_optimize_with_length_limit(self):
        """長さ制限最適化のテスト"""
        actions = [
            OutputAction("Short", OutputType.STDOUT, {}),
            OutputAction("A" * 100, OutputType.STDOUT, {}),
        ]
        
        result = optimize_output_display_pure(actions, max_length=10)
        
        assert len(result) == 2
        assert result[0].content == "Short"
        assert len(result[1].content) <= 13  # 10文字 + "..."
        assert result[1].metadata["truncated"] is True
        assert result[1].metadata["original_length"] == 100
    
    def test_optimize_with_both_options(self):
        """重複除去と長さ制限の組み合わせテスト"""
        actions = [
            OutputAction("A" * 100, OutputType.STDOUT, {}),
            OutputAction("A" * 100, OutputType.STDOUT, {}),
            OutputAction("Short", OutputType.STDOUT, {}),
        ]
        
        result = optimize_output_display_pure(
            actions, 
            max_length=10,
            deduplicate=True
        )
        
        assert len(result) == 2  # 重複除去後
        truncated_action = next(a for a in result if a.metadata.get("truncated"))
        assert truncated_action is not None


class TestValidateOutputConfigurationPure:
    """出力設定検証関数のテスト"""
    
    def test_validate_valid_config(self):
        """有効な設定の検証テスト"""
        config = {
            "show_output": True,
            "filters": ["DEBUG", "INFO"],
            "max_length": 1000
        }
        
        is_valid, errors = validate_output_configuration_pure(config)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_missing_required_key(self):
        """必須キー欠如の検証テスト"""
        config = {
            "filters": ["DEBUG"]
        }
        
        is_valid, errors = validate_output_configuration_pure(config)
        
        assert is_valid is False
        assert any("show_output" in error for error in errors)
    
    def test_validate_invalid_show_output_type(self):
        """無効なshow_output型の検証テスト"""
        config = {
            "show_output": "true"  # 文字列（不正）
        }
        
        is_valid, errors = validate_output_configuration_pure(config)
        
        assert is_valid is False
        assert any("boolean" in error for error in errors)
    
    def test_validate_invalid_filters_type(self):
        """無効なfilters型の検証テスト"""
        config = {
            "show_output": True,
            "filters": "DEBUG,INFO"  # 文字列（不正）
        }
        
        is_valid, errors = validate_output_configuration_pure(config)
        
        assert is_valid is False
        assert any("list" in error for error in errors)
    
    def test_validate_invalid_filter_items(self):
        """無効なフィルタ項目の検証テスト"""
        config = {
            "show_output": True,
            "filters": ["DEBUG", 123, "INFO"]  # 数値含む（不正）
        }
        
        is_valid, errors = validate_output_configuration_pure(config)
        
        assert is_valid is False
        assert any("strings" in error for error in errors)
    
    def test_validate_invalid_max_length(self):
        """無効な最大長の検証テスト"""
        config = {
            "show_output": True,
            "max_length": -1  # 負の値（不正）
        }
        
        is_valid, errors = validate_output_configuration_pure(config)
        
        assert is_valid is False
        assert any("non-negative integer" in error for error in errors)
    
    def test_validate_minimal_config(self):
        """最小設定の検証テスト"""
        config = {
            "show_output": False
        }
        
        is_valid, errors = validate_output_configuration_pure(config)
        
        assert is_valid is True
        assert len(errors) == 0


class TestComplexScenarios:
    """複雑なシナリオのテスト"""
    
    def test_complete_output_workflow(self):
        """完全な出力処理ワークフローのテスト"""
        # 1. リクエスト情報と出力内容を準備
        request_info = RequestInfo(show_output=True, request_type="shell")
        output_content = OutputContent(stdout="Hello DEBUG World", stderr="Error INFO Message")
        
        # 2. フィルタリング
        filtered_stdout, _ = filter_output_content_pure(output_content.stdout, ["DEBUG"])
        filtered_stderr, _ = filter_output_content_pure(output_content.stderr, ["INFO"])
        
        filtered_content = OutputContent(stdout=filtered_stdout, stderr=filtered_stderr)
        
        # 3. 出力判定
        decision = should_show_output_pure(request_info, filtered_content)
        
        # 4. アクション作成
        actions = create_output_actions_pure(filtered_content, decision)
        
        # 5. 最適化
        optimized_actions = optimize_output_display_pure(actions, max_length=50)
        
        # 6. サマリー作成
        summary = create_output_summary_pure(optimized_actions)
        
        # 結果検証
        assert decision.should_show_stdout is True
        assert decision.should_show_stderr is True
        assert len(actions) == 2
        assert len(optimized_actions) >= 1
        assert summary["total_actions"] >= 1
    
    def test_batch_output_processing(self):
        """バッチ出力処理のテスト"""
        requests_and_results = [
            (RequestInfo(show_output=True), OutputContent(stdout="Success", stderr="")),
            (RequestInfo(show_output=True), OutputContent(stdout="", stderr="Error")),
            (RequestInfo(show_output=False), OutputContent(stdout="Hidden", stderr="")),
            (RequestInfo(show_output=True), OutputContent(stdout="Warning", stderr="Critical")),
        ]
        
        # 複数出力処理
        result = process_multiple_outputs_pure(requests_and_results, ["Hidden"])
        
        # パターン分析
        all_outputs = [content for _, content in requests_and_results]
        patterns = analyze_output_patterns_pure(all_outputs)
        
        # サマリー作成
        summary = create_output_summary_pure(result.actions)
        
        # 設定検証
        config = {"show_output": True, "filters": ["Hidden"]}
        is_valid, errors = validate_output_configuration_pure(config)
        
        # 結果検証
        assert result.summary["total_requests"] == 4
        assert patterns["total_outputs"] == 4
        assert summary["total_actions"] >= 1
        assert is_valid is True
    
    def test_error_resilience(self):
        """エラー耐性のテスト"""
        # 様々な問題のある入力でテスト
        problematic_inputs = [
            (RequestInfo(), OutputContent()),  # 空の内容
            (RequestInfo(show_output=True), OutputContent(stdout="A" * 10000)),  # 非常に長い出力
        ]
        
        for request_info, output_content in problematic_inputs:
            try:
                # すべての関数がエラーを適切に処理することを確認
                decision = should_show_output_pure(request_info, output_content)
                actions = create_output_actions_pure(output_content, decision)
                optimized = optimize_output_display_pure(actions, max_length=100)
                
                # 結果が返されることを確認（エラーで停止しない）
                assert decision.output_type is not None
                assert isinstance(actions, list)
                assert isinstance(optimized, list)
            except Exception as e:
                pytest.fail(f"Function should handle problematic input gracefully: {e}")
    
    def test_filter_edge_cases(self):
        """フィルタエッジケースのテスト"""
        edge_cases = [
            ("", []),
            ("text", []),
            ("", ["filter"]),
            ("text", [""]),
            ("same same same", ["same"]),
        ]
        
        for content, filters in edge_cases:
            try:
                result, applied = filter_output_content_pure(content, filters)
                assert isinstance(result, str)
                assert isinstance(applied, bool)
            except Exception as e:
                pytest.fail(f"Filter should handle edge case gracefully: {e}")