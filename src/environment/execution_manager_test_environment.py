from src.environment.test_environment import TestExecutionEnvironment, TestEnvFileOpsMixin
from execution_client.execution_manager import ExecutionManager
from src.path_manager.unified_path_manager import UnifiedPathManager
import os
import shutil

class ExecutionManagerTestEnvironment(TestEnvFileOpsMixin, TestExecutionEnvironment):
    def __init__(self, file_manager, manager, handlers=None):
        self.file_manager = file_manager
        self.manager = manager
        self.file_operator = file_manager.file_operator if file_manager and hasattr(file_manager, 'file_operator') else None
        from src.environment.test_language_handler import HANDLERS as DEFAULT_HANDLERS
        self.handlers = handlers if handlers is not None else DEFAULT_HANDLERS
        self.unified_path_manager = UnifiedPathManager()
        self.upm = UnifiedPathManager()

    def to_container_path(self, host_path: str) -> str:
        return str(self.unified_path_manager.to_container_path(host_path))

    def to_host_path(self, container_path: str) -> str:
        return str(self.unified_path_manager.to_host_path(container_path))

    def run_test_case(self, language_name, name, in_file, source_path, retry=3):
        handler = self.handlers[language_name]
        for attempt in range(retry):
            ok, stdout, stderr = handler.run(self.manager, name, in_file, source_path)
            if ok:
                break
        return ok, stdout, stderr, attempt+1

    def adjust_containers(self, requirements, contest_name=None, problem_name=None, language_name=None):
        # ローカル実行では特に何もしないが、インターフェース維持のためダミー返却
        return [] 