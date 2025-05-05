SUBMIT_FILES = {
    "python": "main.py",
    "pypy": "main.py",
    "rust": "src/main.rs",
}

from commands.command_test import CommandTest

class CommandSubmit:
    def __init__(self, docker_operator, file_manager):
        self.docker_operator = docker_operator
        self.file_manager = file_manager
        self.command_test = CommandTest(docker_operator, file_manager)

    def confirm_submit_with_wa(self):
        ans = input("AC以外のケースがあります。提出してよいですか？ (y/N): ")
        return ans.lower() in ("y", "yes")

    def validate_info_file(self, info_path, contest_name, problem_name, file_operator=None):
        import os
        import json
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

    async def run_submit_command(self, args, volumes, workdir):
        rc, stdout, stderr = await self.docker_operator.run_oj(args, volumes, workdir, interactive=True)
        if rc != 0:
            print(f"[エラー] oj submit失敗 (returncode={rc})\n{stderr}")
        return rc, stdout, stderr

    async def submit(self, contest_name, problem_name, language_name):
        results = await self.command_test.run_test_return_results(contest_name, problem_name, language_name)
        self.command_test.print_test_results(results)
        if not self.command_test.is_all_ac(results):
            if not self.confirm_submit_with_wa():
                print("提出を中止しました。")
                return
        file_operator = self.file_manager.file_operator if self.file_manager else None
        import os
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
        submit_file = SUBMIT_FILES.get(language_name, "main.py")
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