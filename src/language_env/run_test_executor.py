import os
from pathlib import Path
from src.language_env.handlers import get_handler
from src.language_env.file_ops import LocalFileOps
from src.language_env.execution_resource_manager import LocalResourceManager

class RunTestExecutor:
    def __init__(self, exec_manager, upm, file_operator=None, env_type='local', file_ops=None, resource_manager=None):
        self.exec_manager = exec_manager
        self.upm = upm
        self.file_operator = file_operator
        self.env_type = env_type
        self.file_ops = file_ops if file_ops is not None else LocalFileOps()
        self.resource_manager = resource_manager if resource_manager is not None else LocalResourceManager()

    def build(self, language_name, container, source_path):
        handler = get_handler(language_name, self.env_type)
        return handler.build(self.exec_manager, container, source_path)

    def run_test_case(self, language_name, container, in_file, source_path, artifact_path=None, retry=3):
        handler = get_handler(language_name, self.env_type)
        for attempt in range(retry):
            ok, stdout, stderr = handler.run(
                self.exec_manager.client, container, in_file, source_path, artifact_path
            )
            if ok:
                break
            else:
                print(f"[WARN] exec失敗: {container} (attempt {attempt+1})")
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
            ok, stdout, stderr = handler.run(
                self.exec_manager.client, container, in_file, temp_source_path
            )
            out_file = str(in_file).replace('.in', '.out')
            expected = ""
            if self.file_operator:
                if self.file_operator.exists(out_file):
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
                "attempt": 1,
            }
            results.append(result_obj)
        return results

    def run_test_all_cases(self, contest_name, problem_name, language_name):
        handler = get_handler(language_name, self.env_type)
        language_config = handler.config
        env_config = handler.env_config
        # 1. テスト用ソース・テストケース準備
        temp_source_path = self.file_ops.prepare_source_code(contest_name, problem_name, language_name, self.upm, language_config, env_config)
        temp_test_dir = self.file_ops.prepare_test_cases(contest_name, problem_name, self.upm, env_config)
        # 2. テストケース収集
        temp_in_files, _ = self.file_ops.collect_test_cases(temp_test_dir)
        # 3. リソース調整（コンテナ/ローカル/クラウド等）
        requirements = [{
            "type": "test",
            "language": language_name,
            "count": len(temp_in_files)
        }]
        self.resource_manager.adjust_resources(requirements, contest_name, problem_name, language_name)
        # 4. テスト実行
        return self.run_test_cases(temp_source_path, temp_in_files, language_name) 