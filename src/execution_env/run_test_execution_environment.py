from src.execution_env.handlers import get_handler
from src.file.testcase_file_operator import LocalTestcaseFileOperator, DockerTestcaseFileOperator
from src.execution_env.execution_resource_manager import LocalResourceManager, DockerResourceManager
from src.execution_client.client.container import ContainerClient
import os

class RunTestExecutionEnvironment:
    def __init__(self, upm, exec_manager, env_type='local', file_operator=None, file_ops=None, resource_manager=None, ctl=None):
        self.upm = upm
        self.exec_manager = exec_manager
        self.env_type = env_type
        self.file_operator = file_operator
        # 柔軟な差し替えに対応
        if resource_manager is not None:
            self.resource_manager = resource_manager
        elif env_type == 'docker':
            self.resource_manager = DockerResourceManager(upm)
        else:
            self.resource_manager = LocalResourceManager()
        if file_ops is not None:
            self.file_ops = file_ops
        elif env_type == 'docker':
            self.file_ops = DockerTestcaseFileOperator(ctl or ContainerClient(), self.resource_manager)
        else:
            self.file_ops = LocalTestcaseFileOperator()

    def build(self, language_name, container, source_path):
        handler = get_handler(language_name, self.env_type)
        handler.before_build(container, source_path)
        result = handler.build(self.exec_manager, container, source_path)
        handler.after_build(container, source_path, result)
        return result

    def prepare_source_code(self, contest_name, problem_name, language_name):
        handler = get_handler(language_name, self.env_type)
        return self.file_ops.prepare_source_code(
            contest_name, problem_name, language_name, self.upm, handler.config, handler.env_config
        )

    def prepare_test_cases(self, contest_name, problem_name):
        # テストケースは言語非依存
        handler = get_handler("python", self.env_type)
        return self.file_ops.prepare_test_cases(
            contest_name, problem_name, self.upm, handler.env_config
        )

    def run_test_case(self, language_name, container, in_file, source_path, artifact_path=None, retry=3):
        handler = get_handler(language_name, self.env_type)
        for attempt in range(retry):
            handler.before_test_case(container, in_file, source_path)
            handler.before_run(container, source_path)
            ok, stdout, stderr = handler.run(
                self.exec_manager.client, container, in_file, source_path, artifact_path
            )
            handler.after_run(container, source_path, ok, stdout, stderr)
            handler.after_test_case(container, in_file, source_path, ok, stdout, stderr)
            if ok:
                break
        return ok, stdout, stderr, attempt+1

    def run_test_cases(self, temp_source_path, temp_in_files, language_name):
        handler = get_handler(language_name, self.env_type)
        container = None  # 必要に応じて指定
        ok, stdout, stderr = self.build(language_name, container, temp_source_path)
        if not ok:
            print(f"[エラー] ビルド失敗\n{stderr}")
            return []
        results = []
        for in_file in temp_in_files:
            ok, stdout, stderr, attempt = self.run_test_case(language_name, container, in_file, temp_source_path)
            out_file = str(in_file).replace('.in', '.out')
            expected = ""
            if self.file_operator and self.file_operator.exists(out_file):
                with self.file_operator.open(out_file, "r", encoding="utf-8") as f:
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

    def run_test_all_cases(self, contest_name, problem_name, language_name):
        handler = get_handler(language_name, self.env_type)
        temp_source_path = self.prepare_source_code(contest_name, problem_name, language_name)
        temp_test_dir = self.prepare_test_cases(contest_name, problem_name)
        temp_in_files, _ = self.file_ops.collect_test_cases(temp_test_dir)
        # Handlerからリソース制限値を取得しrequirementsに追加
        requirements = [{
            "type": "test",
            "language": language_name,
            "count": len(temp_in_files),
            "memory_limit": getattr(handler, "memory_limit", None),
            "cpu_limit": getattr(handler, "cpu_limit", None),
            "time_limit": getattr(handler, "time_limit", None),
            "extra_env": getattr(handler, "extra_env", None),
            "extra_mounts": getattr(handler, "extra_mounts", None),
        }]
        self.resource_manager.adjust_resources(requirements, contest_name, problem_name, language_name)
        return self.run_test_cases(temp_source_path, temp_in_files, language_name)

    def to_container_path(self, host_path):
        return self.upm.to_container_path(host_path)

    def submit_via_ojtools(self, args, volumes, workdir):
        return self.file_ops.submit_via_ojtools(args, workdir) 