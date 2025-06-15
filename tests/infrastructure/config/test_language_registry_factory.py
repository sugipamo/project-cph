"""Tests for language registry factory."""
import pytest

from src.infrastructure.config.language_registry_factory import create_default_language_registry
from src.configuration.registries.language_registry import LanguageConfig, LanguageRegistry


class TestLanguageRegistryFactory:
    """Test language registry factory functions."""
    
    def test_create_default_language_registry_returns_registry(self):
        registry = create_default_language_registry()
        assert isinstance(registry, LanguageRegistry)
    
    def test_default_registry_contains_python(self):
        registry = create_default_language_registry()
        
        # Python設定の確認
        python_config = registry.get_language_config('python')
        assert python_config is not None
        assert python_config.extension == 'py'
        assert python_config.run_command == 'python3'
        assert python_config.compile_command is None
        assert 'py' in python_config.aliases
        assert 'python3' in python_config.aliases
    
    def test_default_registry_contains_cpp(self):
        registry = create_default_language_registry()
        
        cpp_config = registry.get_language_config('cpp')
        assert cpp_config is not None
        assert cpp_config.extension == 'cpp'
        assert cpp_config.run_command == './main'
        assert cpp_config.compile_command == 'g++ -o main {source_file}'
        assert 'c++' in cpp_config.aliases
        assert 'cxx' in cpp_config.aliases
    
    def test_default_registry_contains_rust(self):
        registry = create_default_language_registry()
        
        rust_config = registry.get_language_config('rust')
        assert rust_config is not None
        assert rust_config.extension == 'rs'
        assert rust_config.run_command == './main'
        assert rust_config.compile_command == 'rustc -o main {source_file}'
        assert 'rs' in rust_config.aliases
    
    def test_default_registry_contains_java(self):
        registry = create_default_language_registry()
        
        java_config = registry.get_language_config('java')
        assert java_config is not None
        assert java_config.extension == 'java'
        assert java_config.run_command == 'java Main'
        assert java_config.compile_command == 'javac {source_file}'
        assert 'jvm' in java_config.aliases
    
    def test_default_registry_contains_javascript(self):
        registry = create_default_language_registry()
        
        js_config = registry.get_language_config('javascript')
        assert js_config is not None
        assert js_config.extension == 'js'
        assert js_config.run_command == 'node'
        assert js_config.compile_command is None
        assert 'js' in js_config.aliases
        assert 'node' in js_config.aliases
    
    def test_default_registry_contains_typescript(self):
        registry = create_default_language_registry()
        
        ts_config = registry.get_language_config('typescript')
        assert ts_config is not None
        assert ts_config.extension == 'ts'
        assert ts_config.run_command == 'ts-node'
        assert ts_config.compile_command is None
        assert 'ts' in ts_config.aliases
    
    def test_default_registry_contains_go(self):
        registry = create_default_language_registry()
        
        go_config = registry.get_language_config('go')
        assert go_config is not None
        assert go_config.extension == 'go'
        assert go_config.run_command == 'go run'
        assert go_config.compile_command is None
        assert 'golang' in go_config.aliases
    
    def test_default_registry_contains_kotlin(self):
        registry = create_default_language_registry()
        
        kotlin_config = registry.get_language_config('kotlin')
        assert kotlin_config is not None
        assert kotlin_config.extension == 'kt'
        assert kotlin_config.run_command == 'kotlin MainKt'
        assert kotlin_config.compile_command == 'kotlinc {source_file} -include-runtime -d main.jar'
        assert 'kt' in kotlin_config.aliases
    
    def test_all_languages_have_required_fields(self):
        registry = create_default_language_registry()
        
        # 登録されているすべての言語を確認
        expected_languages = ['python', 'cpp', 'rust', 'java', 'javascript', 'typescript', 'go', 'kotlin']
        
        for lang in expected_languages:
            config = registry.get_language_config(lang)
            # 必須フィールドの確認
            assert config.extension is not None
            assert config.run_command is not None
            assert isinstance(config.aliases, list)
            assert len(config.aliases) > 0
    
    def test_alias_resolution(self):
        registry = create_default_language_registry()
        
        # エイリアスでも言語を取得できることを確認
        assert registry.get_language_config('py') is not None  # Python alias
        assert registry.get_language_config('c++') is not None  # C++ alias
        assert registry.get_language_config('rs') is not None  # Rust alias
        assert registry.get_language_config('js') is not None  # JavaScript alias
        assert registry.get_language_config('golang') is not None  # Go alias
    
    def test_registry_independence(self):
        # 複数回作成しても独立したインスタンスが返されることを確認
        registry1 = create_default_language_registry()
        registry2 = create_default_language_registry()
        
        assert registry1 is not registry2
        
        # 片方に新しい言語を追加しても、もう片方には影響しない
        registry1.register_language('custom', LanguageConfig(
            extension='custom',
            run_command='custom-run',
            aliases=[]
        ))
        
        assert registry1.get_language_config('custom') is not None
        assert registry2.get_language_config('custom') is None
    
    def test_compile_command_format(self):
        registry = create_default_language_registry()
        
        # コンパイルコマンドに{source_file}プレースホルダーが含まれていることを確認
        cpp_config = registry.get_language_config('cpp')
        assert '{source_file}' in cpp_config.compile_command
        
        rust_config = registry.get_language_config('rust')
        assert '{source_file}' in rust_config.compile_command
        
        java_config = registry.get_language_config('java')
        assert '{source_file}' in java_config.compile_command
        
        kotlin_config = registry.get_language_config('kotlin')
        assert '{source_file}' in kotlin_config.compile_command