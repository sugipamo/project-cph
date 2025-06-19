"""ロギング機能の抽象化と実装

Scripts配下で最も使用頻度の高い副作用であるprint関数を
依存性注入可能な形で抽象化
"""
import sys
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
    """標準出力への実装"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def info(self, message: str) -> None:
        print(f"[INFO] {message}")

    def warning(self, message: str) -> None:
        print(f"[WARNING] {message}", file=sys.stderr)

    def error(self, message: str) -> None:
        print(f"[ERROR] {message}", file=sys.stderr)

    def debug(self, message: str) -> None:
        if self.verbose:
            print(f"[DEBUG] {message}")

    def print(self, *args: Any, **kwargs: Any) -> None:
        """print関数の互換メソッド

        既存のコードからの移行を容易にするため、
        print関数と同じシグネチャを持つ
        """
        print(*args, **kwargs)


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


def create_logger(verbose: bool = False, silent: bool = False) -> Logger:
    """ロガーのファクトリ関数

    Args:
        verbose: 詳細モードを有効にする
        silent: サイレントモード（テスト用）

    Returns:
        Logger: ロガーインスタンス
    """
    if silent:
        return SilentLogger()
    return ConsoleLogger(verbose=verbose)
