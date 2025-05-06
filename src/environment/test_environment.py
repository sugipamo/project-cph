from abc import ABC, abstractmethod
import os
import shutil
from src.environment.test_language_handler import HANDLERS
from src.info_json_manager import InfoJsonManager
from src.commands.test_result_formatter import TestResultFormatter
from src.docker.ctl import DockerCtl
from src.docker.pool import DockerPool
from src.docker.path_mapper import DockerPathMapper

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
        from src.environment.test_language_handler import HANDLERS as DEFAULT_HANDLERS
        self.handlers = handlers if handlers is not None else DEFAULT_HANDLERS
        self.pool = DockerPool()
        self.path_mapper = DockerPathMapper(HOST_PROJECT_ROOT, "/workspace")

    def prepare_source_code(self, contest_name, problem_name, language_name):
        temp_dir = ".temp"
        if language_name == "rust":
            import glob
            src_dir = f"contest_current/rust"
            dst_dir = os.path.join(temp_dir, "rust")
            if self.file_operator:
                if not self.file_operator.exists(temp_dir):
                    self.file_operator.makedirs(temp_dir)
                # .temp/rustが存在する場合、target以外を削除
                if self.file_operator.exists(dst_dir):
                    for item in self.file_operator.resolve_path(dst_dir).iterdir():
                        if item.name != "target":
                            if item.is_dir():
                                self.file_operator.rmtree(item)
                            else:
                                item.unlink()
                else:
                    self.file_operator.makedirs(dst_dir)
                self.file_operator.copytree(src_dir, dst_dir)
            else:
                os.makedirs(temp_dir, exist_ok=True)
                # .temp/rustが存在する場合、target以外を削除
                if os.path.exists(dst_dir):
                    for item in glob.glob(os.path.join(dst_dir, "*")):
                        if os.path.basename(item) != "target":
                            if os.path.isdir(item):
                                shutil.rmtree(item)
                            else:
                                os.remove(item)
                else:
                    os.makedirs(dst_dir, exist_ok=True)
                shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
            return dst_dir
        else:
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
        return self.path_mapper.to_container_path(host_path)

    def to_host_path(self, container_path: str) -> str:
        return self.path_mapper.to_host_path(container_path)

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

    def adjust_containers(self, requirements, contest_name=None, problem_name=None, language_name=None):
        """必要なコンテナ数・ボリュームを調整し、info.jsonも更新する。"""
        containers = self.pool.adjust(requirements)
        # info.jsonの更新もここで行う
        if contest_name and problem_name and language_name:
            from src.info_json_manager import InfoJsonManager
            info_path = "contest_current/info.json"
            manager = InfoJsonManager(info_path)
            manager.data["contest_name"] = contest_name
            manager.data["problem_name"] = problem_name
            manager.data["language_name"] = language_name
            manager.data["containers"] = containers
            manager.save()
        return containers 