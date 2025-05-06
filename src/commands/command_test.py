import os
# === 定数定義 ===
HOST_PROJECT_ROOT = os.path.abspath(".")
CONTAINER_WORKSPACE = "/workspace"

from .test_result_formatter import TestResultFormatter
from .test_language_handler import HANDLERS
from .info_json_manager import InfoJsonManager
from ..docker.pool import DockerPool
from ..docker.ctl import DockerCtl

class CommandTest:
    def __init__(self, file_manager):
        self.file_manager = file_manager

    def prepare_test_environment(self, contest_name, problem_name, language_name):
        import os
        import pathlib
        file_operator = self.file_manager.file_operator if self.file_manager and hasattr(self.file_manager, 'file_operator') else None
        temp_dir = pathlib.Path(".temp")
        if file_operator:
            if not file_operator.exists(str(temp_dir)):
                file_operator.makedirs(str(temp_dir))
        else:
            os.makedirs(temp_dir, exist_ok=True)
        source_path = f"contest_current/{language_name}/main.py"
        temp_source_path = temp_dir / "main.py"
        if file_operator:
            file_operator.copy(source_path, str(temp_source_path))
        else:
            import shutil
            shutil.copy(source_path, temp_source_path)
        test_dir = "contest_current/test"
        temp_test_dir = temp_dir / "test"
        if file_operator:
            if not file_operator.exists(str(temp_test_dir)):
                file_operator.copytree(test_dir, str(temp_test_dir))
        else:
            if os.path.exists(test_dir):
                shutil.copytree(test_dir, temp_test_dir, dirs_exist_ok=True)
        return temp_dir, source_path

    def collect_test_cases(self, temp_dir, test_dir, file_operator=None):
        import glob
        import os
        if file_operator:
            in_files = sorted(file_operator.glob(f"{test_dir}/*.in"))
        else:
            in_files = sorted(glob.glob(f"{test_dir}/*.in"))
        out_files = [str(f).replace('.in', '.out') for f in in_files]
        return in_files, out_files

    def get_test_containers_from_info(self):
        # from commands.info_json_manager import InfoJsonManager
        info_path = "contest_current/info.json"
        manager = InfoJsonManager(info_path)
        return [c["name"] for c in manager.get_containers(type="test")]

    def to_container_path(self, host_path):
        return str(host_path).replace(HOST_PROJECT_ROOT, CONTAINER_WORKSPACE, 1)

    def build_in_container(self, ctl, handler, container, source_path):
        return handler.build(ctl, container, source_path)

    def select_container_for_case(self, test_containers, i):
        return test_containers[i] if i < len(test_containers) else test_containers[-1]

    def ensure_container_running(self, ctl, container, image):
        if not ctl.is_container_running(container):
            ctl.start_container(container, image, {})

    def run_single_test_case(self, ctl, handler, container, in_file, source_path, image, retry=2):
        for attempt in range(retry):
            ok, stdout, stderr = handler.run(ctl, container, in_file, source_path)
            if ok:
                break
            else:
                print(f"[WARN] exec失敗: {container} (attempt {attempt+1})")
                ctl.remove_container(container)
                ctl.start_container(container, image, {})
        return ok, stdout, stderr, attempt+1

    def collect_test_result(self, ok, stdout, stderr, expected, in_file, container, attempt):
        import os
        return {
            "result": (0 if ok else 1, stdout, stderr),
            "expected": expected,
            "time": 0.0,
            "name": os.path.basename(in_file),
            "in_file": in_file,
            "container": container,
            "attempt": attempt,
        }

    async def run_test_cases(self, temp_source_path, temp_in_files, language_name):
        import os
        test_containers = self.get_test_containers_from_info()
        ctl = DockerCtl()
        handler = HANDLERS[language_name]
        # --- ビルド工程 ---
        abs_temp_source_path = os.path.abspath(temp_source_path)
        cont_temp_source_path = self.to_container_path(abs_temp_source_path)
        ok, stdout, stderr = self.build_in_container(ctl, handler, test_containers[0], cont_temp_source_path)
        if not ok:
            print(f"[エラー] ビルド失敗\n{stderr}")
            return []
        # --- テスト実行 ---
        results = []
        for i, in_file in enumerate(temp_in_files):
            container = self.select_container_for_case(test_containers, i)
            image = "oj" if container.startswith("cph_ojtools") else language_name
            self.ensure_container_running(ctl, container, image)
            abs_in_file = os.path.abspath(in_file)
            cont_in_file = self.to_container_path(abs_in_file)
            ok, stdout, stderr, attempt = self.run_single_test_case(ctl, handler, container, cont_in_file, cont_temp_source_path, image, retry=2)
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
            result = self.collect_test_result(ok, stdout, stderr, expected, in_file, container, attempt)
            results.append(result)
        return results

    def print_test_results(self, results):
        for r in results:
            print(TestResultFormatter(r).format())
            print("")

    async def run_test(self, contest_name, problem_name, language_name):
        import pathlib
        # from docker.pool import DockerPool
        # from commands.info_json_manager import InfoJsonManager
        file_operator = self.file_manager.file_operator if self.file_manager else None
        temp_dir, source_path = self.prepare_test_environment(contest_name, problem_name, language_name)
        test_dir = "contest_current/test"
        temp_source_path = str(temp_dir / pathlib.Path(source_path).name)
        temp_in_files, _ = self.collect_test_cases(temp_dir, test_dir, file_operator)
        # --- 必要なコンテナ数を調整し、info.jsonを最新化 ---
        test_case_count = len(temp_in_files)
        requirements = [
            {"type": "test", "language": language_name, "count": test_case_count, "volumes": {
                HOST_PROJECT_ROOT: CONTAINER_WORKSPACE
            }},
            {"type": "ojtools", "count": 1}
        ]
        print(f"[DEBUG] requirements: {requirements}")
        pool = DockerPool()
        containers = pool.adjust(requirements)
        print(f"[DEBUG] containers: {containers}")
        info_path = "contest_current/info.json"
        manager = InfoJsonManager(info_path)
        manager.data["contest_name"] = contest_name
        manager.data["problem_name"] = problem_name
        manager.data["language_name"] = language_name
        manager.data["containers"] = containers
        manager.save()
        # --- テスト実行 ---
        results = await self.run_test_cases(temp_source_path, temp_in_files, language_name)
        self.print_test_results(results)

    async def run_test_return_results(self, contest_name, problem_name, language_name):
        import pathlib
        file_operator = self.file_manager.file_operator if self.file_manager else None
        temp_dir, source_path = self.prepare_test_environment(contest_name, problem_name, language_name)
        test_dir = "contest_current/test"
        temp_source_path = str(temp_dir / pathlib.Path(source_path).name)
        temp_in_files, _ = self.collect_test_cases(temp_dir, test_dir, file_operator)
        # --- 必要なコンテナ数を調整し、info.jsonを最新化 ---
        test_case_count = len(temp_in_files)
        requirements = [
            {"type": "test", "language": language_name, "count": test_case_count, "volumes": {
                HOST_PROJECT_ROOT: CONTAINER_WORKSPACE
            }},
            {"type": "ojtools", "count": 1}
        ]
        pool = DockerPool()
        containers = pool.adjust(requirements)
        info_path = "contest_current/info.json"
        manager = InfoJsonManager(info_path)
        manager.data["contest_name"] = contest_name
        manager.data["problem_name"] = problem_name
        manager.data["language_name"] = language_name
        manager.data["containers"] = containers
        manager.save()
        results = await self.run_test_cases(temp_source_path, temp_in_files, language_name)
        return results

    def is_all_ac(self, results):
        for r in results:
            returncode, stdout, _ = r["result"]
            if returncode != 0 or stdout.strip() != r["expected"].strip():
                return False
        return True 