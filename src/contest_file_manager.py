from pathlib import Path
from src.file_operator import FileOperator

class ContestFileManager:
    def __init__(self, file_operator: FileOperator):
        self.file_operator = file_operator

    def move_from_stocks_to_current(self, contest_name, problem_name, language_name):
        """contest_stocksからcontest_currentへ該当問題ファイルを移動する"""
        raise NotImplementedError("move_from_stocks_to_currentの実装が必要です")

    def copy_from_template_to_current(self, contest_name, problem_name, language_name):
        """contest_templateからcontest_currentへ該当問題ファイルをコピーする"""
        raise NotImplementedError("copy_from_template_to_currentの実装が必要です")

    def problem_exists_in_stocks(self, contest_name, problem_name, language_name):
        """contest_stocksに該当問題ファイルが存在するか確認する"""
        raise NotImplementedError("problem_exists_in_stocksの実装が必要です")

    def problem_exists_in_current(self, contest_name, problem_name, language_name):
        """contest_currentに該当問題ファイルが存在するか確認する"""
        raise NotImplementedError("problem_exists_in_currentの実装が必要です") 