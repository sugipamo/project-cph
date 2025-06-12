"""統合テスト - 新設定システムのエンドツーエンドテスト"""
import unittest
from unittest.mock import MagicMock
from pathlib import Path

from src.configuration import (
    ExecutionConfiguration,
    ExecutionPaths, 
    RuntimeConfig,
    OutputConfig
)
from src.configuration.integration.user_input_parser_integration import (
    UserInputParserIntegration,
    create_new_execution_context
)
from src.workflow.step.simple_step_runner import expand_template_with_new_system


class TestEndToEndIntegration(unittest.TestCase):
    """エンドツーエンドの統合テスト"""
    
    def setUp(self):
        """テスト用設定の準備"""
        self.config = ExecutionConfiguration(
            contest_name='abc123',
            problem_name='problem_a',
            language='python',
            env_type='local',
            command_type='test',
            paths=ExecutionPaths(
                workspace=Path('./workspace'),
                contest_current=Path('./contest_current'),
                contest_stock=Path('./contest_stock'),
                contest_template=Path('./contest_template'),
                contest_temp=Path('./contest_temp')
            ),
            file_patterns={
                'test_files': ['test/*.in', 'test/*.out'],
                'contest_files': ['main.py', '*.py'],
                'solution_files': ['solution.py']
            },
            runtime_config=RuntimeConfig(
                language_id='3.11.1',
                source_file_name='main.py',
                run_command='python3',
                timeout_seconds=30,
                retry_settings={}
            ),
            output_config=OutputConfig(
                show_workflow_summary=True,
                show_step_details=True,
                show_execution_completion=True,
                format_preset='default'
            )
        )
    
    def test_template_expansion_scenario(self):
        """テンプレート展開の包括的なシナリオテスト"""
        # 基本変数展開
        template1 = "Contest: {contest_name}, Problem: {problem_name}"
        result1 = expand_template_with_new_system(template1, self.config)
        self.assertEqual(result1, "Contest: abc123, Problem: problem_a")
        
        # パス変数展開
        template2 = "Copy from {workspace} to {contest_current}"
        result2 = expand_template_with_new_system(template2, self.config)
        self.assertEqual(result2, "Copy from workspace to contest_current")
        
        # ファイルパターン展開
        template3 = "Run tests on {test_files}"
        result3 = expand_template_with_new_system(template3, self.config)
        self.assertEqual(result3, "Run tests on test/*.in")
        
        # 複合展開
        template4 = "{language} contest {contest_name} with {contest_files}"
        result4 = expand_template_with_new_system(template4, self.config)
        self.assertEqual(result4, "python contest abc123 with main.py")
    
    def test_user_input_parser_integration_scenario(self):
        """user_input_parserでの統合シナリオテスト"""
        integration = UserInputParserIntegration()
        
        # 新しいExecutionContextアダプターを作成
        adapter = integration.create_execution_context_adapter(
            command_type='test',
            language='python',
            contest_name='abc123',
            problem_name='problem_a',
            env_type='local',
            env_json={'python': {'file_patterns': {'test_files': ['test/*.py']}}}
        )
        
        # 基本プロパティの確認
        self.assertEqual(adapter.contest_name, 'abc123')
        self.assertEqual(adapter.language, 'python')
        self.assertEqual(adapter.env_type, 'local')
        
        # テンプレート展開の確認
        template = "Test {contest_name}/{problem_name}"
        result = adapter.format_string(template)
        self.assertEqual(result, "Test abc123/problem_a")
        
        # to_dict()の確認
        template_dict = adapter.to_dict()
        self.assertIn('contest_name', template_dict)
        self.assertIn('language', template_dict)
        self.assertEqual(template_dict['contest_name'], 'abc123')
    
    def test_compatibility_validation_scenario(self):
        """互換性検証のシナリオテスト"""
        integration = UserInputParserIntegration()
        
        # 新システムのアダプター
        new_adapter = integration.create_execution_context_adapter(
            command_type='test',
            language='cpp',
            contest_name='contest1',
            problem_name='problem1',
            env_type='docker',
            env_json={}
        )
        
        # 模擬的な旧システム
        mock_old_context = MagicMock()
        mock_old_context.contest_name = 'contest1'
        mock_old_context.language = 'cpp'
        mock_old_context.format_string.return_value = 'contest1/cpp'
        
        # 互換性チェック
        is_compatible = integration.validate_new_system_compatibility(
            mock_old_context, new_adapter
        )
        self.assertTrue(is_compatible)
    
    def test_file_pattern_operations_scenario(self):
        """ファイルパターン操作のシナリオテスト"""
        # MOVETREEの場合
        template_movetree = "Move {contest_files} to backup"
        result_movetree = expand_template_with_new_system(
            template_movetree, self.config, 'movetree'
        )
        # MOVETREEの場合は最初のパターンがそのまま使用される
        self.assertEqual(result_movetree, "Move main.py to backup")
        
        # COPYTREE の場合 (ディレクトリ部分のみが抽出される)
        template_copytree = "Copy {test_files} to archive"
        result_copytree = expand_template_with_new_system(
            template_copytree, self.config, 'copytree'
        )
        # COPYTREEの場合はディレクトリ部分のみが使用される
        self.assertEqual(result_copytree, "Copy test to archive")
    
    def test_error_handling_scenario(self):
        """エラーハンドリングのシナリオテスト"""
        try:
            # 存在しない変数を含むテンプレート
            template = "Invalid {nonexistent_variable}"
            result = expand_template_with_new_system(template, self.config)
            # 未解決の変数はそのまま残る
            self.assertEqual(result, "Invalid {nonexistent_variable}")
        except Exception as e:
            self.fail(f"Unexpected exception raised: {e}")
    
    def test_performance_scenario(self):
        """パフォーマンステストシナリオ"""
        import time
        
        # 大量のテンプレート展開を実行
        templates = [
            "{contest_name}/{problem_name}",
            "{language} solution in {workspace}",
            "Test {test_files} with {run_command}",
            "Deploy to {contest_current} from {contest_template}"
        ] * 100  # 400回の展開
        
        start_time = time.time()
        
        for template in templates:
            result = expand_template_with_new_system(template, self.config)
            self.assertNotEqual(result, template)  # 何らかの展開が行われたことを確認
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 400回の展開が1秒以内に完了することを確認
        self.assertLess(execution_time, 1.0, 
                       f"Performance test failed: {execution_time:.3f}s for 400 expansions")
        print(f"Performance test passed: {execution_time:.3f}s for 400 expansions")


if __name__ == '__main__':
    unittest.main()