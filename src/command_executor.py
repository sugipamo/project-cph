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

class EditorOpener:
    def open(self, path: str):
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
            self._format_header_bar(),
            self._format_input(),
            self._format_input_error_bar(),
            self._format_error(),
            self._format_table()
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

    def _format_header_bar(self):
        return "=" * 17

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
        max_exp = max([len(s) for s in exp_lines]) if exp_lines else 0
        max_out = max([len(s) for s in out_lines]) if out_lines else 0
        max_len = max(len(exp_lines), len(out_lines))
        if max_len == 0:
            return ""
        lines = []
        for i in range(max_len):
            exp = exp_lines[i] if i < len(exp_lines) else ""
            out = out_lines[i] if i < len(out_lines) else ""
            lines.append(f"{exp:<{max_exp}} | {out:<{max_out}}")
        return "\n".join(lines)

class CommandExecutor:
    def __init__(self, docker_operator: DockerOperator = None, file_manager: ContestFileManager = None, editor_opener: EditorOpener = None):
        self.docker_operator = docker_operator or LocalDockerOperator()
        self.file_manager = file_manager
        self.editor_opener = editor_opener or EditorOpener()

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
        if self.editor_opener:
            path = f"contest_current/{language_name}"
            self.editor_opener.open(path)
        # 3. oj download（docker_operator経由で成果物を回収）
        url = f"https://atcoder.jp/contests/{contest_name}/tasks/{contest_name}_{problem_name}"
        cookie_host = ".oj/.local/share/online-judge-tools/cookie.jar"
        test_dir_host = f"contest_current/test"
        ok = self.docker_operator.run_oj_download(url, cookie_host, test_dir_host)
        if not ok:
            print(f"[エラー] oj download失敗: {url}")
            return

    async def run_test(self, contest_name, problem_name, language_name):
        """ビルド→実行を言語ごとに抽象化してテストする（合否判定・レイアウト付き）"""
        import shutil
        file_operator = self.file_manager.file_operator if self.file_manager else None
        source_path = f"contest_current/{language_name}/main.py"
        test_dir = "contest_current/test"
        if language_name == "python":
            runner = PythonRunner(source_path, None, self.docker_operator)
        elif language_name == "pypy":
            runner = PypyRunner(source_path, None, self.docker_operator)
        elif language_name == "rust":
            # rustはmain.rsを使う
            source_path = f"contest_current/{language_name}/main.rs"
            runner = RustRunner(source_path, None, self.docker_operator)
        else:
            print(f"未対応の言語です: {language_name}")
            return
        build_ok = await runner.build()
        if not build_ok:
            print("ビルド失敗")
            return
        if file_operator:
            in_files = sorted(file_operator.glob(f"{test_dir}/*.in"))
        else:
            import glob
            in_files = sorted(glob.glob(os.path.join(test_dir, "*.in")))

        async def run_one(in_file):
            import time
            start = time.monotonic()
            result = await runner.run(input_path=in_file)
            elapsed = time.monotonic() - start
            out_file = str(in_file)[:-3] + ".out"
            expected = ""
            if file_operator and file_operator.exists(out_file):
                with file_operator.open(out_file, "r", encoding="utf-8") as f:
                    expected = f.read()
            elif not file_operator and os.path.exists(out_file):
                with open(out_file, "r", encoding="utf-8") as f:
                    expected = f.read()
            # 実行失敗時のエラー出力
            if result[0] != 0:
                print(f"[エラー] テストケース {os.path.basename(str(in_file))} 実行失敗 (returncode={result[0]})\n{result[2]}")
            return {
                "name": os.path.basename(str(in_file)),
                "result": result,
                "time": elapsed,
                "expected": expected,
                "in_file": in_file,
            }

        tasks = [run_one(in_file) for in_file in in_files]
        import asyncio
        results = await asyncio.gather(*tasks)

        for idx, r in enumerate(results):
            print(TestResultFormatter(r).format())

    # 言語ごとの提出ファイル名
    SUBMIT_FILES = {
        "python": "main.py",
        "pypy": "main.py",
        "rust": "main.rs",
    }

    async def submit(self, contest_name, problem_name, language_name):
        """online-judge-toolsで提出する"""
        file_operator = self.file_manager.file_operator if self.file_manager else None
        info_path = os.path.join("contest_current", "info.json")
        info_exists = file_operator.exists(info_path) if file_operator else os.path.exists(info_path)
        if info_exists:
            if file_operator:
                with file_operator.open(info_path, "r", encoding="utf-8") as f:
                    info = json.load(f)
            else:
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
        # 提出ファイルパス（言語ごとに切り替え）
        submit_file = self.SUBMIT_FILES.get(language_name, "main.py")
        file_path = f"contest_current/{language_name}/{submit_file}"
        # 問題URL
        url = f"https://atcoder.jp/contests/{contest_name}/tasks/{contest_name}_{problem_name}"
        # oj submitコマンド
        args = ["submit", url, file_path, "--yes"]
        rc, stdout, stderr = await self.docker_operator.run_oj(args, volumes, workdir, interactive=True)
        if rc != 0:
            print(f"[エラー] oj submit失敗 (returncode={rc})\n{stderr}")
        return rc, stdout, stderr

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

class MockEditorOpener(EditorOpener):
    def __init__(self):
        self.opened_paths = []
    def open(self, path: str):
        main_file = f"{path}/main.py"
        self.opened_paths.append(main_file) 