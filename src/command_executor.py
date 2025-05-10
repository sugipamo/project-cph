from src.file.contest_file_manager import ContestFileManager
from .commands.command_login import CommandLogin
from .commands.command_open import CommandOpen
from .commands.command_test import CommandTest
from .commands.command_submit import CommandSubmit
from .commands.opener import Opener
from src.environment.test_environment import DockerTestExecutionEnvironment
from src.environment.execution_manager_test_environment import ExecutionManagerTestEnvironment
from src.execution_client.execution_manager import ExecutionManager
from src.execution_client.container.client import ContainerClient

class CommandExecutor:
    def __init__(self, file_manager: ContestFileManager = None, opener: Opener = None, exec_mode: str = None):
        self.file_manager = file_manager
        self.opener = opener or Opener()
        self.exec_mode = exec_mode or "docker"
        self.login_handler = CommandLogin()
        # 実行環境の切り替え
        if self.exec_mode == "local":
            local_client = LocalAsyncClient()
            manager = ExecutionManager(local_client)
            test_env = ExecutionManagerTestEnvironment(self.file_manager, manager)
        else:
            # デフォルトはdocker
            test_env = DockerTestExecutionEnvironment(self.file_manager)
        self.open_handler = CommandOpen(self.file_manager, self.opener, test_env)
        self.test_handler = CommandTest(self.file_manager, test_env)
        self.submit_handler = CommandSubmit(self.file_manager, test_env)

    async def execute(self, command, contest_name=None, problem_name=None, language_name=None):
        """コマンド名に応じて各メソッドを呼び出す"""
        if command == "login":
            return await self.login_handler.login()
        elif command == "open":
            return await self.open_handler.open(contest_name, problem_name, language_name)
        elif command == "submit":
            return await self.submit_handler.submit(contest_name, problem_name, language_name)
        elif command == "test":
            return await self.test_handler.run_test(contest_name, problem_name, language_name)
        else:
            raise ValueError(f"未対応のコマンドです: {command}")

    async def open(self, contest_name, problem_name, language_name):
        return await self.open_handler.open(contest_name, problem_name, language_name)

    async def submit(self, contest_name, problem_name, language_name):
        return await self.submit_handler.submit(contest_name, problem_name, language_name)

    async def run_test(self, contest_name, problem_name, language_name):
        return await self.test_handler.run_test(contest_name, problem_name, language_name)

class MockOpener(Opener):
    def __init__(self):
        self.opened_paths = []
        self.opened_urls = []
    def open_editor(self, path: str, language: str = None):
        main_file = f"{path}/main.py"
        self.opened_paths.append(main_file)
    def open_browser(self, url: str):
        self.opened_urls.append(url) 