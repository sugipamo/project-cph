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
        import pathlib
        file_operator = self.file_manager.file_operator if self.file_manager else None
        source_path = f"contest_current/{language_name}/main.py"
        test_dir = "contest_current/test"
        if language_name == "rust":
            source_path = f"contest_current/{language_name}/src/main.rs"
        temp_dir = pathlib.Path(".temp")
        if file_operator:
            if file_operator.exists(temp_dir):
                file_operator.rmtree(temp_dir)
            file_operator.makedirs(temp_dir)
            file_operator.copy(source_path, temp_dir / pathlib.Path(source_path).name)
            if not file_operator.exists(test_dir):
                file_operator.makedirs(test_dir)
            file_operator.copytree(test_dir, temp_dir / "test")
        else:
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, temp_dir / pathlib.Path(source_path).name)
            if not pathlib.Path(test_dir).exists():
                pathlib.Path(test_dir).mkdir(parents=True, exist_ok=True)
            shutil.copytree(test_dir, temp_dir / "test", dirs_exist_ok=True)
        return temp_dir, source_path

    def collect_test_cases(self, temp_dir, test_dir, file_operator=None):
        import os
        import pathlib
        if file_operator:
            in_files = sorted(file_operator.glob(f"{test_dir}/*.in"))
        else:
            import glob
            in_files = sorted(glob.glob(os.path.join(test_dir, "*.in")))
        temp_in_files = [str(temp_dir / "test" / pathlib.Path(f).name) for f in in_files]
        return temp_in_files, in_files

    def get_test_containers_from_info(self):
        # from commands.info_json_manager import InfoJsonManager
        info_path = "contest_current/info.json"
        manager = InfoJsonManager(info_path)
        return [c["name"] for c in manager.get_containers(type="test")]

    async def run_test_cases(self, temp_source_path, temp_in_files, language_name):
        import os
        test_containers = self.get_test_containers_from_info()
        ctl = DockerCtl()
        handler = HANDLERS[language_name]
        # --- ビルド工程 ---
        build_container = test_containers[0]
        ok, stdout, stderr = handler.build(ctl, build_container, temp_source_path)
        if not ok:
            print(f"[エラー] ビルド失敗\n{stderr}")
            return []
        # --- テスト実行 ---
        results = []
        for i, in_file in enumerate(temp_in_files):
            if i < len(test_containers):
                container = test_containers[i]
            else:
                container = test_containers[-1]
            image = "oj" if container.startswith("cph_ojtools") else language_name
            if not ctl.is_container_running(container):
                ctl.start_container(container, image, {})
            # 絶対パスに変換
            abs_in_file = os.path.abspath(in_file)
            abs_temp_source_path = os.path.abspath(temp_source_path)
            for attempt in range(3):
                ok, stdout, stderr = handler.run(ctl, container, abs_in_file, abs_temp_source_path)
                if ok:
                    break
                else:
                    print(f"[WARN] exec失敗: {container} (attempt {attempt+1})")
                    ctl.remove_container(container)
                    ctl.start_container(container, image, {})
            out_file = in_file.replace('.in', '.out')
            expected = ""
            if os.path.exists(out_file):
                with open(out_file, "r", encoding="utf-8") as f:
                    expected = f.read()
            results.append({
                "result": (0 if ok else 1, stdout, stderr),
                "expected": expected,
                "time": 0.0,
                "name": os.path.basename(in_file),
                "in_file": in_file,
                "container": container,
                "attempt": attempt + 1,
            })
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
        results = await self.run_test_cases(temp_source_path, temp_in_files, language_name)
        return results

    def is_all_ac(self, results):
        for r in results:
            returncode, stdout, _ = r["result"]
            if returncode != 0 or stdout.strip() != r["expected"].strip():
                return False
        return True 