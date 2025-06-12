"""言語レジストリファクトリー - 副作用を分離した言語レジストリ作成"""
from src.configuration.registries.language_registry import LanguageRegistry, LanguageConfig


def create_default_language_registry() -> LanguageRegistry:
    """デフォルト言語レジストリを作成（純粋関数）
    
    副作用なしで言語レジストリを作成。
    既存のLanguageRegistry._load_default_languages()の副作用を分離。
    
    Returns:
        設定済み言語レジストリ
    """
    registry = LanguageRegistry()
    
    # デフォルト言語設定（純粋データ）
    default_languages = {
        'python': LanguageConfig(
            extension='py',
            run_command='python3',
            aliases=['py', 'python3']
        ),
        'cpp': LanguageConfig(
            extension='cpp',
            run_command='./main',
            compile_command='g++ -o main {source_file}',
            aliases=['c++', 'cxx']
        ),
        'rust': LanguageConfig(
            extension='rs',
            run_command='./main',
            compile_command='rustc -o main {source_file}',
            aliases=['rs']
        ),
        'java': LanguageConfig(
            extension='java',
            run_command='java Main',
            compile_command='javac {source_file}',
            aliases=['jvm']
        ),
        'javascript': LanguageConfig(
            extension='js',
            run_command='node',
            aliases=['js', 'node']
        ),
        'typescript': LanguageConfig(
            extension='ts',
            run_command='ts-node',
            aliases=['ts']
        ),
        'go': LanguageConfig(
            extension='go',
            run_command='go run',
            aliases=['golang']
        ),
        'kotlin': LanguageConfig(
            extension='kt',
            run_command='kotlin MainKt',
            compile_command='kotlinc {source_file} -include-runtime -d main.jar',
            aliases=['kt']
        )
    }
    
    for name, config in default_languages.items():
        registry.register_language(name, config)
    
    return registry