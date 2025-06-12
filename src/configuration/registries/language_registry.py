"""言語設定の動的管理"""
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class LanguageConfig:
    """言語設定の定義"""
    extension: str
    run_command: str
    compile_command: Optional[str] = None
    aliases: List[str] = None

    def __post_init__(self):
        if self.aliases is None:
            object.__setattr__(self, 'aliases', [])


class LanguageRegistry:
    """言語設定の動的管理レジストリ"""

    def __init__(self):
        self._languages: Dict[str, LanguageConfig] = {}
        self._load_default_languages()

    def register_language(self, name: str, config: LanguageConfig) -> None:
        """新しい言語を登録

        Args:
            name: 言語名
            config: 言語設定
        """
        self._languages[name] = config

        # エイリアスも登録
        for alias in config.aliases:
            self._languages[alias] = config

    def get_language_config(self, name: str) -> Optional[LanguageConfig]:
        """言語設定を取得

        Args:
            name: 言語名またはエイリアス

        Returns:
            言語設定（存在しない場合はNone）
        """
        return self._languages.get(name)

    def get_file_extension(self, language: str) -> str:
        """言語に応じたファイル拡張子を取得

        Args:
            language: 言語名

        Returns:
            ファイル拡張子（デフォルト: 'txt'）
        """
        config = self.get_language_config(language)
        return config.extension if config else 'txt'

    def get_run_command(self, language: str) -> str:
        """言語に応じた実行コマンドを取得

        Args:
            language: 言語名

        Returns:
            実行コマンド（デフォルト: 言語名）
        """
        config = self.get_language_config(language)
        return config.run_command if config else language

    def get_compile_command(self, language: str) -> Optional[str]:
        """言語に応じたコンパイルコマンドを取得

        Args:
            language: 言語名

        Returns:
            コンパイルコマンド（存在しない場合はNone）
        """
        config = self.get_language_config(language)
        return config.compile_command if config else None

    def list_supported_languages(self) -> List[str]:
        """サポートされている言語の一覧を取得

        Returns:
            言語名のリスト（エイリアスは除外）
        """
        primary_languages = []
        seen_configs = set()

        for name, config in self._languages.items():
            if id(config) not in seen_configs:
                primary_languages.append(name)
                seen_configs.add(id(config))

        return sorted(primary_languages)

    def is_supported(self, language: str) -> bool:
        """言語がサポートされているかチェック

        Args:
            language: 言語名

        Returns:
            サポートされている場合True
        """
        return language in self._languages

    def _load_default_languages(self) -> None:
        """デフォルト言語設定を読み込み"""
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
            self.register_language(name, config)


# グローバルレジストリインスタンス
_global_registry = LanguageRegistry()


def get_language_registry() -> LanguageRegistry:
    """グローバル言語レジストリを取得"""
    return _global_registry


def register_custom_language(name: str, extension: str, run_command: str,
                           compile_command: Optional[str] = None,
                           aliases: Optional[List[str]] = None) -> None:
    """カスタム言語を簡単に登録するヘルパー関数

    Args:
        name: 言語名
        extension: ファイル拡張子
        run_command: 実行コマンド
        compile_command: コンパイルコマンド（オプション）
        aliases: エイリアスリスト（オプション）
    """
    config = LanguageConfig(
        extension=extension,
        run_command=run_command,
        compile_command=compile_command,
        aliases=aliases or []
    )
    _global_registry.register_language(name, config)
