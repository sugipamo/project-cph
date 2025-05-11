from src.language_env.handlers import get_handler
from src.language_env.file_ops import LocalFileOps, DockerFileOps
from src.language_env.execution_resource_manager import LocalResourceManager, DockerResourceManager
from src.execution_client.client.container import ContainerClient

class TestExecutionEnvironment:
    def __init__(self, upm, exec_manager, env_type='local', file_operator=None, ctl=None):
        self.upm = upm
        self.exec_manager = exec_manager
        self.env_type = env_type
        self.file_operator = file_operator

        # resource_manager, file_opsの選択
        if env_type == 'docker':
            self.resource_manager = DockerResourceManager(upm)
            self.file_ops = DockerFileOps(ctl or ContainerClient(), self.resource_manager)
        else:
            self.resource_manager = LocalResourceManager()
            self.file_ops = LocalFileOps()

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
            ok, stdout, stderr = handler.run(
                self.exec_manager.client, container, in_file, source_path, artifact_path
            )
            if ok:
                break
        return ok, stdout, stderr, attempt+1

    def run_test_all_cases(self, contest_name, problem_name, language_name):
        handler = get_handler(language_name, self.env_type)
        temp_source_path = self.prepare_source_code(contest_name, problem_name, language_name)
        temp_test_dir = self.prepare_test_cases(contest_name, problem_name)
        temp_in_files, _ = self.file_ops.collect_test_cases(temp_test_dir)
        requirements = [{
            "type": "test",
            "language": language_name,
            "count": len(temp_in_files)
        }]
        self.resource_manager.adjust_resources(requirements, contest_name, problem_name, language_name)
        container = None  # 必要に応じて取得
        ok, stdout, stderr = handler.build(self.exec_manager, container, temp_source_path)
        if not ok:
            print(f"[エラー] ビルド失敗\n{stderr}")
            return []
        results = []
        for in_file in temp_in_files:
            ok, stdout, stderr = handler.run(
                self.exec_manager.client, container, in_file, temp_source_path
            )
            out_file = str(in_file).replace('.in', '.out')
            expected = ""
            if self.file_operator and self.file_operator.exists(out_file):
                with self.file_operator.open(out_file, "r", encoding="utf-8") as f:
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
                "name": in_file.split('/')[-1],
                "in_file": in_file,
                "container": container,
                "attempt": 1,
            }
            results.append(result_obj)
        return results 