"""言語レジストリのテスト"""
import unittest

from src.configuration.registries.language_registry import (
    LanguageConfig,
    LanguageRegistry,
    get_language_registry,
    register_custom_language
)


class TestLanguageRegistry(unittest.TestCase):
    """言語レジストリのテスト"""
    
    def setUp(self):
        """テスト用レジストリを作成"""
        self.registry = LanguageRegistry()
    
    def test_language_config_creation(self):
        """LanguageConfig作成のテスト"""
        config = LanguageConfig(
            extension='py',
            run_command='python3',
            aliases=['py', 'python']
        )
        
        self.assertEqual(config.extension, 'py')
        self.assertEqual(config.run_command, 'python3')
        self.assertEqual(config.aliases, ['py', 'python'])
        self.assertIsNone(config.compile_command)
    
    def test_default_languages_loaded(self):
        """デフォルト言語が読み込まれることのテスト"""
        self.assertTrue(self.registry.is_supported('python'))
        self.assertTrue(self.registry.is_supported('cpp'))
        self.assertTrue(self.registry.is_supported('rust'))
        self.assertTrue(self.registry.is_supported('java'))
    
    def test_language_aliases(self):
        """言語エイリアスのテスト"""
        # Pythonのエイリアス
        self.assertTrue(self.registry.is_supported('py'))
        self.assertTrue(self.registry.is_supported('python3'))
        
        # C++のエイリアス
        self.assertTrue(self.registry.is_supported('c++'))
        self.assertTrue(self.registry.is_supported('cxx'))
    
    def test_get_file_extension(self):
        """ファイル拡張子取得のテスト"""
        self.assertEqual(self.registry.get_file_extension('python'), 'py')
        self.assertEqual(self.registry.get_file_extension('cpp'), 'cpp')
        self.assertEqual(self.registry.get_file_extension('rust'), 'rs')
        
        # 存在しない言語
        self.assertEqual(self.registry.get_file_extension('nonexistent'), 'txt')
    
    def test_get_run_command(self):
        """実行コマンド取得のテスト"""
        self.assertEqual(self.registry.get_run_command('python'), 'python3')
        self.assertEqual(self.registry.get_run_command('cpp'), './main')
        self.assertEqual(self.registry.get_run_command('java'), 'java Main')
        
        # 存在しない言語
        self.assertEqual(self.registry.get_run_command('nonexistent'), 'nonexistent')
    
    def test_get_compile_command(self):
        """コンパイルコマンド取得のテスト"""
        # C++のコンパイルコマンド
        cpp_compile = self.registry.get_compile_command('cpp')
        self.assertIsNotNone(cpp_compile)
        self.assertIn('g++', cpp_compile)
        
        # Pythonはコンパイル不要
        self.assertIsNone(self.registry.get_compile_command('python'))
        
        # 存在しない言語
        self.assertIsNone(self.registry.get_compile_command('nonexistent'))
    
    def test_register_custom_language(self):
        """カスタム言語登録のテスト"""
        custom_config = LanguageConfig(
            extension='test',
            run_command='test-runner',
            aliases=['tst']
        )
        
        self.registry.register_language('testlang', custom_config)
        
        self.assertTrue(self.registry.is_supported('testlang'))
        self.assertTrue(self.registry.is_supported('tst'))  # エイリアス
        self.assertEqual(self.registry.get_file_extension('testlang'), 'test')
        self.assertEqual(self.registry.get_run_command('testlang'), 'test-runner')
    
    def test_list_supported_languages(self):
        """サポート言語一覧のテスト"""
        languages = self.registry.list_supported_languages()
        
        self.assertIn('python', languages)
        self.assertIn('cpp', languages)
        self.assertIn('rust', languages)
        self.assertIn('java', languages)
        
        # エイリアスは含まれない
        self.assertNotIn('py', languages)
        self.assertNotIn('c++', languages)
    
    def test_language_config_aliasing(self):
        """エイリアスが同じ設定オブジェクトを参照することのテスト"""
        python_config = self.registry.get_language_config('python')
        py_config = self.registry.get_language_config('py')
        
        self.assertIs(python_config, py_config)  # 同じオブジェクト
    
    def test_global_registry(self):
        """グローバルレジストリのテスト"""
        global_registry = get_language_registry()
        
        self.assertIsInstance(global_registry, LanguageRegistry)
        self.assertTrue(global_registry.is_supported('python'))
    
    def test_register_custom_language_helper(self):
        """register_custom_languageヘルパー関数のテスト"""
        # カスタム言語を登録
        register_custom_language(
            name='mylang',
            extension='ml',
            run_command='mylang-run',
            compile_command='mylang-compile {source_file}',
            aliases=['ml']
        )
        
        global_registry = get_language_registry()
        
        self.assertTrue(global_registry.is_supported('mylang'))
        self.assertTrue(global_registry.is_supported('ml'))
        self.assertEqual(global_registry.get_file_extension('mylang'), 'ml')
        self.assertEqual(global_registry.get_run_command('mylang'), 'mylang-run')
        self.assertEqual(global_registry.get_compile_command('mylang'), 'mylang-compile {source_file}')
    
    def test_edge_cases(self):
        """エッジケースのテスト"""
        # 空の文字列
        self.assertFalse(self.registry.is_supported(''))
        self.assertEqual(self.registry.get_file_extension(''), 'txt')
        
        # 存在しない言語
        self.assertFalse(self.registry.is_supported('unknown_language'))
        self.assertEqual(self.registry.get_file_extension('unknown_language'), 'txt')
    
    def test_performance_with_many_languages(self):
        """多数の言語でのパフォーマンステスト"""
        import time
        
        # 100個の言語を登録
        for i in range(100):
            config = LanguageConfig(
                extension=f'ext{i}',
                run_command=f'run{i}',
                aliases=[f'alias{i}']
            )
            self.registry.register_language(f'lang{i}', config)
        
        # 検索パフォーマンステスト
        start_time = time.time()
        
        for i in range(100):
            self.assertTrue(self.registry.is_supported(f'lang{i}'))
            self.assertEqual(self.registry.get_file_extension(f'lang{i}'), f'ext{i}')
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 100個の言語検索が0.1秒以内に完了することを確認
        self.assertLess(execution_time, 0.1, 
                       f"Performance test failed: {execution_time:.3f}s for 100 language lookups")


if __name__ == '__main__':
    unittest.main()