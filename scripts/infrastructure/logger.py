"""ロギング機能の抽象化と実装

Scripts配下で最も使用頻度の高い副作用であるprint関数を
依存性注入可能な形で抽象化
"""
# sysは依存性注入により削除 - system_operationsから受け取る
from abc import ABC, abstractmethod
from typing import Any


class Logger(ABC):
    """ロギングインターフェース"""

    @abstractmethod
    def info(self, message: str) -> None:
        """情報メッセージを出力"""
        pass

    @abstractmethod
    def warning(self, message: str) -> None:
        """警告メッセージを出力"""
        pass

    @abstractmethod
    def error(self, message: str) -> None:
        """エラーメッセージを出力"""
        pass

    @abstractmethod
    def debug(self, message: str) -> None:
        """デバッグメッセージを出力"""
        pass

    @abstractmethod
    def print(self, *args: Any, **kwargs: Any) -> None:
        """print関数の互換メソッド"""
        pass


class ConsoleLogger(Logger):
    """標準出力への実装
    
    副作用操作はsystem_operationsインターフェースを通じて注入される
    """

    def __init__(self, verbose: bool, system_operations):
        """初期化
        
        Args:
            verbose: 詳細モードを有効にするか
            system_operations: システム操作インターフェース
        """
        self.verbose = verbose
        self._system_operations = system_operations

    def info(self, message: str) -> None:
        if self._system_operations:
            self._system_operations.print_stdout(f"[INFO] {message}")
        else:
            print(f"[INFO] {message}")  # 互換性維持のための一時的な対応

    def warning(self, message: str) -> None:
        if self._system_operations:
            self._system_operations.print_stderr(f"[WARNING] {message}")
        else:
            print(f"[WARNING] {message}")  # 互換性維持のための一時的な対応

    def error(self, message: str) -> None:
        if self._system_operations:
            self._system_operations.print_stderr(f"[ERROR] {message}")
        else:
            print(f"[ERROR] {message}")  # 互換性維持のための一時的な対応

    def debug(self, message: str) -> None:
        if self.verbose:
            if self._system_operations:
                self._system_operations.print_stdout(f"[DEBUG] {message}")
            else:
                print(f"[DEBUG] {message}")  # 互換性維持のための一時的な対応

    def print(self, *args: Any, **kwargs: Any) -> None:
        """print関数の互換メソッド

        既存のコードからの移行を容易にするため、
        print関数と同じシグネチャを持つ
        """
        if self._system_operations and hasattr(self._system_operations, 'print_stdout_with_args'):
            self._system_operations.print_stdout_with_args(*args, **kwargs)
        else:
            print(*args, **kwargs)  # 互換性維持のための一時的な対応


class SilentLogger(Logger):
    """テスト用のサイレントロガー"""

    def __init__(self):
        self.messages = {
            'info': [],
            'warning': [],
            'error': [],
            'debug': [],
            'print': []
        }

    def info(self, message: str) -> None:
        self.messages['info'].append(message)

    def warning(self, message: str) -> None:
        self.messages['warning'].append(message)

    def error(self, message: str) -> None:
        self.messages['error'].append(message)

    def debug(self, message: str) -> None:
        self.messages['debug'].append(message)

    def print(self, *args: Any, **kwargs: Any) -> None:
        self.messages['print'].append((args, kwargs))


def create_logger(verbose: bool, silent: bool, system_operations) -> Logger:
    """ロガーのファクトリ関数

    Args:
        verbose: 詳細モードを有効にする
        silent: サイレントモード（テスト用）
        system_operations: システム操作インターフェース

    Returns:
        Logger: ロガーインスタンス
    """
    if silent:
        return SilentLogger()
    
    
    return ConsoleLogger(verbose, system_operations)
