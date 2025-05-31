"""
純粋関数ベースのステップ生成のコア機能テスト
"""
import pytest
from src.env_core.step.core import (
    generate_steps_from_json,
    create_step_from_json,
    format_template,
    validate_step_sequence,
    optimize_step_sequence
)
from src.env_core.step.step import Step, StepType, StepContext, StepGenerationResult


@pytest.fixture
def test_context():
    """テスト用のStepContext"""
    return StepContext(
        contest_name='abc300',
        problem_name='a',
        language='python',
        env_type='local',
        command_type='open',
        workspace_path='./workspace',
        contest_current_path='./contest_current',
        contest_stock_path='./contest_stock',
        contest_template_path='./contest_template',
        contest_temp_path='./.temp',
        source_file_name='main.py',
        language_id='5078'
    )


class TestGenerateStepsFromJson:
    def test_basic_step_generation(self, test_context):
        """基本的なステップ生成のテスト"""
        json_steps = [
            {'type': 'mkdir', 'cmd': ['/tmp/test']},
            {'type': 'copy', 'cmd': ['src.txt', '/tmp/test/dst.txt']},
            {'type': 'shell', 'cmd': ['echo', 'hello']}
        ]
        
        result = generate_steps_from_json(json_steps, test_context)
        
        assert result.is_success
        assert len(result.steps) == 3
        assert result.steps[0].type == StepType.MKDIR
        assert result.steps[1].type == StepType.COPY
        assert result.steps[2].type == StepType.SHELL
    
    def test_template_formatting(self, test_context):
        """テンプレートフォーマットのテスト"""
        json_steps = [
            {'type': 'shell', 'cmd': ['echo', '{contest_name}_{problem_name}']}
        ]
        
        result = generate_steps_from_json(json_steps, test_context)
        
        assert result.is_success
        assert len(result.steps) == 1
        assert result.steps[0].cmd == ['echo', 'abc300_a']
    
    def test_invalid_step_type(self, test_context):
        """無効なステップタイプのテスト"""
        json_steps = [
            {'type': 'invalid_type', 'cmd': ['test']}
        ]
        
        result = generate_steps_from_json(json_steps, test_context)
        
        assert not result.is_success
        assert len(result.errors) == 1
        assert 'Unknown step type: invalid_type' in result.errors[0]
    
    def test_missing_type_field(self, test_context):
        """typeフィールドが欠けているテスト"""
        json_steps = [
            {'cmd': ['test']}
        ]
        
        result = generate_steps_from_json(json_steps, test_context)
        
        assert not result.is_success
        assert len(result.errors) == 1
        assert "Step must have 'type' field" in result.errors[0]


class TestCreateStepFromJson:
    def test_create_mkdir_step(self, test_context):
        """mkdirステップの作成テスト"""
        json_step = {'type': 'mkdir', 'cmd': ['/tmp/test']}
        
        step = create_step_from_json(json_step, test_context)
        
        assert step.type == StepType.MKDIR
        assert step.cmd == ['/tmp/test']
        assert step.allow_failure is False
        assert step.show_output is False
    
    def test_create_step_with_options(self, test_context):
        """オプション付きステップの作成テスト"""
        json_step = {
            'type': 'shell',
            'cmd': ['echo', 'test'],
            'allow_failure': True,
            'show_output': True,
            'cwd': '/tmp'
        }
        
        step = create_step_from_json(json_step, test_context)
        
        assert step.type == StepType.SHELL
        assert step.allow_failure is True
        assert step.show_output is True
        assert step.cwd == '/tmp'
    
    def test_invalid_cmd_type(self, test_context):
        """cmdが配列でない場合のテスト"""
        json_step = {'type': 'shell', 'cmd': 'not_a_list'}
        
        with pytest.raises(ValueError, match="Step 'cmd' must be a list"):
            create_step_from_json(json_step, test_context)


class TestFormatTemplate:
    def test_simple_template(self, test_context):
        """シンプルなテンプレートのテスト"""
        template = "Hello {contest_name}"
        
        result = format_template(template, test_context)
        
        assert result == "Hello abc300"
    
    def test_multiple_placeholders(self, test_context):
        """複数のプレースホルダーのテスト"""
        template = "{contest_name}_{problem_name}_{language}"
        
        result = format_template(template, test_context)
        
        assert result == "abc300_a_python"
    
    def test_non_string_input(self, test_context):
        """文字列以外の入力のテスト"""
        assert format_template(123, test_context) == "123"
        assert format_template(None, test_context) == ""
        assert format_template([], test_context) == "[]"


class TestValidateStepSequence:
    def test_valid_sequence(self):
        """有効なシーケンスのテスト"""
        steps = [
            Step(StepType.MKDIR, ['/tmp/test']),
            Step(StepType.COPY, ['src.txt', '/tmp/test/dst.txt']),
            Step(StepType.SHELL, ['echo', 'done'])
        ]
        
        errors = validate_step_sequence(steps)
        
        assert len(errors) == 0
    
    def test_invalid_copy_args(self):
        """copyステップの引数不足テスト"""
        # Stepクラス自体で検証されるため、直接作成時にエラーが発生する
        with pytest.raises(ValueError, match="Step .* requires at least 2 arguments"):
            Step(StepType.COPY, ['only_one_arg'])
    
    def test_empty_command(self):
        """空のコマンドのテスト"""
        # Stepクラスの__post_init__で検証されるため、
        # 直接作成時にエラーが発生する
        with pytest.raises(ValueError, match="Step .* must have non-empty cmd"):
            Step(StepType.SHELL, [])


class TestOptimizeStepSequence:
    def test_no_optimization_needed(self):
        """最適化が不要なシーケンスのテスト"""
        steps = [
            Step(StepType.COPY, ['src.txt', 'dst.txt']),
            Step(StepType.SHELL, ['echo', 'done'])
        ]
        
        optimized = optimize_step_sequence(steps)
        
        assert len(optimized) == len(steps)
        assert optimized == steps
    
    def test_mkdir_optimization(self):
        """mkdirの最適化テスト"""
        steps = [
            Step(StepType.MKDIR, ['/tmp/test1']),
            Step(StepType.MKDIR, ['/tmp/test2']),
            Step(StepType.MKDIR, ['/tmp/test1']),  # 重複
            Step(StepType.SHELL, ['echo', 'done'])
        ]
        
        optimized = optimize_step_sequence(steps)
        
        # 重複が除去されることを確認
        mkdir_steps = [s for s in optimized if s.type == StepType.MKDIR]
        assert len(mkdir_steps) == 2
        assert mkdir_steps[0].cmd == ['/tmp/test1']
        assert mkdir_steps[1].cmd == ['/tmp/test2']