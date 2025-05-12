from src.execution_env.info_json_manager import InfoJsonManager
from src.execution_client.container.pool import ContainerPool
from src.execution_client.client.container import ContainerClient
from src.execution_client.container.image_manager import ContainerImageManager
from src.path_manager.unified_path_manager import UnifiedPathManager
from src.file.file_operator import FileOperator
from src.file.config_json_manager import ConfigJsonManager
from src.environment.test_environment import DockerTestExecutionEnvironment

class CommandOpen:
    def __init__(self, file_manager, opener, test_env):
        self.file_manager = file_manager
        self.opener = opener
        self.test_env = test_env
        self.upm = UnifiedPathManager()

    async def open(self, contest_name, problem_name, language_name):
        """
        問題ファイルを準備し、VSCodeとCursorでディレクトリを開く
        必要なコンテナを事前に起動し、system_info.jsonで管理する
        """
        import os
        import subprocess
        file_operator = self.file_manager.file_operator if self.file_manager and hasattr(self.file_manager, 'file_operator') else None
        # 1. 問題ファイル準備（system_info.jsonもここで更新される）
        if self.file_manager:
            self.file_manager.prepare_problem_files(contest_name, problem_name, language_name)
            problem_dir, test_dir = self.file_manager.get_problem_files(contest_name, problem_name, language_name)
        
        # 2. 問題ページをブラウザで開く
        url = f"https://atcoder.jp/contests/{contest_name}/tasks/{contest_name}_{problem_name}"
        if self.opener:
            self.opener.open_browser(url)
            # entry_file（config.json）を参照して開く
            config_path = self.upm.config_json()
            config_manager = ConfigJsonManager(config_path)
            entry_file = config_manager.get_entry_file(language_name)
            if entry_file:
                entry_path = self.upm.contest_current(language_name, entry_file)
                self.opener.open_editor(str(entry_path), language_name)
            else:
                self.opener.open_editor(str(problem_dir), language_name)
        
        # 3. テストケース数カウント
        if file_operator:
            # base_dirからの相対パス＋パターンでglobする
            test_dir_rel = os.path.relpath(self.upm.contest_current("test"), file_operator.base_dir)
            pattern = os.path.join(test_dir_rel, "*.in")
            test_case_count = len(list(file_operator.glob(pattern)))
        else:
            test_case_count = len([f for f in os.listdir(test_dir) if f.endswith('.in')]) if os.path.exists(test_dir) else 0
        
        # 4. 必要なコンテナ・環境を調整
        requirements = [
            {"type": "test", "language": language_name, "count": test_case_count},
            {"type": "ojtools", "count": 1, "volumes": {
                "/home/cphelper/.local/share/online-judge-tools/cookie.jar": "/root/.local/share/online-judge-tools/cookie.jar"
            }}
        ]
        containers = self.test_env.adjust_containers(requirements, contest_name, problem_name, language_name)
        # 5. system_info.jsonの更新はadjust_containersで一括実施済み
        info_path = self.upm.info_json()
        manager = InfoJsonManager(info_path)
        # 6. テストケースダウンロード（oj download）
        self.test_env.download_testcases(url, self.upm.contest_current("test"))