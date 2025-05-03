from podman_operator import PodmanOperator, LocalPodmanOperator
from contest_file_manager import ContestFileManager
import subprocess
from command_parser import CommandParser
import shutil
import glob
import os
import json

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

class CommandExecutor:
    def __init__(self, podman_operator: PodmanOperator = None, file_manager: ContestFileManager = None, editor_opener: EditorOpener = None):
        self.podman_operator = podman_operator or LocalPodmanOperator()
        self.file_manager = file_manager
        self.editor_opener = editor_opener or EditorOpener()

    async def login(self, *args, **kwargs):
        """
        online-judge-toolsでログインする（ojtラッパー）
        ※このメソッドのテストは手動で行うことを推奨（対話が必要なため）
        """
        import os
        home = os.path.expanduser("~")
        oj_cache_host = os.path.join(home, ".cache/online-judge-tools")
        oj_cache_cont = "/root/.cache/online-judge-tools"
        project_root = os.path.abspath(".")
        volumes = {oj_cache_host: oj_cache_cont, project_root: "/workspace"}
        workdir = "/workspace"
        # atcoder用URLを明示的に指定
        return await self.podman_operator.run_oj(["login", "https://atcoder.jp/"], volumes, workdir, interactive=True)

    async def open(self, contest_name, problem_name, language_name):
        """
        問題ファイルを準備し、VSCodeとCursorでディレクトリを開く
        """
        import shutil
        import glob
        import os
        # 1. ファイル操作（テンプレート展開やcontest_stocksからの移動など）
        if self.file_manager:
            self.file_manager.prepare_problem_files(contest_name, problem_name, language_name)
        # 2. エディタでディレクトリを開く
        if self.editor_opener:
            path = f"contest_current/{language_name}"
            self.editor_opener.open(path)
        # 3. oj download（テスト時はMockPodmanOperatorでスキップ可能）
        if self.podman_operator:
            url = f"https://atcoder.jp/contests/{contest_name}/tasks/{contest_name}_{problem_name}"
            home = os.path.expanduser("~")
            oj_cache_host = os.path.join(home, ".cache/online-judge-tools")
            oj_cache_cont = "/root/.cache/online-judge-tools"
            project_root = os.path.abspath(".")
            volumes = {oj_cache_host: oj_cache_cont, project_root: "/workspace"}
            temp_dir = os.path.join(project_root, ".temp")
            workdir = "/workspace/.temp"
            os.makedirs(temp_dir, exist_ok=True)
            await self.podman_operator.run_oj(["download", url], volumes, workdir, interactive=False)
            # 既存のテストケースをcontest_stocksに退避
            dest_dir = os.path.join(project_root, f"contest_current/test")
            tests_root = dest_dir
            if self.file_manager:
                self.file_manager.move_tests_to_stocks(contest_name, problem_name, tests_root)
            os.makedirs(dest_dir, exist_ok=True)
            src_test_dir = os.path.join(temp_dir, "test")
            if os.path.isdir(src_test_dir):
                for file in glob.glob(os.path.join(src_test_dir, "*")):
                    shutil.move(file, dest_dir)
                os.rmdir(src_test_dir)
            shutil.rmtree(temp_dir)

    async def test(self, contest_name, problem_name, language_name):
        """独自実装でテストを行う"""
        raise NotImplementedError("testコマンドの実装が必要です")

    async def submit(self, contest_name, problem_name, language_name):
        """online-judge-toolsで提出する"""
        info_path = os.path.join("contest_current", "info.json")
        if os.path.exists(info_path):
            with open(info_path, "r", encoding="utf-8") as f:
                info = json.load(f)
            current_problem = info.get("problem_name")
            if current_problem and current_problem != problem_name:
                print(f"[警告] contest_current/info.jsonのproblem_name（{current_problem}）と指定されたproblem_name（{problem_name}）が異なります。提出を中止します。")
                return
        home = os.path.expanduser("~")
        oj_cache_host = os.path.join(home, ".cache/online-judge-tools")
        oj_cache_cont = "/root/.cache/online-judge-tools"
        project_root = os.path.abspath(".")
        volumes = {oj_cache_host: oj_cache_cont, project_root: "/workspace"}
        workdir = "/workspace"
        # 提出ファイルパス
        file_path = f"contest_current/{language_name}/main.py"
        # 問題URL
        url = f"https://atcoder.jp/contests/{contest_name}/tasks/{contest_name}_{problem_name}"
        # oj submitコマンド
        args = ["submit", url, file_path, "--yes"]
        return await self.podman_operator.run_oj(args, volumes, workdir, interactive=True)

    async def execute(self, command, contest_name=None, problem_name=None, language_name=None):
        """コマンド名に応じて各メソッドを呼び出す"""
        if command == "login":
            return await self.login()
        elif command == "open":
            return await self.open(contest_name, problem_name, language_name)
        elif command == "submit":
            return await self.submit(contest_name, problem_name, language_name)
        elif command == "test":
            return await self.test(contest_name, problem_name, language_name)
        else:
            raise ValueError(f"未対応のコマンドです: {command}")

class MockEditorOpener(EditorOpener):
    def __init__(self):
        self.opened_paths = []
    def open(self, path: str):
        main_file = f"{path}/main.py"
        self.opened_paths.append(main_file) 