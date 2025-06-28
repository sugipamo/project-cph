"""ステップ生成サービスのテスト"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List

from src.domain.services.step_generation_service import (
    create_step_context_from_execution_context,
    execution_context_to_simple_context,
    generate_steps_from_json,
    create_step_from_json,
    format_template,
    expand_file_patterns,
    validate_step_sequence,
    validate_single_step,
    optimize_step_sequence
)
from src.domain.step import Step, StepType, StepContext
from src.domain.step_runner import ExecutionContext


# ヘルパー関数：テスト用の完全なStepを作成
def create_test_step(step_type: StepType, cmd: List[str], **kwargs) -> Step:
    """テスト用のStepオブジェクトを作成"""
    defaults = {
        'allow_failure': False,
        'show_output': True,
        'cwd': None,
        'force_env_type': None,
        'format_options': None,
        'output_format': None,
        'format_preset': None,
        'when': None,
        'name': None,
        'auto_generated': False,
        'max_workers': 1
    }
    defaults.update(kwargs)
    return Step(type=step_type, cmd=cmd, **defaults)


class TestCreateStepContextFromExecutionContext:
    """create_step_context_from_execution_contextのテスト"""

    def test_with_file_patterns_attribute(self):
        """file_patterns属性を持つ実行コンテキストの変換"""
        execution_context = Mock()
        execution_context.file_patterns = {"source": "*.py", "test": "*_test.py"}
        execution_context.contest_name = "abc123"
        execution_context.problem_name = "a"
        execution_context.language = "python3"
        execution_context.env_type = "local"
        execution_context.command_type = "run"
        execution_context.local_workspace_path = "/workspace"
        execution_context.contest_current_path = "/contest/current"
        execution_context.contest_stock_path = "/contest/stock"
        execution_context.contest_template_path = "/contest/template"
        execution_context.contest_temp_path = "/contest/temp"
        execution_context.source_file_name = "main.py"
        execution_context.language_id = "py3"

        result = create_step_context_from_execution_context(execution_context)

        assert isinstance(result, StepContext)
        assert result.contest_name == "abc123"
        assert result.problem_name == "a"
        assert result.language == "python3"
        assert result.file_patterns == {"source": "*.py", "test": "*_test.py"}

    def test_with_env_json_language_config(self):
        """env_jsonから言語固有設定を取得するケース"""
        execution_context = Mock()
        execution_context.env_json = {
            "python3": {
                "file_patterns": {
                    "source": {"workspace": "src/*.py"},
                    "test": {"contest_current": "tests/*.py"}
                }
            }
        }
        execution_context.language = "python3"
        execution_context.contest_name = "abc123"
        execution_context.problem_name = "b"
        execution_context.env_type = "local"
        execution_context.command_type = "test"
        execution_context.local_workspace_path = "/workspace"
        execution_context.contest_current_path = "/contest/current"
        execution_context.source_file_name = "solution.py"
        execution_context.language_id = "py3"
        
        # file_patterns属性がないことを明示
        del execution_context.file_patterns

        result = create_step_context_from_execution_context(execution_context)

        assert result.file_patterns == {"source": "src/*.py", "test": "tests/*.py"}

    def test_with_env_json_root_config(self):
        """env_jsonのルートレベル設定を使用するケース"""
        execution_context = Mock()
        execution_context.env_json = {
            "file_patterns": {
                "source": {"contest_stock": "stock/*.cpp"},
                "header": "include/*.h"
            }
        }
        execution_context.language = "cpp"  # env_jsonに存在しない言語
        execution_context.contest_name = "arc100"
        execution_context.problem_name = "c"
        execution_context.env_type = "docker"
        execution_context.command_type = "build"
        execution_context.local_workspace_path = "/workspace"
        execution_context.contest_current_path = "/contest/current"
        execution_context.source_file_name = "main.cpp"
        execution_context.language_id = "cpp17"
        
        del execution_context.file_patterns

        result = create_step_context_from_execution_context(execution_context)

        assert result.file_patterns == {"source": "stock/*.cpp", "header": "include/*.h"}

    def test_without_file_patterns(self):
        """file_patternsがない場合"""
        execution_context = Mock()
        execution_context.contest_name = "agc001"
        execution_context.problem_name = "d"
        execution_context.language = "java"
        execution_context.env_type = "local"
        execution_context.command_type = "submit"
        execution_context.local_workspace_path = "/workspace"
        execution_context.contest_current_path = "/contest/current"
        execution_context.source_file_name = "Main.java"
        execution_context.language_id = "java8"
        
        del execution_context.file_patterns
        execution_context.env_json = None

        result = create_step_context_from_execution_context(execution_context)

        assert result.file_patterns is None

    def test_with_missing_optional_attributes(self):
        """オプション属性が欠けている場合"""
        execution_context = Mock()
        execution_context.contest_name = "practice"
        execution_context.problem_name = "a"
        execution_context.language = "python3"
        execution_context.env_type = "local"
        execution_context.command_type = "run"
        
        # 必須属性のみ設定
        del execution_context.file_patterns
        execution_context.env_json = None
        del execution_context.local_workspace_path
        del execution_context.contest_current_path
        del execution_context.contest_stock_path
        del execution_context.contest_template_path
        del execution_context.contest_temp_path
        del execution_context.source_file_name
        del execution_context.language_id

        result = create_step_context_from_execution_context(execution_context)

        assert result.local_workspace_path == ""
        assert result.contest_current_path == ""
        assert result.contest_stock_path is None
        assert result.source_file_name is None


class TestExecutionContextToSimpleContext:
    """execution_context_to_simple_contextのテスト"""

    def test_standard_conversion(self):
        """標準的な実行コンテキストの変換"""
        execution_context = Mock()
        execution_context.contest_name = "abc200"
        execution_context.problem_name = "e"
        execution_context.language = "python3"
        execution_context.local_workspace_path = "/home/user/workspace"
        execution_context.contest_current_path = "/home/user/contest/current"
        execution_context.contest_stock_path = "/home/user/contest/stock"
        execution_context.contest_template_path = "/home/user/contest/template"
        execution_context.source_file_name = "solve.py"
        execution_context.language_id = "py3"
        execution_context.run_command = "python3 {source}"
        execution_context.file_patterns = {"source": "*.py"}

        result = execution_context_to_simple_context(execution_context)

        assert isinstance(result, ExecutionContext)
        assert result.contest_name == "abc200"
        assert result.problem_name == "e"
        assert result.run_command == "python3 {source}"
        assert result.file_patterns == {"source": "*.py"}

    def test_run_command_from_env_json(self):
        """env_jsonからrun_commandを取得"""
        execution_context = Mock()
        execution_context.contest_name = "abc100"
        execution_context.problem_name = "f"
        execution_context.language = "cpp"
        execution_context.local_workspace_path = "/workspace"
        execution_context.contest_current_path = "/contest"
        execution_context.source_file_name = "main.cpp"
        execution_context.language_id = "cpp17"
        execution_context.env_json = {
            "cpp": {
                "run_command": "g++ -o main {source} && ./main",
                "file_patterns": {"source": "*.cpp"}
            }
        }
        
        del execution_context.file_patterns
        del execution_context.run_command

        result = execution_context_to_simple_context(execution_context)

        assert result.run_command == "g++ -o main {source} && ./main"

    def test_run_command_from_config(self):
        """config.runtime_configからrun_commandを取得"""
        execution_context = Mock()
        execution_context.contest_name = "arc120"
        execution_context.problem_name = "g"
        execution_context.language = "rust"
        execution_context.local_workspace_path = "/workspace"
        execution_context.contest_current_path = "/contest"
        execution_context.source_file_name = "main.rs"
        execution_context.language_id = "rust"
        execution_context.config = Mock()
        execution_context.config.runtime_config = Mock()
        execution_context.config.runtime_config.run_command = "cargo run"
        execution_context.env_json = None
        
        del execution_context.file_patterns
        del execution_context.run_command

        result = execution_context_to_simple_context(execution_context)

        assert result.run_command == "cargo run"

    def test_default_run_command(self):
        """デフォルトのrun_commandを使用"""
        execution_context = Mock()
        execution_context.contest_name = "agc050"
        execution_context.problem_name = "h"
        execution_context.language = "unknown"
        execution_context.local_workspace_path = "/workspace"
        execution_context.contest_current_path = "/contest"
        execution_context.source_file_name = "solution.txt"
        execution_context.language_id = "unknown"
        execution_context.env_json = None
        
        del execution_context.file_patterns
        del execution_context.run_command
        del execution_context.config

        result = execution_context_to_simple_context(execution_context)

        assert result.run_command == "python3"

    def test_with_missing_attributes(self):
        """属性が欠けている場合のフォールバック"""
        execution_context = Mock()
        execution_context.contest_name = "practice2"
        execution_context.problem_name = "b"
        execution_context.language = "python3"
        execution_context.env_json = None
        
        # 欠けている属性
        del execution_context.local_workspace_path
        del execution_context.contest_current_path
        del execution_context.contest_stock_path
        del execution_context.contest_template_path
        del execution_context.source_file_name
        del execution_context.language_id
        del execution_context.file_patterns
        del execution_context.run_command
        del execution_context.config

        result = execution_context_to_simple_context(execution_context)

        assert result.local_workspace_path == ""
        assert result.contest_current_path == ""
        assert result.contest_stock_path == ""
        assert result.run_command == "python3"


class TestGenerateStepsFromJson:
    """generate_steps_from_jsonのテスト"""

    def test_successful_generation(self):
        """正常なステップ生成"""
        json_steps = [
            {"type": "mkdir", "cmd": ["/tmp/test"]},
            {"type": "touch", "cmd": ["/tmp/test/file.txt"]}
        ]
        context = Mock()
        context.contest_name = "abc300"
        context.problem_name = "a"
        context.language = "python3"
        context.local_workspace_path = "/workspace"
        context.contest_current_path = "/contest"
        context.source_file_name = "main.py"
        context.language_id = "py3"
        context.file_patterns = {}
        context.run_command = "python3"
        
        os_provider = Mock()
        json_provider = Mock()
        
        # run_stepsのモック結果
        mock_steps = [
            create_test_step(StepType.MKDIR, ["/tmp/test"]),
            create_test_step(StepType.TOUCH, ["/tmp/test/file.txt"])
        ]
        
        with patch("src.domain.services.step_generation_service.run_steps") as mock_run_steps:
            mock_run_steps.return_value = mock_steps
            
            result = generate_steps_from_json(json_steps, context, os_provider, json_provider)

        assert len(result.steps) == 2
        assert result.steps[0].type == StepType.MKDIR
        assert result.steps[1].type == StepType.TOUCH
        assert len(result.errors) == 0

    def test_with_errors(self):
        """エラーが発生した場合"""
        json_steps = [
            {"type": "invalid", "cmd": ["test"]}
        ]
        context = Mock()
        context.contest_name = "abc300"
        context.problem_name = "b"
        context.language = "python3"
        context.local_workspace_path = "/workspace"
        context.contest_current_path = "/contest"
        context.source_file_name = "main.py"
        context.language_id = "py3"
        context.file_patterns = {}
        context.run_command = "python3"
        
        os_provider = Mock()
        json_provider = Mock()
        
        # エラーを含む結果
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "Invalid step type"
        
        with patch("src.domain.services.step_generation_service.run_steps") as mock_run_steps:
            mock_run_steps.return_value = [mock_result]
            
            result = generate_steps_from_json(json_steps, context, os_provider, json_provider)

        assert len(result.steps) == 0
        assert len(result.errors) == 1
        assert "Invalid step type" in result.errors[0]

    def test_mixed_results(self):
        """成功と失敗が混在する場合"""
        json_steps = [
            {"type": "mkdir", "cmd": ["/tmp/test"]},
            {"type": "invalid", "cmd": ["test"]},
            {"type": "touch", "cmd": ["/tmp/test/file.txt"]}
        ]
        context = Mock()
        context.contest_name = "abc300"
        context.problem_name = "c"
        context.language = "python3"
        context.local_workspace_path = "/workspace"
        context.contest_current_path = "/contest"
        context.source_file_name = "main.py"
        context.language_id = "py3"
        context.file_patterns = {}
        context.run_command = "python3"
        
        os_provider = Mock()
        json_provider = Mock()
        
        # 混在する結果
        mock_results = [
            Mock(success=True, step=create_test_step(StepType.MKDIR, ["/tmp/test"])),
            Mock(success=False, error_message="Invalid step type"),
            Mock(success=True, step=create_test_step(StepType.TOUCH, ["/tmp/test/file.txt"]))
        ]
        
        for result in mock_results:
            if not hasattr(result, 'error_message'):
                result.error_message = None
        
        with patch("src.domain.services.step_generation_service.run_steps") as mock_run_steps:
            mock_run_steps.return_value = mock_results
            
            result = generate_steps_from_json(json_steps, context, os_provider, json_provider)

        assert len(result.steps) == 2
        assert len(result.errors) == 1

    def test_missing_providers(self):
        """プロバイダーが未設定の場合"""
        json_steps = [{"type": "mkdir", "cmd": ["/tmp/test"]}]
        context = Mock()
        
        with pytest.raises(ValueError, match="プロバイダーは必須です"):
            generate_steps_from_json(json_steps, context, None, None)

    def test_empty_json_steps(self):
        """空のステップリスト"""
        json_steps = []
        context = Mock()
        context.contest_name = "abc300"
        context.problem_name = "d"
        context.language = "python3"
        context.local_workspace_path = "/workspace"
        context.contest_current_path = "/contest"
        context.source_file_name = "main.py"
        context.language_id = "py3"
        context.file_patterns = {}
        context.run_command = "python3"
        
        os_provider = Mock()
        json_provider = Mock()
        
        with patch("src.domain.services.step_generation_service.run_steps") as mock_run_steps:
            mock_run_steps.return_value = []
            
            result = generate_steps_from_json(json_steps, context, os_provider, json_provider)

        assert len(result.steps) == 0
        assert len(result.errors) == 0


class TestCreateStepFromJson:
    """create_step_from_jsonのテスト"""

    def test_create_step(self):
        """JSONからステップを作成"""
        json_step = {"type": "shell", "cmd": ["echo 'hello'"]}
        context = Mock()
        context.contest_name = "abc300"
        context.problem_name = "e"
        context.language = "python3"
        context.local_workspace_path = "/workspace"
        context.contest_current_path = "/contest"
        context.source_file_name = "main.py"
        context.language_id = "py3"
        context.file_patterns = {}
        context.run_command = "python3"
        
        mock_step = create_test_step(StepType.SHELL, ["echo 'hello'"])
        
        with patch("src.domain.services.step_generation_service.create_step_simple") as mock_create:
            mock_create.return_value = mock_step
            
            result = create_step_from_json(json_step, context)

        assert result.type == StepType.SHELL
        assert result.cmd == ["echo 'hello'"]


class TestFormatTemplate:
    """format_templateのテスト"""

    def test_valid_template(self):
        """有効なテンプレートのフォーマット"""
        template = "Contest: {contest_name}, Problem: {problem_name}"
        context = Mock()
        context.contest_name = "abc300"
        context.problem_name = "f"
        context.language = "python3"
        context.local_workspace_path = "/workspace"
        context.contest_current_path = "/contest"
        context.source_file_name = "main.py"
        context.language_id = "py3"
        context.file_patterns = {}
        context.run_command = "python3"
        
        with patch("src.domain.services.step_generation_service.expand_template") as mock_expand:
            mock_expand.return_value = "Contest: abc300, Problem: f"
            
            result = format_template(template, context)

        assert result == "Contest: abc300, Problem: f"

    def test_none_template(self):
        """Noneテンプレートの場合"""
        context = Mock()
        
        with pytest.raises(ValueError, match="Template is required but None was provided"):
            format_template(None, context)

    def test_non_string_template(self):
        """文字列以外のテンプレート"""
        context = Mock()
        
        with pytest.raises(ValueError, match="Template must be a string"):
            format_template(123, context)


class TestExpandFilePatterns:
    """expand_file_patternsのテスト"""

    def test_with_typed_execution_configuration(self):
        """TypedExecutionConfigurationを使用する場合"""
        template = "{source_file}"
        context = Mock()
        context.resolve_formatted_string = Mock(return_value="/workspace/main.py")
        
        # TypedExecutionConfigurationをモック
        with patch("src.domain.services.step_generation_service.TypedExecutionConfiguration", Mock):
            result = expand_file_patterns(template, context, StepType.SHELL)

        context.resolve_formatted_string.assert_called_once_with(template)
        assert result == "/workspace/main.py"

    def test_with_simple_context(self):
        """SimpleExecutionContextを使用する場合"""
        template = "Run {source}"
        context = Mock()
        context.contest_name = "abc300"
        context.problem_name = "g"
        context.language = "python3"
        context.local_workspace_path = "/workspace"
        context.contest_current_path = "/contest"
        context.source_file_name = "main.py"
        context.language_id = "py3"
        context.file_patterns = {"source": "*.py"}
        context.run_command = "python3"
        
        with patch("src.domain.services.step_generation_service.expand_template") as mock_expand:
            mock_expand.return_value = "Run {source}"
            with patch("src.domain.services.step_generation_service.expand_file_patterns_in_text") as mock_expand_patterns:
                mock_expand_patterns.return_value = "Run main.py"
                
                result = expand_file_patterns(template, context, StepType.SHELL)

        assert result == "Run main.py"

    def test_without_resolve_formatted_string(self):
        """TypedExecutionConfigurationにresolve_formatted_stringがない場合"""
        template = "{source_file}"
        context = Mock()
        del context.resolve_formatted_string
        
        with patch("src.domain.services.step_generation_service.TypedExecutionConfiguration", Mock):
            with pytest.raises(AttributeError, match="does not have required 'resolve_formatted_string' method"):
                expand_file_patterns(template, context, StepType.SHELL)


class TestValidateStepSequence:
    """validate_step_sequenceのテスト"""

    def test_valid_sequence(self):
        """有効なステップシーケンス"""
        steps = [
            create_test_step(StepType.MKDIR, ["/tmp/test"]),
            create_test_step(StepType.TOUCH, ["/tmp/test/file.txt"]),
            create_test_step(StepType.SHELL, ["echo 'done'"])
        ]
        
        errors = validate_step_sequence(steps)
        
        assert len(errors) == 0

    def test_invalid_sequence(self):
        """無効なステップを含むシーケンス"""
        # Stepクラスの__post_init__検証をバイパスするために直接作成
        from dataclasses import dataclass
        
        @dataclass
        class MockStep:
            type: StepType
            cmd: list
            
        # 無効なステップを作成
        steps = [
            MockStep(type=StepType.MKDIR, cmd=[]),  # 空のコマンド
            MockStep(type=StepType.COPY, cmd=["/src"]),  # 引数不足
            MockStep(type=StepType.SHELL, cmd=[""])  # 空のコマンド文字列
        ]
        
        # validate_step_sequenceをモックして、MockStepを処理できるようにする
        with patch("src.domain.services.step_generation_service.validate_single_step") as mock_validate:
            # 各ステップのバリデーション結果を設定
            mock_validate.side_effect = [
                ["Command cannot be empty"],
                ["Requires at least 2 arguments (src, dst), got 1"],
                ["Command cannot be empty"]
            ]
            
            errors = validate_step_sequence(steps)
        
        assert len(errors) == 3
        assert "Step 0 (mkdir)" in errors[0]
        assert "Step 1 (copy)" in errors[1]
        assert "Step 2 (shell)" in errors[2]


class TestValidateSingleStep:
    """validate_single_stepのテスト"""

    def test_empty_command(self):
        """空のコマンド"""
        # Stepクラスは初期化時に検証を行うため、無効なStepの作成はエラーになる
        # validate_single_step関数を直接テストする代わりに、モックStepを使用
        mock_step = Mock()
        mock_step.type = StepType.SHELL
        mock_step.cmd = []
        
        errors = validate_single_step(mock_step)
        assert "Command cannot be empty" in errors[0]

    def test_copy_valid(self):
        """有効なコピーコマンド"""
        step = create_test_step(StepType.COPY, ["/src/file.txt", "/dst/file.txt"])
        errors = validate_single_step(step)
        assert len(errors) == 0

    def test_copy_insufficient_args(self):
        """引数不足のコピーコマンド"""
        mock_step = Mock()
        mock_step.type = StepType.COPY
        mock_step.cmd = ["/src/file.txt"]
        
        errors = validate_single_step(mock_step)
        assert "Requires at least 2 arguments" in errors[0]

    def test_copy_empty_paths(self):
        """空のパスを持つコピーコマンド"""
        step = create_test_step(StepType.COPY, ["", "/dst/file.txt"])
        errors = validate_single_step(step)
        assert "Source and destination paths cannot be empty" in errors[0]

    def test_mkdir_valid(self):
        """有効なmkdirコマンド"""
        step = create_test_step(StepType.MKDIR, ["/tmp/newdir"])
        errors = validate_single_step(step)
        assert len(errors) == 0

    def test_mkdir_no_args(self):
        """引数なしのmkdirコマンド"""
        mock_step = Mock()
        mock_step.type = StepType.MKDIR
        mock_step.cmd = []
        
        errors = validate_single_step(mock_step)
        assert "Command cannot be empty" in errors[0]

    def test_mkdir_empty_path(self):
        """空のパスを持つmkdirコマンド"""
        step = create_test_step(StepType.MKDIR, [""])
        errors = validate_single_step(step)
        assert "Path cannot be empty" in errors[0]

    def test_shell_empty_command(self):
        """空のシェルコマンド"""
        step = create_test_step(StepType.SHELL, [""])
        errors = validate_single_step(step)
        assert "Command cannot be empty" in errors[0]

    def test_all_file_operation_types(self):
        """すべてのファイル操作タイプをテスト"""
        # 2引数が必要なタイプ
        for step_type in [StepType.COPY, StepType.COPYTREE, StepType.MOVE, StepType.MOVETREE]:
            mock_step = Mock()
            mock_step.type = step_type
            mock_step.cmd = ["/src"]
            
            errors = validate_single_step(mock_step)
            assert len(errors) == 1
            assert "Requires at least 2 arguments" in errors[0]

        # 1引数が必要なタイプ
        for step_type in [StepType.MKDIR, StepType.TOUCH, StepType.REMOVE, StepType.RMTREE]:
            mock_step = Mock()
            mock_step.type = step_type
            mock_step.cmd = []
            
            errors = validate_single_step(mock_step)
            assert len(errors) == 1
            assert "Command cannot be empty" in errors[0]


class TestOptimizeStepSequence:
    """optimize_step_sequenceのテスト"""

    def test_merge_consecutive_mkdir(self):
        """連続するmkdirをマージ"""
        steps = [
            create_test_step(StepType.MKDIR, ["/tmp/dir1"]),
            create_test_step(StepType.MKDIR, ["/tmp/dir2"]),
            create_test_step(StepType.MKDIR, ["/tmp/dir3"]),
            create_test_step(StepType.TOUCH, ["/tmp/file.txt"]),
            create_test_step(StepType.MKDIR, ["/tmp/dir4"])
        ]
        
        optimized = optimize_step_sequence(steps)
        
        # 最初の3つのmkdirは個別に保持される（重複排除のみ）
        assert len(optimized) == 5
        assert all(s.type == StepType.MKDIR for s in optimized[:3])
        assert optimized[3].type == StepType.TOUCH
        assert optimized[4].type == StepType.MKDIR

    def test_remove_duplicate_mkdir(self):
        """重複するmkdirを削除"""
        steps = [
            create_test_step(StepType.MKDIR, ["/tmp/dir1"]),
            create_test_step(StepType.MKDIR, ["/tmp/dir1"]),  # 重複
            create_test_step(StepType.MKDIR, ["/tmp/dir2"]),
            create_test_step(StepType.MKDIR, ["/tmp/dir1"])   # 重複
        ]
        
        optimized = optimize_step_sequence(steps)
        
        # 重複が削除される
        assert len(optimized) == 2
        assert optimized[0].cmd == ["/tmp/dir1"]
        assert optimized[1].cmd == ["/tmp/dir2"]

    def test_preserve_step_properties(self):
        """ステップのプロパティを保持"""
        steps = [
            create_test_step(StepType.MKDIR, ["/tmp/dir1"], allow_failure=True, show_output=False),
            create_test_step(StepType.MKDIR, ["/tmp/dir2"], allow_failure=False, show_output=True)
        ]
        
        optimized = optimize_step_sequence(steps)
        
        assert optimized[0].allow_failure is True
        assert optimized[0].show_output is False

    def test_no_optimization_needed(self):
        """最適化が不要な場合"""
        steps = [
            create_test_step(StepType.SHELL, ["echo 'start'"]),
            create_test_step(StepType.MKDIR, ["/tmp/dir1"]),
            create_test_step(StepType.COPY, ["/src/file", "/dst/file"]),
            create_test_step(StepType.SHELL, ["echo 'end'"])
        ]
        
        optimized = optimize_step_sequence(steps)
        
        # 変更なし
        assert len(optimized) == len(steps)
        for i, step in enumerate(optimized):
            assert step.type == steps[i].type
            assert step.cmd == steps[i].cmd

    def test_empty_sequence(self):
        """空のシーケンス"""
        steps = []
        optimized = optimize_step_sequence(steps)
        assert len(optimized) == 0