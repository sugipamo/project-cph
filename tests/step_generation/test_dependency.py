"""
依存関係解決機能のテスト
"""
import pytest
from src.env.step_generation.dependency import (
    resolve_dependencies,
    generate_preparation_steps,
    optimize_mkdir_steps,
    analyze_step_dependencies
)
from src.env.step_generation.step import Step, StepType, StepContext


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


class TestResolveDependencies:
    def test_simple_copy_dependency(self, test_context):
        """シンプルなcopy操作の依存解決テスト"""
        steps = [
            Step(StepType.COPY, ['src.txt', '/tmp/deep/nested/dst.txt'])
        ]
        
        resolved = resolve_dependencies(steps, test_context)
        
        # 親ディレクトリ作成ステップが挿入されることを確認
        assert len(resolved) == 2
        assert resolved[0].type == StepType.MKDIR
        assert resolved[0].cmd == ['/tmp/deep/nested']
        assert resolved[1] == steps[0]
    
    def test_touch_dependency(self, test_context):
        """touchファイル操作の依存解決テスト"""
        steps = [
            Step(StepType.TOUCH, ['/tmp/path/to/file.txt'])
        ]
        
        resolved = resolve_dependencies(steps, test_context)
        
        assert len(resolved) == 2
        assert resolved[0].type == StepType.MKDIR
        assert resolved[0].cmd == ['/tmp/path/to']
        assert resolved[0].allow_failure is True  # ディレクトリ作成は失敗を許可
    
    def test_existing_directory_tracking(self, test_context):
        """既存ディレクトリの追跡テスト"""
        steps = [
            Step(StepType.MKDIR, ['/tmp/test']),
            Step(StepType.COPY, ['src.txt', '/tmp/test/file1.txt']),
            Step(StepType.COPY, ['src2.txt', '/tmp/test/file2.txt'])
        ]
        
        resolved = resolve_dependencies(steps, test_context)
        
        # 最初のmkdirで/tmp/testが作成されるため、
        # 後続のcopyでは追加のmkdirは不要
        mkdir_steps = [s for s in resolved if s.type == StepType.MKDIR]
        assert len(mkdir_steps) == 1
        assert mkdir_steps[0].cmd == ['/tmp/test']
    
    def test_working_directory_dependency(self, test_context):
        """作業ディレクトリの依存解決テスト"""
        steps = [
            Step(StepType.SHELL, ['echo', 'hello'], cwd='/tmp/workdir')
        ]
        
        resolved = resolve_dependencies(steps, test_context)
        
        assert len(resolved) == 2
        assert resolved[0].type == StepType.MKDIR
        assert resolved[0].cmd == ['/tmp/workdir']
    
    def test_no_dependencies_needed(self, test_context):
        """依存関係が不要なケースのテスト"""
        steps = [
            Step(StepType.SHELL, ['echo', 'hello']),
            Step(StepType.COPY, ['src.txt', 'dst.txt'])  # 相対パス
        ]
        
        resolved = resolve_dependencies(steps, test_context)
        
        # 追加のステップは不要
        assert len(resolved) == len(steps)
        assert resolved == steps


class TestGeneratePreparationSteps:
    def test_copy_preparation(self, test_context):
        """copy操作の準備ステップ生成テスト"""
        step = Step(StepType.COPY, ['src.txt', '/tmp/deep/nested/dst.txt'])
        existing_dirs = set()
        existing_files = set()
        
        prep_steps = generate_preparation_steps(step, existing_dirs, existing_files, test_context)
        
        assert len(prep_steps) == 1
        assert prep_steps[0].type == StepType.MKDIR
        assert prep_steps[0].cmd == ['/tmp/deep/nested']
    
    def test_no_preparation_needed(self, test_context):
        """準備ステップが不要なケース"""
        step = Step(StepType.SHELL, ['echo', 'hello'])
        existing_dirs = set()
        existing_files = set()
        
        prep_steps = generate_preparation_steps(step, existing_dirs, existing_files, test_context)
        
        assert len(prep_steps) == 0
    
    def test_existing_directory_skip(self, test_context):
        """既存ディレクトリの場合はスキップ"""
        step = Step(StepType.COPY, ['src.txt', '/tmp/existing/dst.txt'])
        existing_dirs = {'/tmp/existing'}
        existing_files = set()
        
        prep_steps = generate_preparation_steps(step, existing_dirs, existing_files, test_context)
        
        assert len(prep_steps) == 0


class TestOptimizeMkdirSteps:
    def test_consecutive_mkdir_optimization(self):
        """連続するmkdirステップの最適化テスト"""
        steps = [
            Step(StepType.MKDIR, ['/tmp/test1']),
            Step(StepType.MKDIR, ['/tmp/test2']),
            Step(StepType.MKDIR, ['/tmp/test1']),  # 重複
            Step(StepType.SHELL, ['echo', 'done']),
            Step(StepType.MKDIR, ['/tmp/test3'])
        ]
        
        optimized = optimize_mkdir_steps(steps)
        
        # 連続するmkdirは最適化されるが、間にshellがあるので分離される
        mkdir_count = len([s for s in optimized if s.type == StepType.MKDIR])
        assert mkdir_count == 3  # test1, test2, test3 (重複除去済み)
        
        # 最初の2つのmkdirが統合される
        assert optimized[0].type == StepType.MKDIR
        assert optimized[1].type == StepType.MKDIR
        assert optimized[2].type == StepType.SHELL
        assert optimized[3].type == StepType.MKDIR
    
    def test_mkdir_with_different_attributes(self):
        """異なる属性を持つmkdirの処理テスト"""
        steps = [
            Step(StepType.MKDIR, ['/tmp/test1'], allow_failure=True),
            Step(StepType.MKDIR, ['/tmp/test2'], allow_failure=False),
            Step(StepType.MKDIR, ['/tmp/test3'], allow_failure=True)
        ]
        
        optimized = optimize_mkdir_steps(steps)
        
        # 異なる属性のため統合されない
        assert len(optimized) == 3
        assert all(s.type == StepType.MKDIR for s in optimized)
    
    def test_empty_steps_list(self):
        """空のステップリストのテスト"""
        steps = []
        
        optimized = optimize_mkdir_steps(steps)
        
        assert len(optimized) == 0


class TestAnalyzeStepDependencies:
    def test_copy_file_dependency(self):
        """ファイルコピーの依存関係分析テスト"""
        steps = [
            Step(StepType.TOUCH, ['temp.txt']),
            Step(StepType.COPY, ['temp.txt', 'dst.txt']),
            Step(StepType.SHELL, ['cat', 'dst.txt'])
        ]
        
        dependencies = analyze_step_dependencies(steps)
        
        # ステップ1(copy)はステップ0(touch)に依存
        assert 1 in dependencies
        assert 0 in dependencies[1]
    
    def test_no_dependencies(self):
        """依存関係がないケースのテスト"""
        steps = [
            Step(StepType.SHELL, ['echo', 'hello']),
            Step(StepType.MKDIR, ['/tmp/test'])
        ]
        
        dependencies = analyze_step_dependencies(steps)
        
        # 依存関係はない
        for deps in dependencies.values():
            assert len(deps) == 0