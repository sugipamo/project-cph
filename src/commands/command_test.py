import os
from src.path_manager.unified_path_manager import UnifiedPathManager
from src.file.file_operator import FileOperator
from src.path_manager.common_paths import HOST_PROJECT_ROOT, CONTAINER_WORKSPACE, TEMP_DIR, CONTAINER_TEMP_DIR, OJTOOLS_COOKIE_HOST, OJTOOLS_COOKIE_CONT
# === 定数定義 ===

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
        return self.env.collect_test_cases(temp_test_dir, file_operator)

    def get_test_containers_from_info(self):
        return self.env.get_test_containers_from_info()

    def to_container_path(self, host_path):
        return self.env.to_container_path(host_path)

    def build_in_container(self, ctl, handler, container, source_path):
        # ctlは不要になったのでhandler, container, source_pathのみ渡す
        return self.env.build_in_container(handler, container, source_path)

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
        handler = HANDLERS[language_name]
        # env側に全て委譲
        return self.env.run_test_cases(temp_source_path, temp_in_files, language_name, handler)

    def print_test_results(self, results):
        for r in results:
            print(ResultFormatter(r).format())
            print("")

    async def run_test(self, contest_name, problem_name, language_name):
        results = await self.env.run_test_all_cases(contest_name, problem_name, language_name)
        self.print_test_results(results)

    async def run_test_return_results(self, contest_name, problem_name, language_name):
        results = await self.env.run_test_all_cases(contest_name, problem_name, language_name)
        return results

    def is_all_ac(self, results):
        for r in results:
            returncode, stdout, _ = r["result"]
            if returncode != 0 or stdout.strip() != r["expected"].strip():
                return False
        return True 