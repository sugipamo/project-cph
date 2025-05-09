from src.environment.test_environment import TestExecutionEnvironment, TestEnvFileOpsMixin
from execution_client.execution_manager import ExecutionManager
from src.path_manager.unified_path_manager import UnifiedPathManager
import os
import shutil
import subprocess

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
        for attempt in range(retry):
            ok, stdout, stderr = handler.run(self.manager, name, in_file, source_path)
            if ok:
                break
        return ok, stdout, stderr, attempt+1

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
        # workdirが/workspaceで始まる場合はローカルパスに変換
        if workdir.startswith("/workspace"):
            # 例: /workspace/contest_current/python → ./contest_current/python
            workdir = "." + workdir[len("/workspace"):]
        cookie_path = "/home/cphelper/.local/share/online-judge-tools/cookie.jar"
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