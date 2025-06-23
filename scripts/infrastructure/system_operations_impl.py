"""システム操作関連モジュールのラッパー実装"""
import os
import sys
from pathlib import Path
from typing import List, Optional, Union

from .system_operations import SystemOperations


class SystemOperationsImpl(SystemOperations):
    """os, sys などの実装"""

    def get_cwd(self) -> str:
        return os.getcwd()

    def chdir(self, path: Union[str, Path]) -> None:
        os.chdir(path)

    def path_exists(self, path: Union[str, Path]) -> bool:
        return os.path.exists(path)

    def is_file(self, path: Union[str, Path]) -> bool:
        return os.path.isfile(path)

    def is_dir(self, path: Union[str, Path]) -> bool:
        return os.path.isdir(path)

    def makedirs(self, path: Union[str, Path], exist_ok: bool = False) -> None:
        os.makedirs(path, exist_ok=exist_ok)

    def remove(self, path: Union[str, Path]) -> None:
        os.remove(path)

    def rmdir(self, path: Union[str, Path]) -> None:
        os.rmdir(path)

    def listdir(self, path: Union[str, Path]) -> List[str]:
        return os.listdir(path)

    def get_env(self, key: str, default: Optional[str]) -> Optional[str]:
        # CLAUDE.mdルール適用: dict.get()使用禁止、明示的設定取得
        if key in os.environ:
            return os.environ[key]
        return default

    def set_env(self, key: str, value: str) -> None:
        os.environ[key] = value

    def exit(self, code: int) -> None:
        sys.exit(code)

    def get_argv(self) -> List[str]:
        return sys.argv.copy()
