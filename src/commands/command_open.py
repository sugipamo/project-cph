

class CommandOpen:
    def __init__(self, file_manager, opener, test_env):
        self.file_manager = file_manager
        self.opener = opener
        self.test_env = test_env
        self.upm = UnifiedPathManager()

    async def open(self, contest_name, problem_name):
        """
        問題ファイルを準備し、VSCodeとCursorでディレクトリを開く
        必要なコンテナを事前に起動し、system_info.jsonで管理する
        """
        import os
        import subprocess
        file_operator = self.file_manager.file_operator if self.file_manager and hasattr(self.file_manager, 'file_operator') else None
        # 1. 問題ファイル準備（system_info.jsonもここで更新される）
        if self.file_manager:
            self.file_manager.prepare_problem_files(contest_name, problem_name, self.language_name)
            problem_dir, test_dir = self.file_manager.get_problem_files(contest_name, problem_name, self.language_name)
        
        # 2. 問題ページをブラウザで開く
        url = f"https://atcoder.jp/contests/{contest_name}/tasks/{contest_name}_{problem_name}"
        if self.opener:
            self.opener.open_browser(url)
            # entry_file（Configクラス）を参照して開く
            entry_file = LanguageConfigAccessor.get_entry_file(self.language_name)
            if entry_file:
                entry_path = self.upm.contest_current(self.language_name, entry_file)
                self.opener.open_editor(str(entry_path), self.language_name)
            else:
                self.opener.open_editor(str(problem_dir), self.language_name)
        
        print("[DEBUG] open: contest_name=", contest_name, "problem_name=", problem_name, "language_name=", self.language_name, flush=True)
        # 3. テストケース数カウント
        if file_operator:
            # base_dirからの相対パス＋パターンでglobする
            test_dir_rel = os.path.relpath(self.upm.contest_current("test"), file_operator.base_dir)
            pattern = os.path.join(test_dir_rel, "*.in")
            test_case_count = len(list(file_operator.glob(pattern)))
        else:
            test_case_count = len([f for f in os.listdir(test_dir) if f.endswith('.in')]) if os.path.exists(test_dir) else 0
        
        print("[DEBUG] open: test_case_count=", test_case_count, flush=True)
        # 4. 必要なコンテナ・環境を調整
        requirements = [
            {"type": "test", "language": self.language_name, "count": test_case_count},
            {"type": "ojtools", "count": 1, "volumes": {
                "/home/cphelper/.local/share/online-judge-tools/cookie.jar": "/root/.local/share/online-judge-tools/cookie.jar"
            }}
        ]
        print("[DEBUG] open: requirements=", requirements, flush=True)
        containers = self.test_env.resource_manager.adjust_resources(requirements, contest_name, problem_name, self.language_name)
        print("[DEBUG] open: containers after adjust_resources=", containers, flush=True)
        # 5. system_info.jsonの更新はadjust_resourcesで一括実施済み
        info_path = self.upm.info_json()
        manager = InfoJsonManager(info_path)
        # 6. テストケースダウンロード（oj download）
        print("[DEBUG] open: download_testcases url=", url, flush=True)
        self.test_env.file_ops.download_testcases(url, self.upm.contest_current("test"))