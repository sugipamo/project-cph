"""Infrastructure層での設定ファイル読み込みサービス

Configuration層の純粋化のため、副作用を伴う設定ファイル読み込みを
Infrastructure層に移動します。
"""
from pathlib import Path
from typing import Any, Dict

from old_src.infrastructure.di_container import DIContainer, DIKey


class ConfigLoaderService:
    """設定ファイル読み込みの副作用をInfrastructure層で処理"""

    def __init__(self, container: DIContainer):
        """Infrastructure層のプロバイダーを使用して初期化"""
        self._json_provider = container.resolve(DIKey.JSON_PROVIDER)
        self._os_provider = container.resolve(DIKey.OS_PROVIDER)
        self._file_driver = container.resolve(DIKey.FILE_DRIVER)

    def load_config_files(self, system_dir: str, env_dir: str, language: str) -> Dict[str, Any]:
        """設定ファイルを読み込み、マージされた辞書を返す

        Args:
            system_dir: システム設定ディレクトリ
            env_dir: 環境設定ディレクトリ
            language: 言語設定

        Returns:
            マージされた設定辞書
        """
        merged_config = {}

        # システム設定の読み込み
        system_config = self._load_system_configs(Path(system_dir))
        merged_config.update(system_config)

        # 環境設定の読み込み
        env_config = self._load_env_configs(Path(env_dir), language)
        merged_config.update(env_config)

        return merged_config

    def _load_system_configs(self, system_dir: Path) -> Dict[str, Any]:
        """システム設定ファイルを読み込み"""
        system_config = {}

        if not system_dir.exists():
            return system_config

        for json_file in system_dir.glob("*.json"):
            try:
                config_data = self._load_json_file(str(json_file))
                system_config.update(config_data)
            except Exception:
                # エラーログは後でLoggerが利用可能になってから出力
                pass

        return system_config

    def _load_env_configs(self, env_dir: Path, language: str) -> Dict[str, Any]:
        """環境設定ファイルを読み込み"""
        env_config = {}

        # 共有設定
        shared_config_path = env_dir / "shared" / "env.json"
        if shared_config_path.exists():
            try:
                shared_config = self._load_json_file(str(shared_config_path))
                env_config.update(shared_config)
            except Exception:
                pass

        # 言語固有設定
        language_config_path = env_dir / language / "env.json"
        if language_config_path.exists():
            try:
                language_config = self._load_json_file(str(language_config_path))
                env_config.update(language_config)
            except Exception:
                pass

        return env_config

    def _load_json_file(self, file_path: str) -> Dict[str, Any]:
        """JSONファイルを読み込み"""
        try:
            file_content = self._file_driver.read_file(file_path)
            return self._json_provider.loads(file_content)
        except Exception:
            # Infrastructure層での例外処理
            return {}
