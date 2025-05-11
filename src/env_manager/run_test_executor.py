import os
from pathlib import Path
from src.language_env.handlers import get_handler

class RunTestExecutor:
    def __init__(self, exec_manager, upm, file_operator=None, env_type='local'):
        self.exec_manager = exec_manager
        self.upm = upm
        self.file_operator = file_operator
        self.env_type = env_type

    def build(self, language_name, container, source_path):
        handler = get_handler(language_name, self.env_type)
        cmd = handler.build_command(source_path)
        if cmd is None:
            return True, '', ''
        abs_source_path = self.upm.to_host_path(source_path) or source_path
        host_cwd = abs_source_path if handler.config.name == "rust" else os.path.dirname(abs_source_path)
        container_cwd = self.upm.to_container_path(host_cwd)
        image = language_name
        result = self.exec_manager.run_and_measure(container, cmd, cwd=container_cwd, image=image)
        ok = result.returncode == 0
        return ok, result.stdout, result.stderr

    def run_test_case(self, language_name, container, in_file, source_path, artifact_path=None, retry=3):
        handler = get_handler(language_name, self.env_type)
        stdout = stderr = ""
        cont_in_file = in_file
        cont_source_path = source_path
        host_in_file = self.upm.to_host_path(cont_in_file)
        if host_in_file is not None:
            host_in_file = str(host_in_file)
        else:
            host_in_file = cont_in_file
        for attempt in range(retry):
            ok, stdout, stderr = handler.run(self.exec_manager.client, container, cont_in_file, cont_source_path, artifact_path, host_in_file=host_in_file)
            if ok:
                break
            else:
                print(f"[WARN] exec失敗: {container} (attempt {attempt+1})")
        return ok, stdout, stderr, attempt+1

    def run_test_cases(self, temp_source_path, temp_in_files, language_name):
        handler = get_handler(language_name, self.env_type)
        container = None  # 必要に応じて指定
        abs_temp_source_path = os.path.abspath(temp_source_path)
        cont_temp_source_path = self.upm.to_container_path(abs_temp_source_path)
        ok, stdout, stderr = self.build(language_name, container, cont_temp_source_path)
        if not ok:
            print(f"[エラー] ビルド失敗\n{stderr}")
            return []
        results = []
        for in_file in temp_in_files:
            abs_in_file = os.path.abspath(in_file)
            cont_in_file = self.upm.to_container_path(abs_in_file)
            cont_temp_source_path = self.upm.to_container_path(abs_temp_source_path)
            run_cmd = handler.run_command(cont_temp_source_path)
            with open(in_file, "r", encoding="utf-8") as f:
                input_data = f.read()
            abs_run_cwd = self.upm.to_host_path(cont_temp_source_path) or cont_temp_source_path
            run_cwd = abs_run_cwd if handler.config.name == "rust" else os.path.dirname(abs_run_cwd)
            container_run_cwd = self.upm.to_container_path(run_cwd)
            image = language_name
            if not run_cmd or run_cmd == ["None"]:
                ok = False
                stdout = ""
                stderr = "実行ファイルが見つかりません (run_cmdがNone)"
                attempt = 1
            else:
                result = self.exec_manager.run_and_measure(container, run_cmd, cwd=container_run_cwd, input=input_data, image=image)
                stdout = result.stdout
                stderr = result.stderr
                ok = result.returncode == 0
                attempt = 1
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
                "attempt": attempt,
            }
            results.append(result_obj)
        return results 