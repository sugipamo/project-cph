import json
from pathlib import Path
from file_operator import FileOperator
import shutil
import os

class ContestFileManager:
    def __init__(self, file_operator: FileOperator):
        self.file_operator = file_operator

    def get_current_info_path(self):
        return Path("contest_current/info.json")

    def get_current_config_path(self):
        return Path("contest_current/config.json")

    def get_exclude_files(self, config_path):
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config.get("exclude_files", [])
        return []

    def _remove_empty_parents(self, path, stop_at):
        """
        path: Pathオブジェクト。空なら削除し、stop_atまで親を再帰的に辿る。
        stop_at: これ以上は削除しないディレクトリ（Pathオブジェクト）
        """
        while path != stop_at and path.exists() and path.is_dir() and not any(path.iterdir()):
            path.rmdir()
            path = path.parent

    def move_current_to_stocks(self, problem_name, language_name):
        """
        contest_current/{language}/{problem_name}配下のファイルを、info.jsonのcontest_nameを参照してcontest_stocks/{contest_name}/{language}/{problem_name}/に移動する
        config.jsonのexclude_filesに含まれるファイルは移動しない
        info.json, config.jsonはcontest_current/に残す
        """
        src_dir = Path(f"contest_current/{language_name}/{problem_name}")
        info_path = self.get_current_info_path()
        config_path = self.get_current_config_path()
        if not src_dir.exists() or not info_path.exists():
            return
        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)
        old_contest_name = info.get("contest_name")
        if not old_contest_name:
            return
        dst_dir = Path(f"contest_stocks/{old_contest_name}/{language_name}/{problem_name}")
        dst_dir.mkdir(parents=True, exist_ok=True)
        exclude_files = self.get_exclude_files(config_path)
        for item in src_dir.iterdir():
            if item.name in exclude_files:
                continue
            shutil.move(str(item), str(dst_dir / item.name))
        # src_dirが空になったら削除
        if not any(x for x in src_dir.iterdir() if x.name not in exclude_files):
            src_dir.rmdir()
        # 親ディレクトリも空なら再帰的に削除
        self._remove_empty_parents(src_dir.parent, Path(f"contest_stocks/{old_contest_name}"))
        self._remove_empty_parents(src_dir.parent.parent, Path("contest_stocks"))
        # info.json, config.jsonはcontest_current/に残す

    def move_from_stocks_to_current(self, contest_name, problem_name, language_name):
        """
        contest_stocks/{contest_name}/{language}/{problem_name}/配下をディレクトリごとcontest_current/{language}/{problem_name}/に移動する
        移動後、空になったディレクトリは削除する
        info.json, config.jsonはcontest_current/に作成
        """
        src_dir = Path(f"contest_stocks/{contest_name}/{language_name}/{problem_name}")
        dst_dir = Path(f"contest_current/{language_name}/{problem_name}")
        if not src_dir.exists():
            raise FileNotFoundError(f"{src_dir}が存在しません")
        config_path = self.get_current_config_path()
        exclude_files = self.get_exclude_files(config_path)
        for item in src_dir.iterdir():
            if item.name in exclude_files:
                continue
            if item.is_file():
                dst_file = dst_dir / item.name
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(item), str(dst_file))
            elif item.is_dir():
                shutil.move(str(item), str(dst_dir / item.name))
        # info.jsonを新しいcontest_nameでcontest_current/に作成
        info_path = self.get_current_info_path()
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump({"contest_name": contest_name, "problem_name": problem_name, "language_name": language_name}, f, ensure_ascii=False, indent=2)
        # config.jsonがなければデフォルト作成
        if not config_path.exists():
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump({"exclude_files": []}, f, ensure_ascii=False, indent=2)
        # 元ディレクトリを削除（空なら）
        if not any(src_dir.iterdir()):
            src_dir.rmdir()
            # 親ディレクトリも空なら再帰的に削除
            self._remove_empty_parents(src_dir.parent, Path(f"contest_stocks/{contest_name}"))
            self._remove_empty_parents(src_dir.parent.parent, Path("contest_stocks"))

    def copy_from_template_to_current(self, contest_name, problem_name, language_name):
        """
        contest_template/{language}/ 配下のファイルを contest_current/{language}/{problem_name}/ にコピーする
        info.json, config.jsonはcontest_current/に作成
        """
        src_dir = Path(f"contest_template/{language_name}")
        dst_dir = Path(f"contest_current/{language_name}/{problem_name}")
        if not src_dir.exists():
            raise FileNotFoundError(f"{src_dir}が存在しません")
        config_path = self.get_current_config_path()
        exclude_files = self.get_exclude_files(config_path)
        for item in src_dir.iterdir():
            if item.name in exclude_files:
                continue
            if item.is_file():
                dst_file = dst_dir / item.name
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(item), str(dst_file))
            elif item.is_dir():
                shutil.copytree(str(item), str(dst_dir / item.name), dirs_exist_ok=True)
        # info.jsonをcontest_current/に作成
        info_path = self.get_current_info_path()
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump({"contest_name": contest_name, "problem_name": problem_name, "language_name": language_name}, f, ensure_ascii=False, indent=2)
        # config.jsonがなければデフォルト作成
        if not config_path.exists():
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump({"exclude_files": []}, f, ensure_ascii=False, indent=2)

    def problem_exists_in_stocks(self, contest_name, problem_name, language_name):
        src_dir = Path(f"contest_stocks/{contest_name}/{language_name}/{problem_name}")
        return src_dir.exists() and any(src_dir.iterdir())

    def problem_exists_in_current(self, contest_name, problem_name, language_name):
        dst_dir = Path(f"contest_current/{language_name}/{problem_name}")
        return dst_dir.exists() and any(dst_dir.iterdir())

    def prepare_problem_files(self, contest_name=None, problem_name=None, language_name=None):
        """
        info.jsonに contest_name, problem_name, language_name をすべて保存し、
        次回実行時の初期値として利用できるようにする。
        引数がNoneの場合はinfo.jsonの値を使う。
        """
        info_path = self.get_current_info_path()
        # info.jsonがあれば初期値として利用
        if info_path.exists():
            with open(info_path, "r", encoding="utf-8") as f:
                info = json.load(f)
            if contest_name is None:
                contest_name = info.get("contest_name")
            if problem_name is None:
                problem_name = info.get("problem_name")
            if language_name is None:
                language_name = info.get("language_name")
        # 以降は従来通り
        self.move_current_to_stocks(problem_name, language_name)
        if self.problem_exists_in_stocks(contest_name, problem_name, language_name):
            self.move_from_stocks_to_current(contest_name, problem_name, language_name)
        elif Path(f"contest_template/{language_name}").exists():
            self.copy_from_template_to_current(contest_name, problem_name, language_name)
        else:
            raise FileNotFoundError("問題ファイルがcontest_stocksにもtemplateにも存在しません") 