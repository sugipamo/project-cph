from pathlib import Path
from file_operator import FileOperator

class ContestFileManager:
    def __init__(self, file_operator: FileOperator):
        self.file_operator = file_operator

    def move_from_stocks_to_current(self, contest_name, problem_name, language_name):
        """contest_stocksからcontest_currentへ該当問題ファイルを移動する"""
        src = Path(f"../contest_stocks/{contest_name}/{language_name}/{problem_name}/main.py")
        dst = Path(f"../contest_current/{language_name}/{problem_name}/main.py")
        self.file_operator.move(src, dst)

    def copy_from_template_to_current(self, contest_name, problem_name, language_name):
        """contest_templateからcontest_currentへ該当問題ファイルをコピーする"""
        src = Path(f"../contest_template/{language_name}/main.py")
        dst = Path(f"../contest_current/{language_name}/{problem_name}/main.py")
        self.file_operator.copy(src, dst)

    def problem_exists_in_stocks(self, contest_name, problem_name, language_name):
        """contest_stocksに該当問題ファイルが存在するか確認する"""
        src = Path(f"../contest_stocks/{contest_name}/{language_name}/{problem_name}/main.py")
        return self.file_operator.exists(src)

    def problem_exists_in_current(self, contest_name, problem_name, language_name):
        """contest_currentに該当問題ファイルが存在するか確認する"""
        dst = Path(f"../contest_current/{language_name}/{problem_name}/main.py")
        return self.file_operator.exists(dst)

    def prepare_problem_files(self, contest_name, problem_name, language_name):
        """
        問題ファイルをcontest_currentに準備する。
        - contest_stocksにあればmove
        - なければtemplateからcopy
        - どちらもなければ例外
        """
        if self.problem_exists_in_stocks(contest_name, problem_name, language_name):
            self.move_from_stocks_to_current(contest_name, problem_name, language_name)
        elif self.file_operator.exists(Path(f"../contest_template/{language_name}/main.py")):
            self.copy_from_template_to_current(contest_name, problem_name, language_name)
        else:
            raise FileNotFoundError("問題ファイルがcontest_stocksにもtemplateにも存在しません") 