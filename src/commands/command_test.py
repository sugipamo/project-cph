from src.commands.test_result_formatter import TestResultFormatter

class CommandTest:
    def __init__(self, docker_operator, file_manager):
        self.docker_operator = docker_operator
        self.file_manager = file_manager

    def prepare_test_environment(self, contest_name, problem_name, language_name):
        import pathlib
        file_operator = self.file_manager.file_operator if self.file_manager else None
        source_path = f"contest_current/{language_name}/main.py"
        test_dir = "contest_current/test"
        if language_name == "rust":
            source_path = f"contest_current/{language_name}/main.rs"
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

    async def run_test_cases(self, temp_source_path, temp_in_files, language_name):
        from language_runner import PythonRunner, RustRunner, PypyRunner
        if language_name == "python":
            runner = PythonRunner(temp_source_path, None, self.docker_operator)
        elif language_name == "pypy":
            runner = PypyRunner(temp_source_path, None, self.docker_operator)
        elif language_name == "rust":
            runner = RustRunner(temp_source_path, None, self.docker_operator)
        else:
            print(f"未対応の言語です: {language_name}")
            return []
        import pathlib
        runner._host_temp_dir = str(pathlib.Path(temp_source_path).parent.resolve())
        async def run_one(in_file):
            import os
            file_operator = self.file_manager.file_operator if self.file_manager else None
            result = await runner.run(input_path=in_file)
            if result is False:
                return {
                    "name": os.path.basename(str(in_file)),
                    "result": (1, "", "runner error"),
                    "time": 0.0,
                    "expected": "",
                    "in_file": in_file,
                }
            if len(result) == 4:
                returncode, stdout, stderr, elapsed = result
            else:
                returncode, stdout, stderr = result
                elapsed = 0.0
            out_file = str(in_file)[:-3] + ".out"
            expected = ""
            if file_operator:
                if file_operator.exists(out_file):
                    with file_operator.open(out_file, "r", encoding="utf-8") as f:
                        expected = f.read()
            else:
                if os.path.exists(out_file):
                    with open(out_file, "r", encoding="utf-8") as f:
                        expected = f.read()
            return {
                "name": os.path.basename(str(in_file)),
                "result": (returncode, stdout, stderr),
                "time": elapsed,
                "expected": expected,
                "in_file": in_file,
            }
        import asyncio
        tasks = [run_one(in_file) for in_file in temp_in_files]
        results = await asyncio.gather(*tasks)
        return results

    def print_test_results(self, results):
        for r in results:
            print(TestResultFormatter(r).format())
            print("")

    async def run_test(self, contest_name, problem_name, language_name):
        file_operator = self.file_manager.file_operator if self.file_manager else None
        temp_dir, source_path = self.prepare_test_environment(contest_name, problem_name, language_name)
        test_dir = "contest_current/test"
        temp_source_path = str(temp_dir / pathlib.Path(source_path).name)
        temp_in_files, _ = self.collect_test_cases(temp_dir, test_dir, file_operator)
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