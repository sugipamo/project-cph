#!/usr/bin/env python3
"""
品質チェッカー共通基底クラス
"""

import glob
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Set

from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger

from .progress_spinner import ProgressSpinner
from .quality_config_loader import QualityConfigLoader


class QualityCheckExecutor(ABC):
    def __init__(self, file_handler: FileHandler, logger: Logger, issues: List[str], verbose: bool = False):
        self.file_handler = file_handler
        self.logger = logger
        self.issues = issues
        self.verbose = verbose

        # 設定読み込み
        config_path = Path(__file__).parent.parent.parent / "configuration" / "quality_checks.json"
        self.config = QualityConfigLoader(str(config_path), file_handler)

    def get_target_files(self, excluded_categories: Optional[List[str]]) -> List[str]:
        """設定に基づいてチェック対象ファイルを取得"""
        target_files = []
        if excluded_categories is None:
            raise ValueError("excluded_categories must be provided explicitly")

        # 除外ディレクトリの収集
        excluded_dirs = set()
        for category in excluded_categories:
            excluded_dirs.update(self.config.get_excluded_directories(category))

        # 除外ファイルの収集
        excluded_files = set(self.config.get_excluded_files())

        # ファイル検索
        for target_dir in self.config.get_target_directories():
            for pattern in self.config.get_file_patterns():
                search_pattern = f"{target_dir}/{pattern}"
                for file_path in glob.glob(search_pattern, recursive=True):
                    if self._should_exclude_file(file_path, excluded_dirs, excluded_files):
                        continue
                    target_files.append(file_path)

        return sorted(target_files)

    def _should_exclude_file(self, file_path: str, excluded_dirs: Set[str], excluded_files: Set[str]) -> bool:
        """ファイルが除外対象かどうかを判定"""
        # 除外ディレクトリのチェック
        for excluded_dir in excluded_dirs:
            if excluded_dir in file_path:
                return True

        # 除外ファイルのチェック
        file_name = Path(file_path).name
        return file_name in excluded_files

    def get_relative_path(self, file_path: str) -> str:
        """相対パスを取得"""
        # 互換性維持: 既存のsrc/プレフィックス除去動作を維持
        if file_path.startswith('src/'):
            return file_path.replace('src/', '')
        return file_path

    def create_progress_spinner(self, message: str) -> ProgressSpinner:
        """プログレススピナーを作成"""
        return ProgressSpinner(message, self.logger)

    @abstractmethod
    def check(self) -> bool:
        """品質チェックを実行（各チェッカーで実装）"""
        pass
