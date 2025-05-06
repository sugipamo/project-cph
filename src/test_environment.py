from abc import ABC, abstractmethod
import os
import shutil
from src.commands.test_language_handler import HANDLERS
from src.commands.info_json_manager import InfoJsonManager
from src.commands.test_result_formatter import TestResultFormatter
from src.docker.ctl import DockerCtl

HOST_PROJECT_ROOT = os.path.abspath(".")
CONTAINER_WORKSPACE = "/workspace"

class TestExecutionEnvironment(ABC):
    @abstractmethod
    def prepare_source_code(self, contest_name, problem_name, language_name):
        pass

    @abstractmethod
    def prepare_test_cases(self, contest_name, problem_name):
        pass

    @abstractmethod
    def to_container_path(self, host_path: str) -> str:
        pass

    @abstractmethod
    def to_host_path(self, container_path: str) -> str:
        pass

    @abstractmethod
    def run_test_case(self, language_name, container, in_file, source_path, retry=2):
        pass

class DockerTestExecutionEnvironment(TestExecutionEnvironment):
    def __init__(self, file_manager, handlers=None):
        self.file_manager = file_manager
        self.file_operator = file_manager.file_operator if file_manager and hasattr(file_manager, 'file_operator') else None
        self.ctl = DockerCtl()
        from src.commands.test_language_handler import HANDLERS as DEFAULT_HANDLERS
        self.handlers = handlers if handlers is not None else DEFAULT_HANDLERS

    def prepare_source_code(self, contest_name, problem_name, language_name):
        temp_dir = ".temp"
        src = f"contest_current/{language_name}/main.py"
        dst = os.path.join(temp_dir, "main.py")
        if self.file_operator:
            if not self.file_operator.exists(temp_dir):
                self.file_operator.makedirs(temp_dir)
            self.file_operator.copy(src, dst)
        else:
            os.makedirs(temp_dir, exist_ok=True)
            shutil.copy(src, dst)
        return dst

    def prepare_test_cases(self, contest_name, problem_name):
        temp_dir = ".temp"
        test_dir = "contest_current/test"
        temp_test_dir = os.path.join(temp_dir, "test")
        if self.file_operator:
            if not self.file_operator.exists(temp_test_dir):
                self.file_operator.copytree(test_dir, temp_test_dir)
        else:
            if os.path.exists(test_dir):
                shutil.copytree(test_dir, temp_test_dir, dirs_exist_ok=True)
        return temp_test_dir

    def to_container_path(self, host_path: str) -> str:
        return str(host_path).replace(HOST_PROJECT_ROOT, CONTAINER_WORKSPACE, 1)

    def to_host_path(self, container_path: str) -> str:
        return str(container_path).replace(CONTAINER_WORKSPACE, HOST_PROJECT_ROOT, 1)

    def run_test_case(self, language_name, container, in_file, source_path, retry=3):
        handler = self.handlers[language_name]
        image = "oj" if container.startswith("cph_ojtools") else language_name
        ctl = self.ctl
        stdout = stderr = ""
        for attempt in range(retry):
            ok, stdout, stderr = handler.run(ctl, container, in_file, source_path)
            if ok:
                break
            else:
                print(f"[WARN] exec失敗: {container} (attempt {attempt+1})")
                ctl.remove_container(container)
                ctl.start_container(container, image, {})
        return ok, stdout, stderr, attempt+1 