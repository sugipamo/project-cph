from abc import ABC, abstractmethod
import os
import shutil
from src.execution_client.container.client import ContainerClient
from src.execution_client.container.pool import ContainerPool
from src.execution_client.container.image_manager import ContainerImageManager
from src.path_manager.unified_path_manager import UnifiedPathManager
from src.path_manager.file_operator import FileOperator
from pathlib import Path

HOST_PROJECT_ROOT = os.path.abspath(".")
CONTAINER_WORKSPACE = "/workspace"

class TestEnvFileOpsMixin:
    def prepare_source_code(self, contest_name, problem_name, language_name):
        temp_dir = ".temp"
        if language_name == "rust":
            import glob
            src_dir = self.upm.contest_current("rust")
            dst_dir = os.path.join(temp_dir, "rust")
            if self.file_operator:
                if not self.file_operator.exists(temp_dir):
                    self.file_operator.makedirs(temp_dir)
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
        elif language_name in ("python", "pypy"):
            src = self.upm.contest_current(language_name, "main.py")
            dst_dir = os.path.join(temp_dir, language_name)
            dst = os.path.join(dst_dir, "main.py")
            if self.file_operator:
                if not self.file_operator.exists(dst_dir):
                    self.file_operator.makedirs(dst_dir)
                self.file_operator.copy(src, dst)
            else:
                os.makedirs(dst_dir, exist_ok=True)
                shutil.copy(src, dst)
            return dst
        else:
            src = self.upm.contest_current(language_name, "main.py")
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
        test_dir = self.upm.contest_current("test")
        temp_test_dir = os.path.join(temp_dir, "test")
        if self.file_operator:
            if not self.file_operator.exists(temp_test_dir):
                self.file_operator.copytree(test_dir, temp_test_dir)
        else:
            if os.path.exists(test_dir):
                shutil.copytree(test_dir, temp_test_dir, dirs_exist_ok=True)
        return temp_test_dir

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

class DockerTestExecutionEnvironment(TestEnvFileOpsMixin, TestExecutionEnvironment):
    def __init__(self, file_manager, handlers=None):
        self.file_manager = file_manager
        self.file_operator = file_manager.file_operator if file_manager and hasattr(file_manager, 'file_operator') else None
        self.ctl = ContainerClient()
        from src.environment.test_language_handler import HANDLERS as DEFAULT_HANDLERS
        self.handlers = handlers if handlers is not None else DEFAULT_HANDLERS
        self.pool = ContainerPool({})
        # .tempも含めたマウントリストで初期化
        mounts = [
            (Path(HOST_PROJECT_ROOT), Path(CONTAINER_WORKSPACE)),
            (Path(os.path.abspath(".temp")), Path("/workspace/.temp"))
        ]
        self.unified_path_manager = UnifiedPathManager(HOST_PROJECT_ROOT, CONTAINER_WORKSPACE, mounts=mounts)
        self.upm = UnifiedPathManager(HOST_PROJECT_ROOT, CONTAINER_WORKSPACE, mounts=mounts)

    def to_container_path(self, host_path: str) -> str:
        return str(self.unified_path_manager.to_container_path(os.path.abspath(host_path)))

    def to_host_path(self, container_path: str) -> str:
        return str(self.unified_path_manager.to_host_path(container_path))

    def run_test_case(self, language_name, container, in_file, source_path, retry=3):
        handler = self.handlers[language_name]
        image = ContainerImageManager().ensure_image("ojtools") if container.startswith("cph_ojtools") else language_name
        ctl = self.ctl
        stdout = stderr = ""
        cont_in_file = self.to_container_path(in_file)
        cont_source_path = self.to_container_path(source_path)
        for attempt in range(retry):
            ok, stdout, stderr = handler.run(ctl, container, cont_in_file, cont_source_path)
            if ok:
                break
            else:
                print(f"[WARN] exec失敗: {container} (attempt {attempt+1})")
                ctl.remove_container(container)
                ctl.start_container(container, image, {})
        return ok, stdout, stderr, attempt+1

    def adjust_containers(self, requirements, contest_name=None, problem_name=None, language_name=None):
        """必要なコンテナ数・ボリュームを調整し、system_info.jsonも更新する。"""
        containers = self.pool.adjust(requirements)
        # system_info.jsonの更新もここで行う
        if contest_name and problem_name and language_name:
            from src.info_json_manager import InfoJsonManager
            info_path = self.upm.info_json()
            manager = InfoJsonManager(info_path)
            manager.data["contest_name"] = contest_name
            manager.data["problem_name"] = problem_name
            manager.data["language_name"] = language_name
            manager.data["containers"] = containers
            manager.save()
        return containers

    def download_testcases(self, url, test_dir_host):
        # ojtoolsコンテナでoj downloadを実行し、テストケースを取得
        info_path = self.upm.info_json()
        from src.info_json_manager import InfoJsonManager
        manager = InfoJsonManager(info_path)
        ojtools_list = manager.get_containers(type="ojtools")
        if not ojtools_list:
            raise RuntimeError("ojtools用コンテナがsystem_info.jsonにありません")
        ojtools_name = ojtools_list[0]["name"]
        ctl = self.ctl
        if not ctl.is_container_running(ojtools_name):
            ctl.run_container(ojtools_name, ContainerImageManager().ensure_image("ojtools"), {})
        # test_dir_hostの親ディレクトリを取得
        self.unified_path_manager.to_container_path(test_dir_host)

    def submit_via_ojtools(self, args, volumes, workdir):
        # ojtoolsコンテナでoj submitを実行
        info_path = self.upm.info_json()
        from src.info_json_manager import InfoJsonManager
        manager = InfoJsonManager(info_path)
        ojtools_list = manager.get_containers(type="ojtools")
        if not ojtools_list:
            raise RuntimeError("ojtools用コンテナがsystem_info.jsonにありません")
        ojtools_name = ojtools_list[0]["name"]
        ctl = self.ctl
        if not ctl.is_container_running(ojtools_name):
            ctl.start_container(ojtools_name, ContainerImageManager().ensure_image("ojtools"), {})
        ok, stdout, stderr = ctl.exec_in_container(ojtools_name, ["oj"] + args)
        return ok, stdout, stderr 