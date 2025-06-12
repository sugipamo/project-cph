"""新設定管理システムの基本動作テスト"""
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.configuration import (
    ConfigurationSource,
    ExecutionConfiguration,
    ExecutionPaths,
    RuntimeConfig,
    OutputConfig,
    ConfigurationLoader,
    TemplateExpander,
    ExecutionConfigurationFactory,
    ExecutionContextAdapter
)


class TestConfigurationSource(unittest.TestCase):
    """ConfigurationSourceのテスト"""
    
    def test_get_merged_config(self):
        """設定マージのテスト"""
        source = ConfigurationSource(
            system={'key1': 'system_value', 'key2': 'system_value2'},
            shared={'key2': 'shared_value', 'key3': 'shared_value3'},
            language={'key3': 'language_value', 'key4': 'language_value4'},
            runtime={'key4': 'runtime_value', 'key5': 'runtime_value5'}
        )
        
        merged = source.get_merged_config()
        
        # 優先順位確認: runtime > language > shared > system
        self.assertEqual(merged['key1'], 'system_value')
        self.assertEqual(merged['key2'], 'shared_value')
        self.assertEqual(merged['key3'], 'language_value')
        self.assertEqual(merged['key4'], 'runtime_value')
        self.assertEqual(merged['key5'], 'runtime_value5')
    
    def test_deep_merge(self):
        """深いマージのテスト"""
        source = ConfigurationSource(
            system={'nested': {'a': 1, 'b': 2}},
            shared={'nested': {'b': 3, 'c': 4}},
            language={},
            runtime={}
        )
        
        merged = source.get_merged_config()
        
        self.assertEqual(merged['nested']['a'], 1)
        self.assertEqual(merged['nested']['b'], 3)  # sharedが優先
        self.assertEqual(merged['nested']['c'], 4)


class TestExecutionConfiguration(unittest.TestCase):
    """ExecutionConfigurationのテスト"""
    
    def setUp(self):
        self.paths = ExecutionPaths(
            workspace=Path('./workspace'),
            contest_current=Path('./contest_current'),
            contest_stock=Path('./contest_stock'),
            contest_template=Path('./contest_template'),
            contest_temp=Path('./contest_temp')
        )
        
        self.runtime_config = RuntimeConfig(
            language_id='python',
            source_file_name='main.py',
            run_command='python3',
            timeout_seconds=30,
            retry_settings={}
        )
        
        self.output_config = OutputConfig(
            show_workflow_summary=True,
            show_step_details=True,
            show_execution_completion=True,
            format_preset='default'
        )
        
        self.config = ExecutionConfiguration(
            contest_name='test_contest',
            problem_name='test_problem',
            language='python',
            env_type='local',
            command_type='test',
            paths=self.paths,
            file_patterns={'test_files': ['test/*.in', 'test/*.out']},
            runtime_config=self.runtime_config,
            output_config=self.output_config
        )
    
    def test_to_template_dict(self):
        """テンプレート辞書生成のテスト"""
        template_dict = self.config.to_template_dict()
        
        self.assertEqual(template_dict['contest_name'], 'test_contest')
        self.assertEqual(template_dict['problem_name'], 'test_problem')
        self.assertEqual(template_dict['language'], 'python')
        self.assertEqual(template_dict['workspace'], 'workspace')
        self.assertEqual(template_dict['source_file_name'], 'main.py')
    
    def test_get_file_pattern(self):
        """ファイルパターン取得のテスト"""
        patterns = self.config.get_file_pattern('test_files')
        self.assertEqual(patterns, ['test/*.in', 'test/*.out'])
        
        # 存在しないパターン
        empty_patterns = self.config.get_file_pattern('nonexistent')
        self.assertEqual(empty_patterns, [])


class TestTemplateExpander(unittest.TestCase):
    """TemplateExpanderのテスト"""
    
    def setUp(self):
        self.config = ExecutionConfiguration(
            contest_name='test_contest',
            problem_name='test_problem',
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
            file_patterns={'test_files': ['test/*.in'], 'contest_files': ['main.py']},
            runtime_config=RuntimeConfig(
                language_id='python',
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
        
        self.expander = TemplateExpander(self.config)
    
    def test_expand_basic_variables(self):
        """基本変数展開のテスト"""
        template = "Contest: {contest_name}, Problem: {problem_name}, Language: {language}"
        result = self.expander.expand_basic_variables(template)
        
        expected = "Contest: test_contest, Problem: test_problem, Language: python"
        self.assertEqual(result, expected)
    
    def test_expand_file_patterns(self):
        """ファイルパターン展開のテスト"""
        template = "Test files: {test_files}, Contest files: {contest_files}"
        result = self.expander.expand_file_patterns(template)
        
        expected = "Test files: test/*.in, Contest files: main.py"
        self.assertEqual(result, expected)
    
    def test_expand_all(self):
        """統一変数展開のテスト"""
        template = "{contest_name}/{problem_name} using {test_files}"
        result = self.expander.expand_all(template)
        
        expected = "test_contest/test_problem using test/*.in"
        self.assertEqual(result, expected)
    
    def test_expand_command(self):
        """コマンド展開のテスト"""
        cmd = ["cp", "{test_files}", "{workspace}/test/"]
        result = self.expander.expand_command(cmd)
        
        expected = ["cp", "test/*.in", "workspace/test/"]
        self.assertEqual(result, expected)
    
    def test_extract_template_keys(self):
        """テンプレートキー抽出のテスト"""
        template = "{contest_name} and {problem_name} with {test_files}"
        keys = self.expander.extract_template_keys(template)
        
        expected_keys = ['contest_name', 'problem_name', 'test_files']
        self.assertEqual(sorted(keys), sorted(expected_keys))
    
    def test_validate_template(self):
        """テンプレート検証のテスト"""
        # 有効なテンプレート
        valid_template = "{contest_name}/{test_files}"
        is_valid, errors = self.expander.validate_template(valid_template)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
        
        # 無効なテンプレート
        invalid_template = "{contest_name}/{invalid_key}"
        is_valid, errors = self.expander.validate_template(invalid_template)
        self.assertFalse(is_valid)
        self.assertIn('invalid_key', errors)


@patch('src.configuration.loaders.configuration_loader.Path')
class TestConfigurationLoader(unittest.TestCase):
    """ConfigurationLoaderのテスト"""
    
    def test_load_source(self, mock_path):
        """設定ソース読み込みのテスト"""
        # Pathのモックを設定
        mock_contest_env = MagicMock()
        mock_system_config = MagicMock()
        
        loader = ConfigurationLoader(mock_contest_env, mock_system_config)
        
        # メソッドをモック
        loader.load_system_configs = MagicMock(return_value={'system_key': 'system_value'})
        loader.load_env_configs = MagicMock(return_value=({'shared_key': 'shared_value'}, {'lang_key': 'lang_value'}))
        
        runtime_args = {'runtime_key': 'runtime_value'}
        source = loader.load_source('python', runtime_args)
        
        self.assertEqual(source.system['system_key'], 'system_value')
        self.assertEqual(source.shared['shared_key'], 'shared_value')
        self.assertEqual(source.language['lang_key'], 'lang_value')
        self.assertEqual(source.runtime['runtime_key'], 'runtime_value')


class TestExecutionContextAdapter(unittest.TestCase):
    """ExecutionContextAdapterのテスト"""
    
    def setUp(self):
        self.config = ExecutionConfiguration(
            contest_name='test_contest',
            problem_name='test_problem',
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
            file_patterns={},
            runtime_config=RuntimeConfig(
                language_id='python',
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
        
        self.expander = TemplateExpander(self.config)
        self.adapter = ExecutionContextAdapter(self.config, self.expander)
    
    def test_format_string(self):
        """format_string互換性のテスト"""
        template = "Contest: {contest_name}, Language: {language}"
        result = self.adapter.format_string(template)
        
        expected = "Contest: test_contest, Language: python"
        self.assertEqual(result, expected)
    
    def test_properties(self):
        """プロパティ互換性のテスト"""
        self.assertEqual(self.adapter.contest_name, 'test_contest')
        self.assertEqual(self.adapter.language, 'python')
        self.assertEqual(self.adapter.workspace_path, 'workspace')
    
    def test_to_dict(self):
        """to_dict互換性のテスト"""
        result = self.adapter.to_dict()
        
        self.assertEqual(result['contest_name'], 'test_contest')
        self.assertEqual(result['language'], 'python')
        self.assertIn('workspace', result)


if __name__ == '__main__':
    unittest.main()