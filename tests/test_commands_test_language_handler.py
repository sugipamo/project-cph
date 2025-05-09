import pytest
from src.environment.test_language_handler import RustTestHandler
from src.path_manager.unified_path_manager import UnifiedPathManager
import os

class DummyCtl:
    def exec_in_container(self, container, cmd, realtime=False):
        return True, 'ok', ''

class DummyCtlFail:
    def exec_in_container(self, container, cmd, realtime=False):
        return False, '', 'error'