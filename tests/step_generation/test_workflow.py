"""
完全なワークフローパイプラインのテスト
"""
import pytest
from unittest.mock import Mock, MagicMock
from src.env.step_generation.workflow import (
    generate_workflow_from_json,
    create_step_context_from_env_context,
    validate_workflow_execution,
    debug_workflow_generation
)
from src.env.step_generation.step import StepContext
from src.operations.composite.composite_request import CompositeRequest


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
        contest_current_path='./contest_current'
    )


@pytest.fixture
def mock_operations():
    """モックのDIコンテナ"""
    operations = Mock()
    file_driver = Mock()
    operations.resolve.return_value = file_driver
    return operations


class TestGenerateWorkflowFromJson:
    def test_complete_pipeline(self, test_context, mock_operations):
        """完全なパイプラインのテスト"""
        json_steps = [
            {'type': 'copy', 'cmd': ['src.txt', '/tmp/deep/nested/dst.txt']},
            {'type': 'shell', 'cmd': ['echo', 'done']}
        ]
        
        composite_request, errors, warnings = generate_workflow_from_json(
            json_steps, test_context, mock_operations
        )
        
        assert isinstance(composite_request, CompositeRequest)
        assert len(errors) == 0
        assert len(warnings) == 0
        assert len(composite_request.requests) > 0
    
    def test_invalid_steps_error_handling(self, test_context, mock_operations):
        """無効なステップのエラーハンドリングテスト"""
        json_steps = [
            {'type': 'invalid_type', 'cmd': ['test']}
        ]
        
        composite_request, errors, warnings = generate_workflow_from_json(
            json_steps, test_context, mock_operations
        )
        
        assert len(errors) > 0
        assert len(composite_request.requests) == 0
    
    def test_dependency_resolution_integration(self, test_context, mock_operations):
        """依存解決の統合テスト"""
        json_steps = [
            {'type': 'copy', 'cmd': ['src.txt', '/tmp/new/dir/dst.txt']}
        ]
        
        composite_request, errors, warnings = generate_workflow_from_json(
            json_steps, test_context, mock_operations
        )
        
        assert len(errors) == 0
        # 依存解決により、mkdir + copy の2つ以上のリクエストが生成される
        assert len(composite_request.requests) >= 2


class TestCreateStepContextFromEnvContext:
    def test_env_context_conversion(self):
        """EnvContextからStepContextへの変換テスト"""
        # モックのEnvContext
        env_context = Mock()
        env_context.contest_name = 'abc300'
        env_context.problem_name = 'a'
        env_context.language = 'python'
        env_context.env_type = 'local'
        env_context.command_type = 'open'
        env_context.workspace_path = './workspace'
        env_context.contest_current_path = './contest_current'
        env_context.contest_stock_path = './contest_stock'
        env_context.contest_template_path = './contest_template'
        env_context.contest_temp_path = './.temp'
        env_context.source_file_name = 'main.py'
        env_context.language_id = '5078'
        
        step_context = create_step_context_from_env_context(env_context)
        
        assert step_context.contest_name == 'abc300'
        assert step_context.problem_name == 'a'
        assert step_context.language == 'python'
        assert step_context.env_type == 'local'
        assert step_context.command_type == 'open'
        assert step_context.workspace_path == './workspace'
        assert step_context.contest_current_path == './contest_current'
        assert step_context.contest_stock_path == './contest_stock'
        assert step_context.contest_template_path == './contest_template'
        assert step_context.contest_temp_path == './.temp'
        assert step_context.source_file_name == 'main.py'
        assert step_context.language_id == '5078'
    
    def test_missing_attributes_default_values(self):
        """属性が欠けている場合のデフォルト値テスト"""
        # 最小限の属性のみを持つモック
        env_context = Mock()
        env_context.contest_name = 'test'
        env_context.problem_name = 'a'
        env_context.language = 'python'
        env_context.env_type = 'local'
        env_context.command_type = 'open'
        
        # 存在しない属性についてはデフォルト値が使用される
        for attr in ['workspace_path', 'contest_current_path', 'contest_stock_path']:
            if not hasattr(env_context, attr):
                setattr(env_context, attr, '')
        
        step_context = create_step_context_from_env_context(env_context)
        
        assert step_context.contest_name == 'test'
        assert step_context.problem_name == 'a'


class TestValidateWorkflowExecution:
    def test_successful_validation(self):
        """成功する検証のテスト"""
        # リクエストを含むCompositeRequest
        composite_request = Mock()
        composite_request.requests = [Mock(), Mock()]
        errors = []
        warnings = []
        
        is_valid, messages = validate_workflow_execution(composite_request, errors, warnings)
        
        assert is_valid is True
        assert any('Generated 2 executable requests' in msg for msg in messages)
    
    def test_validation_with_errors(self):
        """エラーがある場合の検証テスト"""
        composite_request = Mock()
        composite_request.requests = []
        errors = ['Step 0: Invalid type']
        warnings = []
        
        is_valid, messages = validate_workflow_execution(composite_request, errors, warnings)
        
        assert is_valid is False
        assert any('Found 1 errors:' in msg for msg in messages)
        assert any('Step 0: Invalid type' in msg for msg in messages)
    
    def test_validation_with_warnings(self):
        """警告がある場合の検証テスト"""
        composite_request = Mock()
        composite_request.requests = [Mock()]
        errors = []
        warnings = ['Step optimization removed duplicate mkdir']
        
        is_valid, messages = validate_workflow_execution(composite_request, errors, warnings)
        
        assert is_valid is True
        assert any('Found 1 warnings:' in msg for msg in messages)
        assert any('Step optimization removed duplicate mkdir' in msg for msg in messages)
    
    def test_empty_requests_validation(self):
        """空のリクエストの検証テスト"""
        composite_request = Mock()
        composite_request.requests = []
        errors = []
        warnings = []
        
        is_valid, messages = validate_workflow_execution(composite_request, errors, warnings)
        
        assert is_valid is False
        assert any('No executable requests generated' in msg for msg in messages)


class TestDebugWorkflowGeneration:
    def test_debug_info_structure(self, test_context):
        """デバッグ情報の構造テスト"""
        json_steps = [
            {'type': 'mkdir', 'cmd': ['/tmp/test']},
            {'type': 'copy', 'cmd': ['src.txt', '/tmp/test/dst.txt']}
        ]
        
        debug_info = debug_workflow_generation(json_steps, test_context)
        
        # 基本構造の確認
        assert 'input_steps' in debug_info
        assert 'stages' in debug_info
        assert debug_info['input_steps'] == 2
        
        # 各段階の情報が含まれている
        stages = debug_info['stages']
        assert 'step_generation' in stages
        assert 'dependency_resolution' in stages
        assert 'optimization' in stages
        
        # ステップ生成段階の情報
        step_gen = stages['step_generation']
        assert 'generated_steps' in step_gen
        assert 'errors' in step_gen
        assert 'warnings' in step_gen
        assert 'steps' in step_gen
        
        # 依存解決段階の情報
        dep_res = stages['dependency_resolution']
        assert 'original_steps' in dep_res
        assert 'resolved_steps' in dep_res
        assert 'added_steps' in dep_res
        
        # 最適化段階の情報
        opt = stages['optimization']
        assert 'pre_optimization' in opt
        assert 'post_optimization' in opt
        assert 'removed_steps' in opt
    
    def test_debug_with_errors(self, test_context):
        """エラーがある場合のデバッグ情報テスト"""
        json_steps = [
            {'type': 'invalid_type', 'cmd': ['test']}
        ]
        
        debug_info = debug_workflow_generation(json_steps, test_context)
        
        # エラー情報が記録されている
        step_gen = debug_info['stages']['step_generation']
        assert len(step_gen['errors']) > 0
        assert 'Unknown step type: invalid_type' in step_gen['errors'][0]
    
    def test_debug_dependency_insertion(self, test_context):
        """依存関係挿入のデバッグ情報テスト"""
        json_steps = [
            {'type': 'copy', 'cmd': ['src.txt', '/tmp/deep/nested/dst.txt']}
        ]
        
        debug_info = debug_workflow_generation(json_steps, test_context)
        
        # 依存関係により新しいステップが追加される
        dep_res = debug_info['stages']['dependency_resolution']
        assert dep_res['resolved_steps'] > dep_res['original_steps']
        assert dep_res['added_steps'] > 0