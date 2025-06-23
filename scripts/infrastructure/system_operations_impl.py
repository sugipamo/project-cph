"""システム操作関連モジュールのラッパー実装"""
# os, sysは依存性注入により削除 - 各プロバイダーから受け取る
from pathlib import Path
from typing import List, Optional, Union

from .system_operations import SystemOperations


class SystemOperationsImpl(SystemOperations):
    """os, sys などの実装

    副作用操作はos_provider, sys_provider等のインターフェースを通じて注入される
    """

    def __init__(self, os_provider, sys_provider):
        """初期化

        Args:
            os_provider: OS操作プロバイダー
            sys_provider: sys操作プロバイダー
        """
        self._os_provider = os_provider
        self._sys_provider = sys_provider

    def get_cwd(self) -> str:
        return self._os_provider.getcwd()

    def chdir(self, path: Union[str, Path]) -> None:
        self._os_provider.chdir(path)

    def path_exists(self, path: Union[str, Path]) -> bool:
        return self._os_provider.path_exists(path)

    def is_file(self, path: Union[str, Path]) -> bool:
        return self._os_provider.isfile(path)

    def is_dir(self, path: Union[str, Path]) -> bool:
        return self._os_provider.isdir(path)

    def makedirs(self, path: Union[str, Path], exist_ok: bool) -> None:
        self._os_provider.makedirs(path, exist_ok)

    def remove(self, path: Union[str, Path]) -> None:
        self._os_provider.remove(path)

    def rmdir(self, path: Union[str, Path]) -> None:
        self._os_provider.rmdir(path)

    def listdir(self, path: Union[str, Path]) -> List[str]:
        return self._os_provider.listdir(path)

    def get_env(self, key: str) -> Optional[str]:
        # CLAUDE.mdルール適用: デフォルト値禁止、呼び出し元で処理
        return self._os_provider.get_env(key)

    def set_env(self, key: str, value: str) -> None:
        self._os_provider.set_env(key, value)

    def exit(self, code: int) -> None:
        self._sys_provider.exit(code)

    def get_argv(self) -> List[str]:
        return self._sys_provider.get_argv()

    def print_stdout(self, message: str) -> None:
        print(message)
