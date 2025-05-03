from podman_operator import PodmanOperator, LocalPodmanOperator
from contest_file_manager import ContestFileManager

class CommandExecutor:
    def __init__(self, podman_operator: PodmanOperator = None, file_manager: ContestFileManager = None):
        self.podman_operator = podman_operator or LocalPodmanOperator()
        self.file_manager = file_manager

    async def login(self, *args, **kwargs):
        """
        online-judge-toolsでログインする（ojtラッパー）
        ※このメソッドのテストは手動で行うことを推奨（対話が必要なため）
        """
        import os
        home = os.path.expanduser("~")
        oj_cache_host = os.path.join(home, ".cache/online-judge-tools")
        oj_cache_cont = "/root/.cache/online-judge-tools"
        volumes = {oj_cache_host: oj_cache_cont}
        workdir = "/workspace"
        return await self.podman_operator.run_oj(["login"], volumes, workdir, interactive=True)

    async def open(self, contest_name, problem_name, language_name):
        """
        online-judge-toolsで問題データ取得（ojtラッパー）
        ※このメソッドのテストは手動で行うことを推奨（対話が必要な場合があるため）
        """
        # 1. ファイル操作（テンプレート展開やcontest_stocksからの移動など）
        if self.file_manager:
            self.file_manager.prepare_problem_files(contest_name, problem_name, language_name)
        # 2. oj download（テスト時はMockPodmanOperatorでスキップ可能）
        url = f"https://atcoder.jp/contests/{contest_name}/tasks/{contest_name}_{problem_name}"
        import os
        home = os.path.expanduser("~")
        oj_cache_host = os.path.join(home, ".cache/online-judge-tools")
        oj_cache_cont = "/root/.cache/online-judge-tools"
        volumes = {oj_cache_host: oj_cache_cont}
        workdir = "/workspace"
        await self.podman_operator.run_oj(["download", url], volumes, workdir, interactive=False)

    async def submit(self, contest_name, problem_name, language_name):
        """
        online-judge-toolsで提出（ojtラッパー）
        ※このメソッドのテストは手動で行うことを推奨（対話が必要な場合があるため）
        """
        raise NotImplementedError("submitコマンドの実装が必要です")

    async def test(self, contest_name, problem_name, language_name):
        """独自実装でテストを行う"""
        raise NotImplementedError("testコマンドの実装が必要です")

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