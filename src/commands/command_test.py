import os
from src.path_manager.unified_path_manager import UnifiedPathManager
from src.file.file_operator import FileOperator
# === 定数定義 ===
HOST_PROJECT_ROOT = os.path.abspath(".")
CONTAINER_WORKSPACE = "/workspace"
TEMP_DIR = os.path.abspath(".temp")

from .test_result_formatter import ResultFormatter
from src.environment.test_language_handler import HANDLERS
from src.file.info_json_manager import InfoJsonManager
from src.execution_client.container.client import ContainerClient
from src.environment.test_environment import DockerTestExecutionEnvironment
from src.execution_client.container.image_manager import ContainerImageManager
from src.execution_client.execution_manager import ExecutionManager
from src.execution_client.local import LocalAsyncClient

class CommandTest:
    def __init__(self, file_manager, test_env):
        self.file_manager = file_manager
        self.env = test_env
        self.upm = UnifiedPathManager()

    def prepare_test_environment(self, contest_name, problem_name, language_name):
        # DockerTestExecutionEnvironmentに移譲
        temp_source_path = self.env.prepare_source_code(contest_name, problem_name, language_name)
        temp_test_dir = self.env.prepare_test_cases(contest_name, problem_name)
        return temp_source_path, temp_test_dir

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

    def to_container_path(self, host_path):
        return self.env.to_container_path(host_path)

    def build_in_container(self, ctl, handler, container, source_path):
        cmd, artifact_path = handler.build_command(source_path)
        if cmd is None:
            return True, '', '', artifact_path
        # Rustはビルドディレクトリで実行
        abs_source_path = self.upm.to_host_path(source_path) or source_path
        host_cwd = abs_source_path if handler.config.name == "rust" else os.path.dirname(abs_source_path)
        import subprocess
        process = subprocess.Popen(cmd, cwd=host_cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        stdout = ''
        for line in process.stdout:
            print(line, end='')
            stdout += line
        process.wait()
        ok = process.returncode == 0
        return ok, stdout, '', artifact_path

    def select_container_for_case(self, test_containers, i):
        return test_containers[i] if i < len(test_containers) else test_containers[-1]

    def ensure_container_running(self, ctl, container, image):
        if not ctl.is_container_running(container):
            ctl.run_container(container, image, {})

    def run_single_test_case(self, ctl, handler, container, in_file, source_path, image, retry=3):
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
        ctl = ContainerClient()
        handler = HANDLERS[language_name]
        # --- ビルド工程 ---
        abs_temp_source_path = os.path.abspath(temp_source_path)
        cont_temp_source_path = self.to_container_path(abs_temp_source_path)
        ok, stdout, stderr, artifact_path = self.build_in_container(ctl, handler, test_containers[0], cont_temp_source_path)
        if not ok:
            print(f"[エラー] ビルド失敗\n{stderr}")
            return []
        # --- テスト実行 ---
        results = []
        for i, in_file in enumerate(temp_in_files):
            container = self.select_container_for_case(test_containers, i)
            image = ContainerImageManager().ensure_image("ojtools") if container.startswith("cph_ojtools") else language_name
            self.ensure_container_running(ctl, container, image)
            abs_in_file = os.path.abspath(in_file)
            cont_in_file = self.to_container_path(abs_in_file)
            # artifact_pathをホストパスに変換
            host_artifact_path = self.upm.to_host_path(artifact_path) or artifact_path
            # 実行コマンド生成
            run_cmd = handler.run_command(cont_temp_source_path, host_artifact_path)
            # 入力データ取得
            with open(in_file, "r", encoding="utf-8") as f:
                input_data = f.read()
            # 実行クライアントを選択（ここではローカル例）
            exec_manager = ExecutionManager(LocalAsyncClient())
            # 実行時cwdもホストパスに変換
            abs_run_cwd = self.upm.to_host_path(cont_temp_source_path) or cont_temp_source_path
            run_cwd = abs_run_cwd if handler.config.name == "rust" else os.path.dirname(abs_run_cwd)
            result = exec_manager.run_and_measure(container, run_cmd, input=input_data, cwd=run_cwd)
            ok = result.returncode == 0
            stdout = result.stdout
            stderr = result.stderr
            attempt = 1  # リトライ未対応
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
            result_obj = self.collect_test_result(ok, stdout, stderr, expected, in_file, container, attempt)
            results.append(result_obj)
        return results

    def print_test_results(self, results):
        for r in results:
            print(ResultFormatter(r).format())
            print("")

    async def run_test(self, contest_name, problem_name, language_name):
        import pathlib
        file_operator = self.file_manager.file_operator if self.file_manager else None
        temp_source_path, temp_test_dir = self.prepare_test_environment(contest_name, problem_name, language_name)
        temp_in_files, _ = self.collect_test_cases(temp_test_dir, file_operator)
        # --- 必要なコンテナ数を調整し、system_info.jsonを最新化 ---
        test_case_count = len(temp_in_files)
        requirements = [
            {"type": "test", "language": language_name, "count": test_case_count, "volumes": {
                HOST_PROJECT_ROOT: CONTAINER_WORKSPACE,
                TEMP_DIR: "/workspace/.temp"
            }},
            {"type": "ojtools", "count": 1, "volumes": {
                HOST_PROJECT_ROOT: CONTAINER_WORKSPACE,
                TEMP_DIR: "/workspace/.temp",
                "/home/cphelper/.local/share/online-judge-tools/cookie.jar": "/root/.local/share/online-judge-tools/cookie.jar"
            }}
        ]
        containers = self.env.adjust_containers(requirements, contest_name, problem_name, language_name)
        # --- テスト実行 ---
        results = await self.run_test_cases(temp_source_path, temp_in_files, language_name)
        self.print_test_results(results)

    async def run_test_return_results(self, contest_name, problem_name, language_name):
        import pathlib
        file_operator = self.file_manager.file_operator if self.file_manager else None
        temp_source_path, temp_test_dir = self.prepare_test_environment(contest_name, problem_name, language_name)
        temp_in_files, _ = self.collect_test_cases(temp_test_dir, file_operator)
        # --- 必要なコンテナ数を調整し、system_info.jsonを最新化 ---
        test_case_count = len(temp_in_files)
        requirements = [
            {"type": "test", "language": language_name, "count": test_case_count, "volumes": {
                HOST_PROJECT_ROOT: CONTAINER_WORKSPACE,
                TEMP_DIR: "/workspace/.temp"
            }},
            {"type": "ojtools", "count": 1, "volumes": {
                HOST_PROJECT_ROOT: CONTAINER_WORKSPACE,
                TEMP_DIR: "/workspace/.temp",
                "/home/cphelper/.local/share/online-judge-tools/cookie.jar": "/root/.local/share/online-judge-tools/cookie.jar"
            }}
        ]
        containers = self.env.adjust_containers(requirements, contest_name, problem_name, language_name)
        results = await self.run_test_cases(temp_source_path, temp_in_files, language_name)
        return results

    def is_all_ac(self, results):
        for r in results:
            returncode, stdout, _ = r["result"]
            if returncode != 0 or stdout.strip() != r["expected"].strip():
                return False
        return True 