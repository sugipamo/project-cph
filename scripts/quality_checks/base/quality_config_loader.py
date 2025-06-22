#!/usr/bin/env python3
"""
品質チェッカー設定読み込みユーティリティ
"""

import json
from pathlib import Path
from typing import Any, Dict, List


class QualityConfigLoader:
    def __init__(self, config_path: str):
        self._config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not self._config_path.exists():
            raise FileNotFoundError(f"設定ファイルが存在しません: {self._config_path}")

        with open(self._config_path, encoding='utf-8') as f:
            return json.load(f)

    def get_target_directories(self) -> List[str]:
        """チェック対象ディレクトリを取得"""
        return self._config["target_directories"]

    def get_file_patterns(self) -> List[str]:
        """ファイルパターンを取得"""
        return self._config["file_patterns"]

    def get_excluded_directories(self, category: str) -> List[str]:
        """除外ディレクトリを取得"""
        excluded_dirs = self._config["excluded_directories"]
        if category not in excluded_dirs:
            raise KeyError(f"除外ディレクトリのカテゴリが設定されていません: {category}")
        return excluded_dirs[category]

    def get_excluded_files(self) -> List[str]:
        """除外ファイルを取得"""
        return self._config["excluded_files"]

    def get_script_path(self, script_name: str) -> str:
        """スクリプトパスを取得"""
        script_paths = self._config["script_paths"]
        if script_name not in script_paths:
            raise KeyError(f"スクリプトパスが設定されていません: {script_name}")
        return script_paths[script_name]

    def get_allowed_directories(self, category: str) -> List[str]:
        """許可ディレクトリを取得"""
        allowed_dirs = self._config["allowed_directories"]
        if category not in allowed_dirs:
            raise KeyError(f"許可ディレクトリのカテゴリが設定されていません: {category}")
        return allowed_dirs[category]
