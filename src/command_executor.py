from docker_operator import DockerOperator, LocalDockerOperator
from contest_file_manager import ContestFileManager
import subprocess
from command_parser import CommandParser
import shutil
import glob
import os
import json
from language_runner import PythonRunner, RustRunner, PypyRunner
import asyncio
import time
import tempfile
import pathlib
import webbrowser

class Opener:
    def open_editor(self, path: str):
        # VSCodeとCursorでmain.pyのみを同じウィンドウで開く
        main_file = f"{path}/main.py"
        try:
            subprocess.Popen(["code", "--reuse-window", main_file])
        except Exception as e:
            print(f"[警告] VSCode起動失敗: {e}")
        try:
            subprocess.Popen(["cursor", "--reuse-window", main_file])
        except Exception as e:
            print(f"[警告] Cursor起動失敗: {e}")
    def open_browser(self, url: str):
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"[警告] ブラウザでページを開けませんでした: {e}")

class TestResultFormatter:
    def __init__(self, result):
        self.result = result

    @staticmethod
    def color_text(text, color):
        colors = {
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "reset": "\033[0m"
        }
        return f"{colors.get(color, '')}{text}{colors['reset']}"

    def format(self):
        parts = [
            self._format_header(),
            "-" * 17,
            self._format_input(),
            "-" * 17,
            self._format_table(),
            self._format_input_error_bar(),
            self._format_error(),
        ]
        return "\n".join([p for p in parts if p])

    def _format_header(self):
        r = self.result
        name = r["name"]
        returncode, _, _ = r["result"]
        time_sec = r["time"]
        expected = r["expected"]
        stdout = r["result"][1]
        if returncode != 0:
            verdict_colored = self.color_text("RE", "yellow")
        elif stdout.strip() == expected.strip():
            verdict_colored = self.color_text("AC", "green")
        else:
            verdict_colored = self.color_text("WA", "red")
        return f"{name}  {verdict_colored}  {time_sec:.3f}秒"

    def _format_input(self):
        r = self.result
        in_file = r.get("in_file") if "in_file" in r else None
        if in_file and os.path.exists(in_file):
            with open(in_file, "r", encoding="utf-8") as f:
                input_content = f.read().rstrip()
            return input_content
        return ""

    def _format_input_error_bar(self):
        r = self.result
        stderr = r["result"][2]
        if stderr:
            return "-" * 17
        return ""

    def _format_error(self):
        r = self.result
        stderr = r["result"][2]
        if stderr:
            return f"{stderr.strip()}"
        return ""

    def _format_table(self):
        r = self.result
        expected = r["expected"]
        stdout = r["result"][1]
        exp_lines = expected.strip().splitlines()
        out_lines = stdout.strip().splitlines()
        max_exp = max([len(s) for s in exp_lines] + [8]) if exp_lines else 8  # 'Expected'の長さ
        max_out = max([len(s) for s in out_lines] + [6]) if out_lines else 6  # 'Output'の長さ
        max_len = max(len(exp_lines), len(out_lines))
        if max_len == 0:
            return ""
        lines = []
        # カラム名を追加
        lines.append(f"{'Expected':<{max_exp}} | {'Output':<{max_out}}")
        for i in range(max_len):
            exp = exp_lines[i] if i < len(exp_lines) else ""
            out = out_lines[i] if i < len(out_lines) else ""
            lines.append(f"{exp:<{max_exp}} | {out:<{max_out}}")
        return "\n".join(lines)

class CommandExecutor:
    def __init__(self, docker_operator: DockerOperator = None, file_manager: ContestFileManager = None, opener: Opener = None):
        self.docker_operator = docker_operator or LocalDockerOperator()
        self.file_manager = file_manager
        self.opener = opener or Opener()

    async def login(self, *args, **kwargs):
        """
        online-judge-toolsでログインする（ojtラッパー）
        ※このメソッドのテストは手動で行うことを推奨（対話が必要なため）
        """
        import os
        project_root = os.path.abspath(".")
        oj_cache_host = os.path.join(project_root, ".oj/.cache/online-judge-tools")
        oj_cache_cont = "/workspace/.cache/online-judge-tools"
        oj_local_host = os.path.join(project_root, ".oj/.local/share/online-judge-tools")
        oj_local_cont = "/workspace/.local/share/online-judge-tools"
        volumes = {
            oj_cache_host: oj_cache_cont,
            oj_local_host: oj_local_cont,
            project_root: "/workspace"
        }
        workdir = "/workspace"
        # atcoder用URLを明示的に指定
        return await self.docker_operator.run_oj(["login", "https://atcoder.jp/"], volumes, workdir, interactive=True)

    async def open(self, contest_name, problem_name, language_name):
        """
        問題ファイルを準備し、VSCodeとCursorでディレクトリを開く
        """
        # 1. ファイル操作（テンプレート展開やcontest_stocksからの移動など）
        if self.file_manager:
            self.file_manager.prepare_problem_files(contest_name, problem_name, language_name)
        # 2. エディタでディレクトリを開く
        if self.opener:
            path = f"contest_current/{language_name}"
            self.opener.open_editor(path)
        # 3. 問題ページをブラウザで開く
        url = f"https://atcoder.jp/contests/{contest_name}/tasks/{contest_name}_{problem_name}"
        if self.opener:
            self.opener.open_browser(url)
        # 4. oj download（docker_operator経由で成果物を回収）
        cookie_host = ".oj/.local/share/online-judge-tools/cookie.jar"
        test_dir_host = f"contest_current/test"
        ok = self.docker_operator.run_oj_download(url, cookie_host, test_dir_host)
        if not ok:
            print(f"[エラー] oj download失敗: {url}")
            return

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
        file_operator = self.file_manager.file_operator if self.file_manager else None
        temp_dir, source_path = self.prepare_test_environment(contest_name, problem_name, language_name)
        test_dir = "contest_current/test"
        temp_source_path = str(temp_dir / pathlib.Path(source_path).name)
        temp_in_files, _ = self.collect_test_cases(temp_dir, test_dir, file_operator)
        results = await self.run_test_cases(temp_source_path, temp_in_files, language_name)
        return results

    # 言語ごとの提出ファイル名
    SUBMIT_FILES = {
        "python": "main.py",
        "pypy": "main.py",
        "rust": "main.rs",
    }

    def is_all_ac(self, results):
        for r in results:
            returncode, stdout, _ = r["result"]
            if returncode != 0 or stdout.strip() != r["expected"].strip():
                return False
        return True

    def confirm_submit_with_wa(self):
        ans = input("AC以外のケースがあります。提出してよいですか？ (y/N): ")
        return ans.lower() in ("y", "yes")

    def validate_info_file(self, info_path, contest_name, problem_name, file_operator=None):
        if file_operator:
            if not file_operator.exists(info_path):
                return None
            with file_operator.open(info_path, "r", encoding="utf-8") as f:
                info = json.load(f)
        else:
            if not os.path.exists(info_path):
                return None
            with open(info_path, "r", encoding="utf-8") as f:
                info = json.load(f)
        current_contest = info.get("contest_name")
        current_problem = info.get("problem_name")
        if current_contest and current_contest != contest_name:
            print(f"[警告] contest_current/info.jsonのcontest_name（{current_contest}）と指定されたcontest_name（{contest_name}）が異なります。提出を中止します。")
            return None
        if current_problem and current_problem != problem_name:
            print(f"[警告] contest_current/info.jsonのproblem_name（{current_problem}）と指定されたproblem_name（{problem_name}）が異なります。提出を中止します。")
            return None
        return info

    def get_language_id_from_config(self, config_path, language_name, file_operator=None):
        if file_operator:
            if not file_operator.exists(config_path):
                return None
            with file_operator.open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            if not os.path.exists(config_path):
                return None
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        language_id_dict = config.get("language_id", {})
        return language_id_dict.get(language_name)

    def build_submit_command(self, contest_name, problem_name, language_name, file_path, language_id):
        url = f"https://atcoder.jp/contests/{contest_name}/tasks/{contest_name}_{problem_name}"
        args = ["submit", url, file_path, "--yes"]
        if language_id:
            args += ["--language", language_id]
        args += ["--wait=0"]
        return args, url

    async def run_submit_command(self, args, volumes, workdir):
        rc, stdout, stderr = await self.docker_operator.run_oj(args, volumes, workdir, interactive=True)
        if rc != 0:
            print(f"[エラー] oj submit失敗 (returncode={rc})\n{stderr}")
        return rc, stdout, stderr

    async def submit(self, contest_name, problem_name, language_name):
        results = await self.run_test_return_results(contest_name, problem_name, language_name)
        self.print_test_results(results)
        if not self.is_all_ac(results):
            if not self.confirm_submit_with_wa():
                print("提出を中止しました。")
                return
        file_operator = self.file_manager.file_operator if self.file_manager else None
        info_path = os.path.join("contest_current", "info.json")
        config_path = os.path.join("contest_current", "config.json")
        info = self.validate_info_file(info_path, contest_name, problem_name, file_operator)
        if info is None:
            return None
        language_id = self.get_language_id_from_config(config_path, language_name, file_operator)
        project_root = os.path.abspath(".")
        oj_cache_host = os.path.join(project_root, ".oj/.cache/online-judge-tools")
        oj_cache_cont = "/workspace/.cache/online-judge-tools"
        oj_local_host = os.path.join(project_root, ".oj/.local/share/online-judge-tools")
        oj_local_cont = "/workspace/.local/share/online-judge-tools"
        volumes = {
            oj_cache_host: oj_cache_cont,
            oj_local_host: oj_local_cont,
            project_root: "/workspace"
        }
        workdir = "/workspace"
        submit_file = self.SUBMIT_FILES.get(language_name, "main.py")
        temp_file_path = f".temp/{submit_file}"
        if file_operator:
            temp_file_exists = file_operator.exists(temp_file_path)
        else:
            temp_file_exists = os.path.exists(temp_file_path)
        if temp_file_exists:
            file_path = temp_file_path
        else:
            file_path = f"contest_current/{language_name}/{submit_file}"
        args, url = self.build_submit_command(contest_name, problem_name, language_name, file_path, language_id)
        return await self.run_submit_command(args, volumes, workdir)

    async def execute(self, command, contest_name=None, problem_name=None, language_name=None):
        """コマンド名に応じて各メソッドを呼び出す"""
        if command == "login":
            return await self.login()
        elif command == "open":
            return await self.open(contest_name, problem_name, language_name)
        elif command == "submit":
            return await self.submit(contest_name, problem_name, language_name)
        elif command == "test":
            return await self.run_test(contest_name, problem_name, language_name)
        else:
            raise ValueError(f"未対応のコマンドです: {command}")

class MockOpener(Opener):
    def __init__(self):
        self.opened_paths = []
        self.opened_urls = []
    def open_editor(self, path: str):
        main_file = f"{path}/main.py"
        self.opened_paths.append(main_file)
    def open_browser(self, url: str):
        self.opened_urls.append(url) 