"""Tests for step_runner module - step execution and template expansion"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.domain.step_runner import (
    expand_template,
    evaluate_test_condition,
    expand_step_with_file_patterns,
    create_step,
    expand_when_condition,
    ExecutionContext,
    _contains_template_variables,
    get_file_patterns_from_context,
    expand_file_patterns_to_files,
    expand_file_patterns_in_text,
    run_steps
)


class TestStepRunner:
    """Test suite for step runner functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_os_provider = Mock()
        self.mock_json_provider = Mock()
        self.execution_context = ExecutionContext(
            contest_name="ABC100",
            problem_name="A",
            language="python",
            local_workspace_path="/workspace",
            contest_current_path="/contest/current",
            contest_stock_path="/contest/stock",
            contest_template_path="/contest/template",
            source_file_name="main.py",
            language_id="py",
            env_type=None,
            run_command=None,
            contest_files=None,
            test_files=None,
            build_files=None,
            file_patterns=None
        )
    
    def test_contains_template_variables(self):
        """Test detection of template variables"""
        assert _contains_template_variables("Hello {name}!") is True
        assert _contains_template_variables("No templates here") is False
        assert _contains_template_variables("{var1} and {var2}") is True
        assert _contains_template_variables("") is False
    
    def test_expand_template_with_execution_context(self):
        """Test template expansion with ExecutionContext"""
        template = "Contest: {contest_name}, Problem: {problem_name}"
        
        result = expand_template(template, self.execution_context)
        
        assert result == "Contest: ABC100, Problem: A"
    
    def test_expand_template_with_dict_context(self):
        """Test template expansion with dictionary context"""
        template = "{greeting} {name}!"
        context = MagicMock(spec=['to_dict'])
        context.to_dict.return_value = {"greeting": "Hello", "name": "World"}
        
        result = expand_template(template, context)
        
        assert result == "Hello World!"
    
    def test_expand_template_empty_string(self):
        """Test template expansion with empty string"""
        result = expand_template("", self.execution_context)
        assert result == ""
    
    def test_expand_template_no_variables(self):
        """Test template expansion with no variables"""
        template = "Just plain text"
        result = expand_template(template, self.execution_context)
        assert result == "Just plain text"
    
    def test_evaluate_test_condition_directory_exists(self):
        """Test evaluation of directory existence condition"""
        self.mock_os_provider.isdir.return_value = True
        
        result, error = evaluate_test_condition("test -d /some/path", self.mock_os_provider)
        
        assert result is True
        assert error is None
        self.mock_os_provider.isdir.assert_called_once_with("/some/path")
    
    def test_evaluate_test_condition_file_exists(self):
        """Test evaluation of file existence condition"""
        self.mock_os_provider.isfile.return_value = True
        
        result, error = evaluate_test_condition("-f /some/file.txt", self.mock_os_provider)
        
        assert result is True
        assert error is None
        self.mock_os_provider.isfile.assert_called_once_with("/some/file.txt")
    
    def test_evaluate_test_condition_path_exists(self):
        """Test evaluation of path existence condition"""
        self.mock_os_provider.path_exists.return_value = False
        
        result, error = evaluate_test_condition("test -e /nonexistent", self.mock_os_provider)
        
        assert result is False
        assert error is None
        self.mock_os_provider.path_exists.assert_called_once_with("/nonexistent")
    
    def test_evaluate_test_condition_negation(self):
        """Test evaluation of negated condition"""
        self.mock_os_provider.isdir.return_value = False
        
        result, error = evaluate_test_condition("test ! -d /not/a/dir", self.mock_os_provider)
        
        assert result is True
        assert error is None
        self.mock_os_provider.isdir.assert_called_once_with("/not/a/dir")
    
    def test_evaluate_test_condition_empty(self):
        """Test evaluation of empty condition"""
        result, error = evaluate_test_condition("", self.mock_os_provider)
        
        assert result is True
        assert error is None
    
    def test_evaluate_test_condition_invalid(self):
        """Test evaluation of invalid condition"""
        result, error = evaluate_test_condition("invalid condition", self.mock_os_provider)
        
        assert result is False
        assert "test条件は 'test' で始まる必要があります" in error
    
    def test_expand_when_condition_true(self):
        """Test when condition expansion and evaluation"""
        self.mock_os_provider.isdir.return_value = True
        
        result, error = expand_when_condition(
            "test -d {contest_current_path}", 
            self.execution_context,
            self.mock_os_provider
        )
        
        assert result is True
        assert error is None
        self.mock_os_provider.isdir.assert_called_once_with("/contest/current")
    
    def test_expand_when_condition_false(self):
        """Test when condition that evaluates to false"""
        self.mock_os_provider.isfile.return_value = False
        
        result, error = expand_when_condition(
            "test -f {source_file_name}",
            self.execution_context,
            self.mock_os_provider
        )
        
        assert result is False
        assert error is None
    
    def test_expand_step_with_file_patterns_no_patterns(self):
        """Test step expansion when no file patterns present"""
        json_step = {
            "name": "simple_step",
            "cmd": "echo 'hello'"
        }
        
        result = expand_step_with_file_patterns(
            json_step, 
            self.execution_context,
            self.mock_json_provider,
            self.mock_os_provider
        )
        
        assert len(result) == 1
        assert result[0] == json_step
    
    def test_expand_step_with_file_patterns_contest_files(self):
        """Test step expansion with contest_files pattern"""
        json_step = {
            "name": "process_files",
            "cmd": "process {contest_files}"
        }
        
        # Mock file pattern resolution
        with patch('src.domain.step_runner.get_file_patterns_from_context') as mock_get_patterns:
            mock_get_patterns.return_value = ["*.in", "*.txt"]
            
            with patch('src.domain.step_runner.expand_file_patterns_to_files') as mock_expand:
                mock_expand.return_value = ["test1.in", "test2.txt"]
                
                result = expand_step_with_file_patterns(
                    json_step,
                    self.execution_context,
                    self.mock_json_provider,
                    self.mock_os_provider
                )
        
        assert len(result) == 2
        assert result[0]["cmd"] == "process test1.in"
        assert result[1]["cmd"] == "process test2.txt"
    
    @patch('src.domain.step_runner.StepType')
    @patch('src.domain.step_runner.resolve_best')
    def test_create_step_basic(self, mock_resolve_best, mock_step_type):
        """Test basic step creation"""
        json_step = {
            "name": "test_step",
            "type": "python",
            "cmd": ["python", "main.py"]
        }
        
        # Mock config defaults
        mock_defaults_node = Mock()
        mock_defaults_node.value = {
            "name": None,
            "allow_failure": False,
            "show_output": True,
            "max_workers": 1,
            "cwd": None,
            "when": None,
            "output_format": None,
            "format_preset": None,
            "force_env_type": None,
            "format_options": None
        }
        mock_resolve_best.return_value = mock_defaults_node
        
        # Mock config_root on context with next_nodes attribute
        mock_config_root = Mock()
        mock_config_root.next_nodes = []
        self.execution_context.config_root = mock_config_root
        
        mock_step_type.PYTHON = "python"
        
        with patch('src.domain.step_runner.Step') as mock_step_class:
            mock_step = Mock()
            mock_step_class.return_value = mock_step
            
            result = create_step(
                json_step,
                self.execution_context
            )
            
            assert result == mock_step
            mock_step_class.assert_called_once()
    
    @patch('src.domain.step_runner.resolve_best')
    def test_create_step_with_when_condition_false(self, mock_resolve_best):
        """Test step creation with when condition - condition is stored but not evaluated during creation"""
        json_step = {
            "name": "conditional_step",
            "type": "shell",
            "cmd": ["echo", "should not run"],
            "when": "test -d /nonexistent",
            "allow_failure": False,
            "show_output": True
        }
        
        # Mock config defaults
        mock_defaults_node = Mock()
        mock_defaults_node.value = {
            "name": None,
            "allow_failure": False,
            "show_output": True,
            "max_workers": 1,
            "cwd": None,
            "when": None,
            "output_format": None,
            "format_preset": None,
            "force_env_type": None,
            "format_options": None
        }
        mock_resolve_best.return_value = mock_defaults_node
        
        # Mock config_root on context with next_nodes attribute
        mock_config_root = Mock()
        mock_config_root.next_nodes = []
        self.execution_context.config_root = mock_config_root
        
        result = create_step(
            json_step,
            self.execution_context
        )
        
        # Step is created with when condition stored
        assert result is not None
        assert result.when == "test -d /nonexistent"
        assert result.name == "conditional_step"
    
    def test_execution_context_to_dict(self):
        """Test ExecutionContext conversion to dictionary"""
        context_dict = self.execution_context.to_dict()
        
        assert context_dict["contest_name"] == "ABC100"
        assert context_dict["problem_name"] == "A"
        assert context_dict["language"] == "python"
        assert context_dict["language_name"] == "python"  # Alias for backward compatibility
        assert context_dict["local_workspace_path"] == "/workspace"
    
    def test_execution_context_to_dict_with_file_patterns(self):
        """Test ExecutionContext conversion with file patterns"""
        # file_patternsがある場合のテスト
        context = ExecutionContext(
            contest_name="ABC100",
            problem_name="A",
            language="python",
            local_workspace_path="/workspace",
            contest_current_path="/contest/current",
            contest_stock_path=None,
            contest_template_path=None,
            source_file_name=None,
            language_id=None,
            env_type=None,
            run_command=None,
            contest_files=None,
            test_files=None,
            build_files=None,
            file_patterns={
                "test_pattern": ["test/*.in"],
                "build_pattern": ["build/output"]
            }
        )
        
        context_dict = context.to_dict()
        
        # ディレクトリ部分のみが抽出されることを確認
        assert context_dict["test_pattern"] == "test"
        assert context_dict["build_pattern"] == "build/output"  # /がない場合はそのまま
    
    def test_expand_template_with_resolve_formatted_string(self):
        """Test template expansion with TypeSafeConfigNodeManager"""
        template = "{greeting} {name}!"
        context = Mock(spec=['resolve_formatted_string'])
        context.resolve_formatted_string.return_value = "Hello World!"
        
        result = expand_template(template, context)
        
        assert result == "Hello World!"
        context.resolve_formatted_string.assert_called_once_with(template)
    
    def test_expand_template_with_resolve_formatted_string_error(self):
        """Test template expansion error with TypeSafeConfigNodeManager"""
        template = "{invalid}"
        context = Mock(spec=['resolve_formatted_string'])
        context.resolve_formatted_string.side_effect = Exception("Invalid key")
        
        with pytest.raises(ValueError, match=r"テンプレート解決エラー \(resolve_formatted_string\)"):
            expand_template(template, context)
    
    def test_expand_template_with_format_string(self):
        """Test template expansion with ExecutionContextAdapter"""
        template = "{contest} {problem}"
        context = Mock(spec=['format_string'])
        context.format_string.return_value = "ABC100 A"
        
        result = expand_template(template, context)
        
        assert result == "ABC100 A"
        context.format_string.assert_called_once_with(template)
    
    def test_expand_template_with_format_string_error(self):
        """Test template expansion error with ExecutionContextAdapter"""
        template = "{invalid}"
        context = Mock(spec=['format_string'])
        context.format_string.side_effect = Exception("Format error")
        
        with pytest.raises(ValueError, match=r"テンプレート解決エラー \(format_string\)"):
            expand_template(template, context)
    
    def test_expand_template_with_none_value(self):
        """Test template expansion with None value in context"""
        template = "{value}"
        context = Mock(spec=['to_dict'])
        context.to_dict.return_value = {"value": None}
        
        with pytest.raises(ValueError, match="Value for key 'value' is None"):
            expand_template(template, context)
    
    def test_expand_template_with_to_format_dict(self):
        """Test template expansion with StepContext (to_format_dict)"""
        template = "{contest_name} - {problem_name}"
        context = Mock(spec=['to_format_dict'])
        context.to_format_dict.return_value = {
            "contest_name": "ABC200",
            "problem_name": "B"
        }
        
        result = expand_template(template, context)
        
        assert result == "ABC200 - B"
    
    def test_expand_template_with_to_format_dict_none_value(self):
        """Test template expansion error with None in to_format_dict"""
        template = "{missing}"
        context = Mock(spec=['to_format_dict'])
        context.to_format_dict.return_value = {"missing": None}
        
        with pytest.raises(ValueError, match="Value for key 'missing' is None"):
            expand_template(template, context)
    
    def test_expand_template_with_generic_context(self):
        """Test template expansion with generic context object"""
        template = "{contest_name}/{problem_name}.{language}"
        
        # 汎用的なコンテキストオブジェクト
        class GenericContext:
            def __init__(self):
                self.contest_name = "ABC300"
                self.problem_name = "C"
                self.language = "cpp"
                self.contest_files = ["*.in", "*.out"]
                self.test_files = ["test/*.txt"]
                self.build_files = ["build/*"]
        
        context = GenericContext()
        result = expand_template(template, context)
        
        assert result == "ABC300/C.cpp"
    
    def test_evaluate_test_condition_negation_file(self):
        """Test evaluation of negated file condition"""
        self.mock_os_provider.isfile.return_value = True
        
        result, error = evaluate_test_condition("test ! -f /existing.txt", self.mock_os_provider)
        
        assert result is False
        assert error is None
        self.mock_os_provider.isfile.assert_called_once_with("/existing.txt")
    
    def test_evaluate_test_condition_negation_exists(self):
        """Test evaluation of negated exists condition"""
        self.mock_os_provider.path_exists.return_value = False
        
        result, error = evaluate_test_condition("test ! -e /missing", self.mock_os_provider)
        
        assert result is True
        assert error is None
        self.mock_os_provider.path_exists.assert_called_once_with("/missing")
    
    def test_expand_when_condition_empty(self):
        """Test when condition with empty string"""
        result, error = expand_when_condition("", self.execution_context, self.mock_os_provider)
        
        assert result is True
        assert error is None
    
    def test_expand_step_with_file_patterns_empty_patterns(self):
        """Test step expansion when file patterns return empty list"""
        json_step = {
            "name": "process_files",
            "cmd": ["process", "{test_files}"]
        }
        
        with patch('src.domain.step_runner.get_file_patterns_from_context') as mock_get_patterns:
            mock_get_patterns.return_value = []
            
            result = expand_step_with_file_patterns(
                json_step,
                self.execution_context,
                self.mock_json_provider,
                self.mock_os_provider
            )
        
        assert len(result) == 1
        assert result[0] == json_step
    
    def test_expand_step_with_file_patterns_no_actual_files(self):
        """Test step expansion when no actual files match patterns"""
        json_step = {
            "name": "process_files",
            "cmd": ["process", "{build_files}"]
        }
        
        with patch('src.domain.step_runner.get_file_patterns_from_context') as mock_get_patterns:
            mock_get_patterns.return_value = ["*.nonexistent"]
            
            with patch('src.domain.step_runner.expand_file_patterns_to_files') as mock_expand:
                mock_expand.return_value = []
                
                result = expand_step_with_file_patterns(
                    json_step,
                    self.execution_context,
                    self.mock_json_provider,
                    self.mock_os_provider
                )
        
        assert len(result) == 1
        assert result[0] == json_step
    
    def test_expand_step_with_file_patterns_cmd_list(self):
        """Test step expansion with command as list"""
        json_step = {
            "name": "multi_arg_command",
            "cmd": ["python", "script.py", "--file", "{test_files}"]
        }
        
        with patch('src.domain.step_runner.get_file_patterns_from_context') as mock_get_patterns:
            mock_get_patterns.return_value = ["*.test"]
            
            with patch('src.domain.step_runner.expand_file_patterns_to_files') as mock_expand:
                mock_expand.return_value = ["file1.test", "file2.test"]
                
                result = expand_step_with_file_patterns(
                    json_step,
                    self.execution_context,
                    self.mock_json_provider,
                    self.mock_os_provider
                )
        
        assert len(result) == 2
        assert result[0]["cmd"] == ["python", "script.py", "--file", "file1.test"]
        assert result[1]["cmd"] == ["python", "script.py", "--file", "file2.test"]
    
    def test_get_file_patterns_from_context_direct_attribute(self):
        """Test getting file patterns from context attribute"""
        context = Mock()
        context.contest_files = ["*.cpp", "*.h"]
        
        result = get_file_patterns_from_context(context, "contest_files", self.mock_json_provider)
        
        assert result == ["*.cpp", "*.h"]
    
    def test_get_file_patterns_from_context_string_attribute(self):
        """Test getting file patterns when attribute is string"""
        context = Mock()
        context.test_files = "*.test"
        
        result = get_file_patterns_from_context(context, "test_files", self.mock_json_provider)
        
        assert result == ["*.test"]
    
    def test_get_file_patterns_from_context_with_root_node(self):
        """Test getting file patterns from TypeSafeConfigNodeManager"""
        context = Mock()
        context.contest_files = None  # No direct attribute
        
        # Mock root node structure
        mock_node = Mock()
        mock_node.value = ["*.in", "*.out"]
        context._root_node = Mock()
        
        with patch('src.domain.step_runner.resolve_best') as mock_resolve:
            mock_resolve.return_value = mock_node
            
            result = get_file_patterns_from_context(context, "contest_files", self.mock_json_provider)
            
            assert result == ["*.in", "*.out"]
            mock_resolve.assert_called_once_with(context._root_node, ['files', 'contest_files'])
    
    def test_get_file_patterns_from_context_root_node_string(self):
        """Test getting file patterns from root node when value is string"""
        context = Mock()
        context.build_files = None
        
        mock_node = Mock()
        mock_node.value = "build/*"
        context._root_node = Mock()
        
        with patch('src.domain.step_runner.resolve_best') as mock_resolve:
            mock_resolve.return_value = mock_node
            
            result = get_file_patterns_from_context(context, "build_files", self.mock_json_provider)
            
            assert result == ["build/*"]
    
    def test_get_file_patterns_from_context_not_found(self):
        """Test error when file patterns not found"""
        context = Mock()
        context.unknown_pattern = None
        
        with pytest.raises(ValueError, match="ファイルパターン 'unknown_pattern' が見つかりません"):
            get_file_patterns_from_context(context, "unknown_pattern", self.mock_json_provider)
    
    def test_expand_file_patterns_to_files_glob(self):
        """Test expanding glob patterns to actual files"""
        patterns = ["*.py", "test/*.txt"]
        
        self.mock_os_provider.glob.side_effect = [
            ["main.py", "utils.py"],
            ["test/input.txt", "test/output.txt"]
        ]
        
        result = expand_file_patterns_to_files(patterns, self.mock_os_provider)
        
        assert result == ["main.py", "test/input.txt", "test/output.txt", "utils.py"]
        assert self.mock_os_provider.glob.call_count == 2
    
    def test_expand_file_patterns_to_files_no_glob_method(self):
        """Test expanding patterns when os_provider has no glob method"""
        patterns = ["*.md"]
        os_provider = Mock(spec=[])  # No glob method
        
        with patch('glob.glob') as mock_glob:
            mock_glob.return_value = ["README.md", "CONTRIBUTING.md"]
            
            result = expand_file_patterns_to_files(patterns, os_provider)
            
            assert result == ["CONTRIBUTING.md", "README.md"]
            mock_glob.assert_called_once_with("*.md")
    
    def test_expand_file_patterns_to_files_plain_files(self):
        """Test expanding patterns with plain file names"""
        patterns = ["file1.txt", "file2.txt", "file1.txt"]  # Duplicate
        
        result = expand_file_patterns_to_files(patterns, self.mock_os_provider)
        
        # Duplicates removed and sorted
        assert result == ["file1.txt", "file2.txt"]
    
    def test_create_step_missing_cmd(self):
        """Test step creation with missing cmd field"""
        json_step = {
            "name": "invalid_step",
            "type": "shell"
        }
        
        with pytest.raises(ValueError, match="'cmd'フィールドが必須です"):
            create_step(json_step, self.execution_context)
    
    def test_create_step_missing_type(self):
        """Test step creation with missing type field"""
        json_step = {
            "name": "invalid_step",
            "cmd": ["echo", "test"]
        }
        
        with pytest.raises(ValueError, match="'type'フィールドが必須です"):
            create_step(json_step, self.execution_context)
    
    def test_create_step_no_config(self):
        """Test step creation when config is not available"""
        json_step = {
            "name": "test_step",
            "type": "shell",
            "cmd": ["echo", "test"]
        }
        
        # No config_root on context
        self.execution_context.config_root = None
        
        with pytest.raises(ValueError, match="ステップのデフォルト値が設定ファイルから取得できません"):
            create_step(json_step, self.execution_context)
    
    def test_expand_file_patterns_in_text_basic(self):
        """Test expanding file patterns in text"""
        text = "Process {contest_files} and {test_files}"
        file_patterns = {
            "contest_files": ["*.cpp"],
            "test_files": ["test/*.in"]
        }
        
        # Mock StepType
        mock_step_type = Mock()
        
        result = expand_file_patterns_in_text(text, file_patterns, mock_step_type)
        
        assert result == "Process *.cpp and test/*.in"
    
    def test_expand_file_patterns_in_text_directory_extraction(self):
        """Test directory extraction for tree operations"""
        text = "Move {test_files} to output"
        file_patterns = {
            "test_files": ["test/*.txt"]
        }
        
        # StepTypeをインポート
        from src.domain.step import StepType
        
        # MOVETREE操作でのディレクトリ抽出をテスト
        result = expand_file_patterns_in_text(text, file_patterns, StepType.MOVETREE)
        
        assert result == "Move test to output"
    
    def test_expand_file_patterns_in_text_empty_patterns(self):
        """Test with empty pattern list"""
        text = "Process {build_files}"
        file_patterns = {
            "build_files": []
        }
        
        result = expand_file_patterns_in_text(text, file_patterns, Mock())
        
        # Pattern not replaced when list is empty
        assert result == "Process {build_files}"
    
    def test_run_steps_success(self):
        """Test successful execution of steps"""
        steps_data = [
            {
                "name": "step1",
                "type": "shell",
                "cmd": ["echo", "test1"]
            },
            {
                "name": "step2",
                "type": "python",
                "cmd": ["python", "script.py"]
            }
        ]
        
        with patch('src.domain.step_runner.expand_step_with_file_patterns') as mock_expand:
            # Return unchanged steps
            mock_expand.side_effect = lambda step, *args: [step]
            
            with patch('src.domain.step_runner.create_step') as mock_create:
                mock_step1 = Mock()
                mock_step2 = Mock()
                mock_create.side_effect = [mock_step1, mock_step2]
                
                result = run_steps(
                    steps_data,
                    self.execution_context,
                    self.mock_os_provider,
                    self.mock_json_provider
                )
        
        assert len(result) == 2
        assert result[0] == mock_step1
        assert result[1] == mock_step2
    
    def test_run_steps_with_expansion(self):
        """Test run_steps with file pattern expansion"""
        steps_data = [
            {
                "name": "process_files",
                "type": "shell",
                "cmd": ["process", "{test_files}"]
            }
        ]
        
        expanded_steps = [
            {"name": "process_files", "type": "shell", "cmd": ["process", "file1.txt"]},
            {"name": "process_files", "type": "shell", "cmd": ["process", "file2.txt"]}
        ]
        
        with patch('src.domain.step_runner.expand_step_with_file_patterns') as mock_expand:
            mock_expand.return_value = expanded_steps
            
            with patch('src.domain.step_runner.create_step') as mock_create:
                mock_step1 = Mock()
                mock_step2 = Mock()
                mock_create.side_effect = [mock_step1, mock_step2]
                
                result = run_steps(
                    steps_data,
                    self.execution_context,
                    self.mock_os_provider,
                    self.mock_json_provider
                )
        
        assert len(result) == 2
        assert result[0] == mock_step1
        assert result[1] == mock_step2
    
    def test_run_steps_with_error(self):
        """Test run_steps with step creation error"""
        steps_data = [
            {
                "name": "good_step",
                "type": "shell",
                "cmd": ["echo", "ok"]
            },
            {
                "name": "bad_step",
                # Missing required fields
            }
        ]
        
        with patch('src.domain.step_runner.expand_step_with_file_patterns') as mock_expand:
            mock_expand.side_effect = lambda step, *args: [step]
            
            with patch('src.domain.step_runner.create_step') as mock_create:
                mock_step1 = Mock()
                mock_create.side_effect = [
                    mock_step1,
                    ValueError("Missing required field")
                ]
                
                result = run_steps(
                    steps_data,
                    self.execution_context,
                    self.mock_os_provider,
                    self.mock_json_provider
                )
        
        assert len(result) == 2
        assert result[0] == mock_step1
        # Error result object
        assert hasattr(result[1], 'success')
        assert result[1].success is False
        assert result[1].error_message == "Missing required field"
        assert result[1].step is None