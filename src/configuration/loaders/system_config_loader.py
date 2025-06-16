"""システム設定読み込み専用クラス"""
import json
from pathlib import Path
from typing import Any, Dict


class SystemConfigLoader:
    """システム設定ファイルの読み込み専用クラス

    責任:
    - config/system/ ディレクトリからの設定ファイル読み込み
    - エラーハンドリング
    - ファイル存在チェック
    """

    def __init__(self, system_config_dir: Path):
        """初期化

        Args:
            system_config_dir: システム設定ディレクトリのパス
        """
        self.system_config_dir = system_config_dir

    def load_system_configs(self) -> Dict[str, Any]:
        """システム設定の読み込み

        Returns:
            Dict[str, Any]: システム設定辞書
        """
        system_config = {}

        if not self.system_config_dir.exists():
            return system_config

        # 読み込むシステム設定ファイル
        system_files = [
            "docker_security.json",
            "docker_defaults.json",
            "file_patterns.json",
            "languages.json",
            "timeout.json"
        ]

        for filename in system_files:
            file_path = self.system_config_dir / filename
            config_data = self._load_json_file(file_path)
            if config_data:
                system_config.update(config_data)

        return system_config

    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """JSONファイルを読み込み

        Args:
            file_path: ファイルパス

        Returns:
            Dict[str, Any]: 読み込まれた設定データ（失敗時は空辞書）
        """
        try:
            if file_path.exists():
                with open(file_path, encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError):
            # ログ出力などの処理は呼び出し側で処理
            pass

        return {}
