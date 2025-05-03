class CommandExecutor:
    def login(self, *args, **kwargs):
        """online-judge-toolsでログインする（ojtラッパー）"""
        raise NotImplementedError("loginコマンドの実装が必要です")

    def open(self, contest_name, problem_name, language_name):
        """online-judge-toolsで問題データ取得（ojtラッパー）"""
        raise NotImplementedError("openコマンドの実装が必要です")

    def submit(self, contest_name, problem_name, language_name):
        """online-judge-toolsで提出（ojtラッパー）"""
        raise NotImplementedError("submitコマンドの実装が必要です")

    def test(self, contest_name, problem_name, language_name):
        """独自実装でテストを行う"""
        raise NotImplementedError("testコマンドの実装が必要です")

    def execute(self, command, contest_name=None, problem_name=None, language_name=None):
        """コマンド名に応じて各メソッドを呼び出す"""
        if command == "login":
            return self.login()
        elif command == "open":
            return self.open(contest_name, problem_name, language_name)
        elif command == "submit":
            return self.submit(contest_name, problem_name, language_name)
        elif command == "test":
            return self.test(contest_name, problem_name, language_name)
        else:
            raise ValueError(f"未対応のコマンドです: {command}") 