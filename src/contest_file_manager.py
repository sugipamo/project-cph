import json
from pathlib import Path
from file_operator import FileOperator
import shutil
import os
from commands.info_json_manager import InfoJsonManager

class ContestFileManager:
    def __init__(self, file_operator: FileOperator):
        self.file_operator = file_operator

    def get_current_info_path(self):
        return self.file_operator.resolve_path("contest_current/info.json")

    def get_current_config_path(self):
        return self.file_operator.resolve_path("contest_current/config.json")

    def get_exclude_files(self, config_path):
        """
        config.jsonのmoveignore（正規表現リスト）を返す
        """
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config.get("moveignore", [])
        return []

    def _is_ignored(self, name, ignore_patterns):
        import re
        for pat in ignore_patterns:
            if re.fullmatch(pat, name):
                return True
        return False

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
        contest_current/{language}/配下のファイルを、info.jsonのcontest_nameとproblem_nameを参照してcontest_stocks/{contest_name}/{problem_name}/に移動する
        config.jsonのmoveignoreに含まれるファイルは移動しない
        info.json, config.jsonはcontest_current/に残す
        """
        src_dir = self.file_operator.resolve_path(f"contest_current/{language_name}")
        info_path = self.get_current_info_path()
        config_path = self.get_current_config_path()
        if not src_dir.exists() or not info_path.exists():
            return
        manager = InfoJsonManager(info_path)
        info = manager.data
        old_contest_name = info.get("contest_name")
        old_problem_name = info.get("problem_name")
        if not old_contest_name or not old_problem_name:
            return
        dst_dir = self.file_operator.resolve_path(f"contest_stocks/{old_contest_name}/{old_problem_name}")
        dst_dir.mkdir(parents=True, exist_ok=True)
        ignore_patterns = self.get_exclude_files(config_path)
        for item in src_dir.iterdir():
            if self._is_ignored(item.name, ignore_patterns):
                continue
            shutil.move(str(item), str(dst_dir / item.name))
        if not any(x for x in src_dir.iterdir() if not self._is_ignored(x.name, ignore_patterns)):
            src_dir.rmdir()
        self._remove_empty_parents(src_dir.parent, self.file_operator.resolve_path(f"contest_stocks/{old_contest_name}"))
        self._remove_empty_parents(src_dir.parent.parent, self.file_operator.resolve_path("contest_stocks"))

    def move_from_stocks_to_current(self, contest_name, problem_name, language_name):
        """
        contest_stocks/{contest_name}/{problem_name}/配下をディレクトリごとcontest_current/{language_name}/に移動する
        移動後、空になったディレクトリは削除する
        info.json, config.jsonはcontest_current/に作成
        """
        src_dir = self.file_operator.resolve_path(f"contest_stocks/{contest_name}/{problem_name}")
        dst_dir = self.file_operator.resolve_path(f"contest_current/{language_name}")
        if not src_dir.exists():
            raise FileNotFoundError(f"{src_dir}が存在しません")
        config_path = self.get_current_config_path()
        ignore_patterns = self.get_exclude_files(config_path)
        for item in src_dir.iterdir():
            if self._is_ignored(item.name, ignore_patterns):
                continue
            if item.is_file():
                dst_file = dst_dir / item.name
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(item), str(dst_file))
            elif item.is_dir():
                shutil.move(str(item), str(dst_dir / item.name))
        info_path = self.get_current_info_path()
        manager = InfoJsonManager(info_path)
        manager.data["contest_name"] = contest_name
        manager.data["problem_name"] = problem_name
        manager.data["language_name"] = language_name
        manager.save()
        if not config_path.exists():
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump({"moveignore": []}, f, ensure_ascii=False, indent=2)
            self._generate_moveignore_readme()
        if not any(src_dir.iterdir()):
            src_dir.rmdir()
            self._remove_empty_parents(src_dir.parent, self.file_operator.resolve_path(f"contest_stocks/{contest_name}"))
            self._remove_empty_parents(src_dir.parent.parent, self.file_operator.resolve_path("contest_stocks"))

    def copy_from_template_to_current(self, contest_name, problem_name, language_name):
        """
        contest_template/{language}/ 配下のファイルを contest_current/{language}/{problem_name}/ にコピーする
        info.json, config.jsonはcontest_current/に作成
        """
        src_dir = self.file_operator.resolve_path(f"contest_template/{language_name}")
        dst_dir = self.file_operator.resolve_path(f"contest_current/{language_name}")
        if not src_dir.exists():
            raise FileNotFoundError(f"{src_dir}が存在しません")
        config_path = self.get_current_config_path()
        ignore_patterns = self.get_exclude_files(config_path)
        for item in src_dir.iterdir():
            if self._is_ignored(item.name, ignore_patterns):
                continue
            if item.is_file():
                dst_file = dst_dir / item.name
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(item), str(dst_file))
            elif item.is_dir():
                shutil.copytree(str(item), str(dst_dir / item.name), dirs_exist_ok=True)
        info_path = self.get_current_info_path()
        manager = InfoJsonManager(info_path)
        manager.data["contest_name"] = contest_name
        manager.data["problem_name"] = problem_name
        manager.data["language_name"] = language_name
        manager.save()
        if not config_path.exists():
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump({"moveignore": []}, f, ensure_ascii=False, indent=2)
            self._generate_moveignore_readme()

    def _generate_moveignore_readme(self):
        readme_path = self.file_operator.resolve_path("contest_current/README.md")
        content = (
            "# contest_current/config.json の moveignore 設定例\n"
            "\n"
            "- `moveignore` は移動時に無視するファイル名の正規表現リストです。\n"
            "- 例: `['^.*\\.log$', '^debug.*']`\n"
            "\n"
            "## 設定例\n"
            "```json\n"
            "{\n    \"moveignore\": [\n        \"^.*\\\\.log$\",\n        \"^debug.*\"\n    ]\n}\n"
            "```\n"
        )
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)

    def problem_exists_in_stocks(self, contest_name, problem_name, language_name):
        src_dir = self.file_operator.resolve_path(f"contest_stocks/{contest_name}/{problem_name}")
        return src_dir.exists() and any(src_dir.iterdir())

    def problem_exists_in_current(self, contest_name, problem_name, language_name):
        dst_dir = self.file_operator.resolve_path(f"contest_current/{language_name}")
        return dst_dir.exists() and any(dst_dir.iterdir())

    def prepare_problem_files(self, contest_name=None, problem_name=None, language_name=None):
        """
        info.jsonに contest_name, problem_name, language_name をすべて保存し、
        次回実行時の初期値として利用できるようにする。
        引数がNoneの場合はinfo.jsonの値を使う。
        """
        info_path = self.get_current_info_path()
        config_path = self.get_current_config_path()
        if info_path.exists():
            manager = InfoJsonManager(info_path)
            info = manager.data
            if contest_name is None:
                contest_name = info.get("contest_name")
            if problem_name is None:
                problem_name = info.get("problem_name")
            if language_name is None:
                language_name = info.get("language_name")
        # config.jsonにlanguage_idがなければ初期値を追加
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}
        if "language_id" not in config:
            config["language_id"] = {
                "python": "5082",
                "pypy": "5078",
                "rust": "5054"
            }
            # 親ディレクトリを作成
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        self.move_current_to_stocks(problem_name, language_name)
        if self.problem_exists_in_stocks(contest_name, problem_name, language_name):
            self.move_from_stocks_to_current(contest_name, problem_name, language_name)
        elif self.file_operator.resolve_path(f"contest_template/{language_name}").exists():
            self.copy_from_template_to_current(contest_name, problem_name, language_name)
        else:
            raise FileNotFoundError("問題ファイルがcontest_stocksにもtemplateにも存在しません")

    def move_tests_to_stocks(self, contest_name, problem_name, tests_root):
        """
        contest_current/tests配下の既存テストケースをcontest_stocksに退避する。
        指定problem_name以外のディレクトリやファイルをcontest_stocks/{contest_name}/test/{problem_name}/に移動。
        """
        import shutil
        import os
        from pathlib import Path
        tests_root = self.file_operator.resolve_path(tests_root)
        stocks_tests_root = self.file_operator.resolve_path(f"contest_stocks/{contest_name}/test")
        if not tests_root.exists():
            return
        for item in tests_root.iterdir():
            # problem_name以外のディレクトリやファイルを退避
            if item.name != problem_name:
                dst = stocks_tests_root / item.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(item), str(dst)) 