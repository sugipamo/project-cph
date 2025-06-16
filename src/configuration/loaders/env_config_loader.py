"""環境設定(env.json)読み込み専用クラス"""
import json
from pathlib import Path
from typing import Any, Dict, Tuple


class EnvConfigLoader:
    """env.jsonファイルの読み込み専用クラス

    責任:
    - contest_env/ ディレクトリからのenv.json読み込み
    - shared/env.json と言語固有env.jsonの読み込み
    - エラーハンドリング
    """

    def __init__(self, contest_env_dir: Path):
        """初期化

        Args:
            contest_env_dir: contest_envディレクトリのパス
        """
        self.contest_env_dir = contest_env_dir

    def load_env_configs(self, language: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """環境設定の読み込み

        Args:
            language: 対象言語

        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: (shared設定, 言語固有設定)
        """
        shared_config = self._load_shared_config()
        language_config = self._load_language_config(language)

        return shared_config, language_config

    def _load_shared_config(self) -> Dict[str, Any]:
        """共有設定の読み込み

        Returns:
            Dict[str, Any]: 共有設定辞書
        """
        shared_path = self.contest_env_dir / "shared" / "env.json"
        return self._load_json_file(shared_path)

    def _load_language_config(self, language: str) -> Dict[str, Any]:
        """言語固有設定の読み込み

        Args:
            language: 対象言語

        Returns:
            Dict[str, Any]: 言語固有設定辞書
        """
        language_path = self.contest_env_dir / language / "env.json"
        return self._load_json_file(language_path)

    def get_available_languages(self) -> list[str]:
        """利用可能な言語一覧を取得

        Returns:
            list[str]: 言語名のリスト
        """
        languages = []

        if not self.contest_env_dir.exists():
            return languages

        try:
            for item in self.contest_env_dir.iterdir():
                if item.is_dir() and item.name != "shared":
                    env_file = item / "env.json"
                    if env_file.exists():
                        languages.append(item.name)
        except (OSError, PermissionError):
            pass

        return sorted(languages)

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
