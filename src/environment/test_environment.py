from abc import ABC, abstractmethod
import os
import shutil
from src.execution_client.container.client import ContainerClient
from src.execution_client.container.pool import ContainerPool
from src.execution_client.container.image_manager import ContainerImageManager
from src.path_manager.unified_path_manager import UnifiedPathManager
from src.file.file_operator import FileOperator
from pathlib import Path
from src.file.info_json_manager import InfoJsonManager
from src.language_env.profiles import get_profile
from src.language_env.constants import CONTAINER_WORKSPACE
from src.path_manager.common_paths import HOST_PROJECT_ROOT
from src.execution_client.execution_manager import ExecutionManager
from src.execution_client.local import LocalAsyncClient

class TestEnvFileOpsMixin:
    def prepare_source_code(self, contest_name, problem_name, language_name):
        profile = get_profile(language_name, 'local')
        temp_dir = Path(profile.env_config.temp_dir)
        if language_name == "rust":
            import glob
            src_dir = self.upm.contest_current("rust")
            dst_dir = temp_dir / "rust"
            if self.file_operator:
                if not self.file_operator.exists(dst_dir):
                    self.file_operator.makedirs(dst_dir)
                if self.file_operator.exists(dst_dir):
                    resolved = self.file_operator.resolve_path(dst_dir)
                    resolved_path = Path(resolved)
                    for item in resolved_path.iterdir():
                        if item.name != "target":
                            if item.is_dir():
                                self.file_operator.rmtree(item)
                            else:
                                item.unlink()
                else:
                    self.file_operator.makedirs(dst_dir)
                self.file_operator.copytree(src_dir, dst_dir)
            else:
                dst_dir.mkdir(parents=True, exist_ok=True)
                if dst_dir.exists():
                    for item in dst_dir.iterdir():
                        if item.name != "target":
                            if item.is_dir():
                                shutil.rmtree(item)
                            else:
                                item.unlink()
                else:
                    dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
            return str(dst_dir)
        elif language_name in ("python", "pypy"):
            src = self.upm.contest_current(language_name, "main.py")
            dst_dir = temp_dir / language_name
            dst = dst_dir / "main.py"
            if self.file_operator:
                if not self.file_operator.exists(dst_dir):
                    self.file_operator.makedirs(dst_dir)
                self.file_operator.copy(src, dst)
            else:
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy(src, dst)
            return str(dst)
        else:
            src = self.upm.contest_current(language_name, "main.py")
            dst = temp_dir / "main.py"
            if self.file_operator:
                if not self.file_operator.exists(temp_dir):
                    self.file_operator.makedirs(temp_dir)
                self.file_operator.copy(src, dst)
            else:
                temp_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy(src, dst)
            return str(dst)

    def prepare_test_cases(self, contest_name, problem_name):
        profile = get_profile("python", 'local')  # テストケースは言語依存しない場合はpythonでOK
        temp_dir = Path(profile.env_config.temp_dir)
        test_dir = self.upm.contest_current("test")
        temp_test_dir = temp_dir / "test"
        if self.file_operator:
            if not self.file_operator.exists(temp_test_dir):
                self.file_operator.copytree(test_dir, temp_test_dir)
        else:
            if test_dir.exists():
                shutil.copytree(test_dir, temp_test_dir, dirs_exist_ok=True)
        return str(temp_test_dir)

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
    def __init__(self, file_manager, handlers=None, env_type='local', ctl=None, exec_manager=None):
        self.file_manager = file_manager
        self.file_operator = file_manager.file_operator if file_manager and hasattr(file_manager, 'file_operator') else None
        self.ctl = ctl if ctl is not None else ContainerClient()
        from src.environment.test_language_handler import HANDLERS as DEFAULT_HANDLERS
        self.handlers = handlers if handlers is not None else DEFAULT_HANDLERS
        self.pool = ContainerPool({})
        temp_dir = get_profile("python", "local").env_config.temp_dir
        temp_abs = Path(os.path.abspath(temp_dir)).resolve()
        mounts = [
            (Path(HOST_PROJECT_ROOT).resolve(), Path(CONTAINER_WORKSPACE)),
            (temp_abs, Path(CONTAINER_WORKSPACE) / ".temp")
        ]
        self.unified_path_manager = UnifiedPathManager(HOST_PROJECT_ROOT, CONTAINER_WORKSPACE, mounts=mounts)
        self.upm = UnifiedPathManager(HOST_PROJECT_ROOT, CONTAINER_WORKSPACE, mounts=mounts)
        self.env_type = env_type
        if exec_manager is not None:
            self.exec_manager = exec_manager
        elif env_type == 'docker':
            self.exec_manager = ExecutionManager(self.ctl)
        else:
            self.exec_manager = ExecutionManager(LocalAsyncClient())

    def to_container_path(self, host_path: str) -> str:
        return str(self.unified_path_manager.to_container_path(os.path.abspath(host_path)))

    def to_host_path(self, container_path: str) -> str:
        return str(self.unified_path_manager.to_host_path(container_path))

    def run_test_case(self, language_name, container, in_file, source_path, artifact_path=None, retry=3):
        handler = self.handlers[language_name]
        image = ContainerImageManager().ensure_image("ojtools") if container.startswith("cph_ojtools") else language_name
        ctl = self.ctl
        stdout = stderr = ""
        cont_in_file = in_file
        cont_source_path = source_path
        # upmでホスト側パスに変換
        host_in_file = self.unified_path_manager.to_host_path(cont_in_file)
        if host_in_file is not None:
            host_in_file = str(host_in_file)
        else:
            host_in_file = cont_in_file
        for attempt in range(retry):
            ok, stdout, stderr = handler.run(ctl, container, cont_in_file, cont_source_path, artifact_path, host_in_file=host_in_file)
            if ok:
                break
            else:
                print(f"[WARN] exec失敗: {container} (attempt {attempt+1})")
        return ok, stdout, stderr, attempt+1

    def adjust_containers(self, requirements, contest_name=None, problem_name=None, language_name=None):
        """必要なコンテナ数・ボリュームを調整し、system_info.jsonも更新する。"""
        containers = self.pool.adjust(requirements)
        # system_info.jsonの更新もここで行う
        if contest_name and problem_name and language_name:
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
        manager = InfoJsonManager(info_path)
        ojtools_list = manager.get_containers(type="ojtools")
        if not ojtools_list:
            raise RuntimeError("ojtools用コンテナがsystem_info.jsonにありません")
        ojtools_name = ojtools_list[0]["name"]
        ctl = self.ctl
        if not ctl.is_container_running(ojtools_name):
            ctl.start_container(ojtools_name, ContainerImageManager().ensure_image("ojtools"), {})
        cmd = ["oj"] + args
        result = ctl.exec_in_container(ojtools_name, cmd)
        print(f"returncode: {result.returncode}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        ok = result.returncode == 0
        stdout = result.stdout
        stderr = result.stderr
        return ok, stdout, stderr

    def collect_test_cases(self, temp_test_dir, file_operator=None):
        import glob
        import os
        if file_operator:
            in_files = sorted(file_operator.glob(f"{temp_test_dir}/*.in"))
        else:
            in_files = sorted(glob.glob(f"{temp_test_dir}/*.in"))
        out_files = [str(f).replace('.in', '.out') for f in in_files]
        return in_files, out_files

    def get_test_containers_from_info(self):
        info_path = self.upm.info_json()
        manager = InfoJsonManager(info_path)
        return [c["name"] for c in manager.get_containers(type="test")]

    def build_in_container(self, handler, container, source_path):
        cmd, artifact_path = handler.build_command(source_path)
        print(f"[DEBUG] build_in_container: container={container}, source_path={source_path}, cmd={cmd}, artifact_path={artifact_path}")
        if cmd is None:
            return True, '', '', artifact_path
        abs_source_path = self.upm.to_host_path(source_path) or source_path
        host_cwd = abs_source_path if handler.config.name == "rust" else os.path.dirname(abs_source_path)
        container_cwd = self.to_container_path(host_cwd)
        print(f"[DEBUG] build_in_container: abs_source_path={abs_source_path}, host_cwd={host_cwd}, container_cwd={container_cwd}")
        image = ContainerImageManager().ensure_image(handler.config.name)
        result = self.exec_manager.run_and_measure(container, cmd, cwd=container_cwd, image=image)
        print(f"[DEBUG] build_in_container: result.returncode={result.returncode}, result.stdout={result.stdout}, result.stderr={result.stderr}")
        ok = result.returncode == 0
        return ok, result.stdout, result.stderr, artifact_path

    def run_test_cases(self, temp_source_path, temp_in_files, language_name, handler):
        import os
        test_containers = self.get_test_containers_from_info()
        abs_temp_source_path = os.path.abspath(temp_source_path)
        cont_temp_source_path = self.to_container_path(abs_temp_source_path)
        print(f"[DEBUG] run_test_cases: temp_source_path={temp_source_path}, abs_temp_source_path={abs_temp_source_path}, cont_temp_source_path={cont_temp_source_path}")
        ok, stdout, stderr, artifact_path = self.build_in_container(handler, test_containers[0], cont_temp_source_path)
        if not ok:
            print(f"[エラー] ビルド失敗\n{stderr}")
            return []
        results = []
        for i, in_file in enumerate(temp_in_files):
            container = test_containers[i] if i < len(test_containers) else test_containers[-1]
            abs_in_file = os.path.abspath(in_file)
            cont_in_file = self.to_container_path(abs_in_file)
            cont_artifact_path = self.to_container_path(artifact_path) if artifact_path else artifact_path
            cont_temp_source_path = self.to_container_path(abs_temp_source_path)
            run_cmd = handler.run_command(cont_temp_source_path, cont_artifact_path)
            with open(in_file, "r", encoding="utf-8") as f:
                input_data = f.read()
            abs_run_cwd = self.upm.to_host_path(cont_temp_source_path) or cont_temp_source_path
            run_cwd = abs_run_cwd if handler.config.name == "rust" else os.path.dirname(abs_run_cwd)
            print(f"[DEBUG] run_test_cases: container={container}, in_file={in_file}, abs_in_file={abs_in_file}, cont_in_file={cont_in_file}, run_cmd={run_cmd}, run_cwd={run_cwd}")
            image = ContainerImageManager().ensure_image(language_name)
            result = self.exec_manager.run_and_measure(container, run_cmd, cwd=run_cwd, input=input_data, image=image)
            stdout = result.stdout
            stderr = result.stderr
            ok = result.returncode == 0
            attempt = 1
            out_file = str(in_file).replace('.in', '.out')
            expected = ""
            file_operator = self.file_manager.file_operator if self.file_manager else None
            if file_operator:
                if file_operator.exists(out_file):
                    with file_operator.open(out_file, "r", encoding="utf-8") as f:
                        expected = f.read()
            else:
                if os.path.exists(out_file):
                    with open(out_file, "r", encoding="utf-8") as f:
                        expected = f.read()
            result_obj = {
                "result": (0 if ok else 1, stdout, stderr),
                "expected": expected,
                "time": 0.0,
                "name": os.path.basename(in_file),
                "in_file": in_file,
                "container": container,
                "attempt": attempt,
            }
            results.append(result_obj)
        return results

    async def run_test_all_cases(self, contest_name, problem_name, language_name):
        # 1. テスト用ソース・テストケース準備
        temp_source_path = self.prepare_source_code(contest_name, problem_name, language_name)
        temp_test_dir = self.prepare_test_cases(contest_name, problem_name)
        file_operator = self.file_manager.file_operator if self.file_manager else None
        temp_in_files, _ = self.collect_test_cases(temp_test_dir, file_operator)
        # 2. requirements生成・コンテナ調整
        test_case_count = len(temp_in_files)
        requirements = [
            {"type": "test", "language": language_name, "count": test_case_count, "volumes": {
                str(self.upm.project_root): str(self.upm.container_root),
                str(self.upm.project_root + "/.temp"): str(self.upm.container_root + "/.temp")
            }},
            {"type": "ojtools", "count": 1, "volumes": {
                str(self.upm.project_root): str(self.upm.container_root),
                str(self.upm.project_root + "/.temp"): str(self.upm.container_root + "/.temp"),
                "/home/cphelper/.local/share/online-judge-tools/cookie.jar": "/root/.local/share/online-judge-tools/cookie.jar"
            }}
        ]
        self.adjust_containers(requirements, contest_name, problem_name, language_name)
        # 3. テスト実行
        from src.environment.test_language_handler import HANDLERS
        handler = HANDLERS[language_name]
        results = self.run_test_cases(temp_source_path, temp_in_files, language_name, handler)
        return results 