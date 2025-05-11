import os
HOST_PROJECT_ROOT = os.path.abspath(".")
CONTAINER_WORKSPACE = "/workspace"
TEMP_DIR = "/workspace/.temp"
from .command_test import CommandTest
from .common import get_project_root_volumes
from src.file.info_json_manager import InfoJsonManager
from src.execution_client.client.container import ContainerClient
from src.execution_client.container.image_manager import ContainerImageManager
from src.path_manager.unified_path_manager import UnifiedPathManager
from src.file.file_operator import FileOperator

SUBMIT_FILES = {
    "python": "main.py",
    "pypy": "main.py",
    "rust": "src/main.rs",
}

class CommandSubmit:
    def __init__(self, file_manager, test_env):
        self.file_manager = file_manager
        self.command_test = CommandTest(file_manager, test_env)
        self.upm = UnifiedPathManager()
        self.test_env = test_env

    def confirm_submit_with_wa(self):
        ans = input("AC以外のケースがあります。提出してよいですか？ (y/N): ")
        return ans.lower() in ("y", "yes")

    def validate_info_file(self, info_path, contest_name, problem_name, file_operator=None):
        manager = InfoJsonManager(info_path)
        info = manager.data
        current_contest = info.get("contest_name")
        current_problem = info.get("problem_name")
        if current_contest and current_contest != contest_name:
            print(f"[警告] contest_current/system_info.jsonのcontest_name（{current_contest}）と指定されたcontest_name（{contest_name}）が異なります。提出を中止します。")
            return None
        if current_problem and current_problem != problem_name:
            print(f"[警告] contest_current/system_info.jsonのproblem_name（{current_problem}）と指定されたproblem_name（{problem_name}）が異なります。提出を中止します。")
            return None
        return info

    def get_language_id_from_config(self, config_path, language_name, file_operator=None):
        import os
        import json
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

    def get_ojtools_container_from_info(self):
        info_path = self.upm.info_json()
        manager = InfoJsonManager(info_path)
        for c in manager.get_containers(type="ojtools"):
            return c["name"]
        raise RuntimeError("ojtools用コンテナがsystem_info.jsonにありません")

    async def run_submit_command(self, args, volumes, workdir):
        # test_env経由で提出処理を実行
        return self.test_env.submit_via_ojtools(args, volumes, workdir)

    async def submit(self, contest_name, problem_name, language_name):
        results = await self.command_test.run_test_return_results(contest_name, problem_name, language_name)
        self.command_test.print_test_results(results)
        if not self.command_test.is_all_ac(results):
            if not self.confirm_submit_with_wa():
                print("提出を中止しました。")
                return
        file_operator = self.file_manager.file_operator if self.file_manager and hasattr(self.file_manager, 'file_operator') else None
        import os
        info_path = self.upm.info_json()
        config_path = self.upm.config_json()
        info = self.validate_info_file(info_path, contest_name, problem_name, file_operator)
        if info is None:
            return None
        language_id = self.get_language_id_from_config(config_path, language_name, file_operator)
        volumes = get_project_root_volumes()
        workdir = "/workspace"
        submit_file = SUBMIT_FILES.get(language_name, "main.py")
        temp_file_path = f".temp/{submit_file}"
        if file_operator:
            temp_file_exists = file_operator.exists(temp_file_path)
        else:
            temp_file_exists = os.path.exists(temp_file_path)
        if temp_file_exists:
            file_path = temp_file_path
        else:
            file_path = self.upm.contest_current(language_name, submit_file)
        # ファイルパスをコンテナ内パスに変換
        cont_file_path = self.test_env.to_container_path(file_path)
        args, url = self.build_submit_command(contest_name, problem_name, language_name, cont_file_path, language_id)
        temp_source_path, temp_test_dir = self.command_test.prepare_test_environment(contest_name, problem_name, language_name)
        temp_in_files, _ = self.command_test.collect_test_cases(temp_test_dir, file_operator)
        test_case_count = len(temp_in_files)
        requirements = [
            {"type": "test", "language": language_name, "count": test_case_count, "volumes": {
                HOST_PROJECT_ROOT: CONTAINER_WORKSPACE
            }},
            {"type": "ojtools", "count": 1, "volumes": {
                HOST_PROJECT_ROOT: CONTAINER_WORKSPACE,
                TEMP_DIR: "/workspace/.temp",
                "/home/cphelper/.local/share/online-judge-tools/cookie.jar": "/root/.local/share/online-judge-tools/cookie.jar"
            }}
        ]
        return await self.run_submit_command(args, volumes, workdir) 