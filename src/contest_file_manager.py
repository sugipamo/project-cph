from pathlib import Path
from file_operator import FileOperator
import shutil
import os

class ContestFileManager:
    def __init__(self, file_operator: FileOperator):
        self.file_operator = file_operator

    def move_from_stocks_to_current(self, contest_name, problem_name, language_name):
        """
        contest_stocks/{contest_name}/{language}/配下をディレクトリごとcontest_current/{language}/に移動する
        """
        src_dir = Path(f"contest_stocks/{contest_name}/{language_name}")
        dst_dir = Path(f"contest_current/{language_name}")
        if not src_dir.exists():
            raise FileNotFoundError(f"{src_dir}が存在しません")
        # ディレクトリごと移動
        for item in src_dir.iterdir():
            if item.is_file():
                dst_file = dst_dir / item.name
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(item), str(dst_file))
            elif item.is_dir():
                shutil.move(str(item), str(dst_dir / item.name))
        # 元ディレクトリを削除
        if not any(src_dir.iterdir()):
            src_dir.rmdir()

    def copy_from_template_to_current(self, contest_name, problem_name, language_name):
        """
        contest_template/{language}/配下をcontest_current/{language}/にコピーする
        """
        src_dir = Path(f"contest_template/{language_name}")
        dst_dir = Path(f"contest_current/{language_name}")
        if not src_dir.exists():
            raise FileNotFoundError(f"{src_dir}が存在しません")
        # ディレクトリごとコピー
        for item in src_dir.iterdir():
            if item.is_file():
                dst_file = dst_dir / item.name
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(item), str(dst_file))
            elif item.is_dir():
                shutil.copytree(str(item), str(dst_dir / item.name), dirs_exist_ok=True)

    def problem_exists_in_stocks(self, contest_name, problem_name, language_name):
        src_dir = Path(f"contest_stocks/{contest_name}/{language_name}")
        return src_dir.exists() and any(src_dir.iterdir())

    def problem_exists_in_current(self, contest_name, problem_name, language_name):
        dst_dir = Path(f"contest_current/{language_name}")
        return dst_dir.exists() and any(dst_dir.iterdir())

    def prepare_problem_files(self, contest_name, problem_name, language_name):
        """
        問題ファイルをcontest_currentに準備する。
        - contest_stocksにあればmove
        - なければtemplateからcopy
        - どちらもなければ例外
        """
        if self.problem_exists_in_stocks(contest_name, problem_name, language_name):
            self.move_from_stocks_to_current(contest_name, problem_name, language_name)
        elif Path(f"contest_template/{language_name}").exists():
            self.copy_from_template_to_current(contest_name, problem_name, language_name)
        else:
            raise FileNotFoundError("問題ファイルがcontest_stocksにもtemplateにも存在しません") 