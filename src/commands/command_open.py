class CommandOpen:
    def __init__(self, docker_operator, file_manager, opener):
        self.docker_operator = docker_operator
        self.file_manager = file_manager
        self.opener = opener

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
            self.opener.open_editor(path, language_name)
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