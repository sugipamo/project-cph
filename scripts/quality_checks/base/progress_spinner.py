#!/usr/bin/env python3
"""
プログレススピナー共通実装
"""

from infrastructure.logger import Logger


class ProgressSpinner:
    def __init__(self, message: str, logger: Logger):
        self.message = message
        self.logger = logger

    def start(self):
        pass  # チェック中表示は不要

    def stop(self, success: bool = True):
        self.logger.info(f"{'✅' if success else '❌'} {self.message}")
