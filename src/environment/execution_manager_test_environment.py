from src.environment.test_environment import TestExecutionEnvironment, TestEnvFileOpsMixin
from src.execution_client.execution_manager import ExecutionManager
from src.path_manager.unified_path_manager import UnifiedPathManager
from src.path_manager.common_paths import HOST_PROJECT_ROOT, CONTAINER_WORKSPACE, upm
import os
import shutil
import subprocess
from pathlib import Path

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
        # ローカル実行時は変換せずそのまま返す
        return str(host_path)

    def to_host_path(self, container_path: str) -> str:
        # ローカル実行時は変換せずそのまま返す
        return str(container_path)

    def run_test_case(self, language_name, name, in_file, source_path, retry=3):
        handler = self.handlers[language_name]
        # ビルドコマンドを取得
        build_cmd = handler.build_command(source_path)
        if build_cmd:
            build_proc = subprocess.run(build_cmd, capture_output=True, text=True)
            if build_proc.returncode != 0:
                return False, build_proc.stdout, build_proc.stderr, 1
        run_cmd = handler.run_command(source_path)
        with open(in_file, "r", encoding="utf-8") as f:
            input_data = f.read()
        for attempt in range(retry):
            proc = subprocess.run(run_cmd, input=input_data, capture_output=True, text=True)
            ok = proc.returncode == 0
            if ok:
                break
        return ok, proc.stdout, proc.stderr, attempt+1

    def adjust_containers(self, requirements, contest_name=None, problem_name=None, language_name=None):
        # ローカル実行では特に何もしないが、インターフェース維持のためダミー返却
        return []

    def download_testcases(self, url, test_dir_host):
        # test_dir_hostが存在すれば削除
        if os.path.exists(test_dir_host):
            shutil.rmtree(test_dir_host)
        os.makedirs(test_dir_host, exist_ok=True)
        # oj downloadをローカルで実行
        result = subprocess.run(["oj", "download", url, "-d", test_dir_host], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ERROR] oj download failed: {result.stderr}")
            raise RuntimeError("oj download failed")
        print(result.stdout)

    def submit_via_ojtools(self, args, volumes, workdir):
        host_workdir = upm.to_host_path(workdir)
        if host_workdir is not None:
            # プロジェクトルートからの相対パスに変換
            workdir = os.path.relpath(str(host_workdir), HOST_PROJECT_ROOT)
            if not workdir.startswith('.'):
                workdir = './' + workdir
        cookie_path = ".local/share/online-judge-tools/cookie.jar"
        if not args:
            args = []
        if args and args[0] == "submit":
            cmd = ["oj", "--cookie", cookie_path, "submit"] + args[1:]
        else:
            cmd = ["oj", "--cookie", cookie_path] + args
        result = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True)
        ok = result.returncode == 0
        if not ok:
            print(f"[ERROR] oj submit failed: {result.stderr}")
            print(f"[ERROR] oj submit stdout: {result.stdout}")
        return ok, result.stdout, result.stderr

    async def run_test_all_cases(self, contest_name, problem_name, language_name):
        temp_source_path = self.prepare_source_code(contest_name, problem_name, language_name)
        temp_test_dir = self.prepare_test_cases(contest_name, problem_name)
        file_operator = self.file_manager.file_operator if self.file_manager else None
        temp_in_files, _ = self.collect_test_cases(temp_test_dir, file_operator)
        handler = self.handlers[language_name]
        results = []
        for i, in_file in enumerate(temp_in_files):
            name = f"local_test_{i+1}"
            ok, stdout, stderr, attempt = self.run_test_case(language_name, name, in_file, temp_source_path)
            out_file = str(in_file).replace('.in', '.out')
            expected = ""
            if file_operator:
                if file_operator.exists(out_file):
                    with file_operator.open(out_file, "r", encoding="utf-8") as f:
                        expected = f.read()
            else:
                import os
                if os.path.exists(out_file):
                    with open(out_file, "r", encoding="utf-8") as f:
                        expected = f.read()
            result_obj = {
                "result": (0 if ok else 1, stdout, stderr),
                "expected": expected,
                "time": 0.0,
                "name": Path(in_file).name,
                "in_file": in_file,
                "container": name,
                "attempt": attempt,
            }
            results.append(result_obj)
        return results

    def collect_test_cases(self, temp_test_dir, file_operator=None):
        import glob
        import os
        if file_operator:
            in_files = sorted(file_operator.glob(f"{temp_test_dir}/*.in"))
        else:
            in_files = sorted(glob.glob(f"{temp_test_dir}/*.in"))
        out_files = [str(f).replace('.in', '.out') for f in in_files]
        return in_files, out_files 