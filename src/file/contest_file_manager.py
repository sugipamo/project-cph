from src.file.file_operator import FileOperator
from src.execution_env.info_json_manager import InfoJsonManager
from src.file.config_json_manager import ConfigJsonManager
from src.file.moveignore_manager import MoveIgnoreManager
from src.path_manager.unified_path_manager import UnifiedPathManager
from src.execution_env.language_env_profile import LANGUAGE_ENVS, LanguageConfigAccessor
import time
import json

class ContestFileManager:
    def __init__(self, file_operator: FileOperator, project_root=None, container_root="/workspace"):
        self.file_operator = file_operator
        self.upm = UnifiedPathManager(project_root, container_root)

    def get_current_info_path(self):
        return self.file_operator.resolve_path(self.upm.info_json())

    def get_current_config_path(self):
        return self.file_operator.resolve_path(self.upm.config_json())

    def get_exclude_files(self):
        """
        指定言語のmoveignore（正規表現リスト）を返す
        """
        return LanguageConfigAccessor.get_moveignore(self.language_name)

    def _is_ignored(self, name, ignore_patterns):
        return MoveIgnoreManager.is_ignored_with_patterns(name, ignore_patterns)

    def _remove_empty_parents(self, path, stop_at):
        """
        path: Pathオブジェクト。空なら削除し、stop_atまで親を再帰的に辿る。
        stop_at: これ以上は削除しないディレクトリ（Pathオブジェクト）
        """
        while path != stop_at and path.exists() and path.is_dir() and not any(path.iterdir()):
            self.file_operator.rmtree(path)
            path = path.parent

    def copy_current_to_stocks(self):
        """
        contest_current/{language}/配下のファイルを、contest_stocks/{contest_name}/{problem_name}/{language_name}/にコピーする
        config.jsonのmoveignoreに含まれるファイルはコピーしない
        info.json, config.jsonはcontest_current/に残す
        """
        src_dir = self.file_operator.resolve_path(self.upm.contest_current(self.language_name))
        config_path = self.get_current_config_path()

        
        info_path = self.get_current_info_path()
        if info_path.exists():
            manager = InfoJsonManager(info_path)
            info = manager.data
            old_contest_name = info.get("contest_name")
            old_problem_name = info.get("problem_name")
        
            ignore_patterns = self.get_exclude_files()
            for language in LANGUAGE_ENVS.keys():
                src_dir = self.file_operator.resolve_path(self.upm.contest_current(language))
                if not src_dir.exists():
                    continue
                dst_dir = self.file_operator.resolve_path(self.upm.contest_stocks(old_contest_name, old_problem_name, language))
                dst_dir.mkdir(parents=True, exist_ok=True)
                for item in src_dir.iterdir():
                    if self._is_ignored(item.name, ignore_patterns):
                        continue
                    if item.is_file():
                        self.file_operator.copy(item, dst_dir / item.name)
                    elif item.is_dir():
                        self.file_operator.copytree(item, dst_dir / item.name)

    def _move_or_copy_skip_existing(self, src_dir, dst_dir, move=False):
        """
        src_dir配下をdst_dirに再帰的にコピー（move=Trueなら移動）。
        既にdst_dir側に同名ファイル・ディレクトリが存在する場合はスキップ。
        """
        if not src_dir.exists():
            return
        dst_dir.mkdir(parents=True, exist_ok=True)
        for item in src_dir.iterdir():
            dst_item = dst_dir / item.name
            if dst_item.exists():
                continue  # 既存はスキップ
            if item.is_file():
                if move:
                    self.file_operator.move(item, dst_item)
                else:
                    self.file_operator.copy(item, dst_item)
            elif item.is_dir():
                self._move_or_copy_skip_existing(item, dst_item, move=move)

    def move_current_to_stocks(self):
        """
        contest_current/{language}/配下のファイルを、info.jsonのcontest_nameとproblem_nameを参照してcontest_stocks/{contest_name}/{problem_name}/に移動する
        config.jsonのmoveignoreに含まれるファイルは移動しない
        info.json, config.jsonはcontest_current/に残す
        """
        src_dir = self.file_operator.resolve_path(self.upm.contest_current(self.language_name))
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
        dst_dir = self.file_operator.resolve_path(self.upm.contest_stocks(old_contest_name, old_problem_name))
        dst_dir.mkdir(parents=True, exist_ok=True)
        ignore_patterns = self.get_exclude_files()
        for item in src_dir.iterdir():
            if self._is_ignored(item.name, ignore_patterns):
                continue
            self.file_operator.move(item, dst_dir / item.name)
        if not any(x for x in src_dir.iterdir() if not self._is_ignored(x.name, ignore_patterns)):
            self.file_operator.rmtree(src_dir)
        self._remove_empty_parents(src_dir.parent, self.file_operator.resolve_path(self.upm.contest_stocks(old_contest_name)))
        self._remove_empty_parents(src_dir.parent.parent, self.file_operator.resolve_path("contest_stocks"))

    def move_from_stocks_to_current(self, contest_name, problem_name, language_name=None):
        """
        contest_stocks/{contest_name}/{problem_name}/{language_name} 配下を contest_current/ に移動する
        既存ファイル・ディレクトリはスキップ
        """
        if language_name is None:
            language_name = self._get_current_language()
        src_dir = self.file_operator.resolve_path(self.upm.contest_stocks(contest_name, problem_name, language_name))
        dst_dir = self.file_operator.resolve_path(self.upm.contest_current())
        if not src_dir.exists():
            raise FileNotFoundError(f"{src_dir} が存在しません")
        self._move_or_copy_skip_existing(src_dir, dst_dir, move=True)
        # 移動後、ストック側が空なら削除
        if not any(src_dir.iterdir()):
            self.file_operator.rmtree(src_dir)
        self._remove_empty_parents(src_dir.parent, self.file_operator.resolve_path(self.upm.contest_stocks(contest_name, problem_name)))
        self._remove_empty_parents(src_dir.parent.parent, self.file_operator.resolve_path(self.upm.contest_stocks(contest_name)))
        self._remove_empty_parents(src_dir.parent.parent.parent, self.file_operator.resolve_path("contest_stocks"))

    def move_from_stock_test_to_current(self):
        """
        contest_stocks/{contest_name}/{problem_name}/test 配下を contest_current/test に移動する
        既存ファイル・ディレクトリはスキップ
        """
        src_dir = self.file_operator.resolve_path(self.upm.contest_stocks(self.contest_name, self.problem_name, "test"))
        dst_dir = self.file_operator.resolve_path(self.upm.contest_current("test"))
        if not src_dir.exists():
            raise FileNotFoundError(f"{src_dir} が存在しません")
        self._move_or_copy_skip_existing(src_dir, dst_dir, move=True)
        # 移動後、ストック側が空なら削除
        if not any(src_dir.iterdir()):
            self.file_operator.rmtree(src_dir)
        self._remove_empty_parents(src_dir.parent, self.file_operator.resolve_path(self.upm.contest_stocks(self.contest_name, self.problem_name)))
        self._remove_empty_parents(src_dir.parent.parent, self.file_operator.resolve_path(self.upm.contest_stocks(self.contest_name)))
        self._remove_empty_parents(src_dir.parent.parent.parent, self.file_operator.resolve_path("contest_stocks"))

    def _get_current_language(self):
        # system_info.jsonから現在の言語を取得（InfoJsonManagerを活用）
        info_path = self.file_operator.resolve_path(self.upm.info_json())
        if info_path.exists():
            manager = InfoJsonManager(info_path)
            return manager.data.get("language_name")
        return None

    def copy_from_template_to_current(self):
        """
        contest_template/{language}/ 配下のファイルを contest_current/ にコピーする
        info.json, config.jsonはcontest_current/に作成
        """
        src_dir = self.file_operator.resolve_path(self.upm.contest_template(self.language_name))
        dst_dir = self.file_operator.resolve_path(self.upm.contest_current())
        if not src_dir.exists():
            raise FileNotFoundError(f"{src_dir}が存在しません")
        config_path = self.get_current_config_path()
        ignore_patterns = self.get_exclude_files()
        for item in src_dir.iterdir():
            if self._is_ignored(item.name, ignore_patterns):
                continue
            dst_file = dst_dir / item.name
            # 既存ファイルがあれば削除
            if dst_file.exists():
                if dst_file.is_file():
                    dst_file.unlink()
                elif dst_file.is_dir():
                    import shutil
                    shutil.rmtree(dst_file)
            if item.is_file():
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                self.file_operator.copy(item, dst_file)
            elif item.is_dir():
                self.file_operator.copytree(item, dst_dir / item.name)
        info_path = self.get_current_info_path()
        manager = InfoJsonManager(info_path)
        manager.data["contest_name"] = self.contest_name
        manager.data["problem_name"] = self.problem_name
        manager.data["language_name"] = self.language_name
        manager.save()
        if not config_path.exists():
            manager = ConfigJsonManager(str(config_path))
            manager.data["moveignore"] = []
            manager.save()
            self._generate_moveignore_readme()

    def _generate_moveignore_readme(self):
        readme_path = self.file_operator.resolve_path("contest_current/README.md")
        MoveIgnoreManager.generate_readme(str(readme_path))

    def stocks_exists(self):
        """
        contest_stocks/{contest_name}/{problem_name}/{language_name} または test ディレクトリが存在し、何かしらファイルがあるか判定（共通化）
        """
        lang_dir = self.file_operator.resolve_path(self.upm.contest_stocks(self.contest_name, self.problem_name, self.language_name))
        test_dir = self.file_operator.resolve_path(self.upm.contest_stocks(self.contest_name, self.problem_name, "test"))
        return (lang_dir.exists() and any(lang_dir.iterdir())) or (test_dir.exists() and any(test_dir.iterdir()))

    def copy_from_stocks_to_current(self, contest_name, problem_name, language_name=None):
        """
        contest_stocks/{contest_name}/{problem_name}/{language_name}→contest_current/
        contest_stocks/{contest_name}/{problem_name}/test→contest_current/test
        """
        if language_name is None:
            language_name = self._get_current_language()
        lang_src = self.file_operator.resolve_path(self.upm.contest_stocks(contest_name, problem_name, language_name))
        lang_dst = self.file_operator.resolve_path(self.upm.contest_current())
        if lang_src.exists():
            for item in lang_src.iterdir():
                dst_file = lang_dst / item.name
                if item.is_file():
                    self.file_operator.copy(item, dst_file)
                elif item.is_dir():
                    self.file_operator.copytree(item, dst_file)
        test_src = self.file_operator.resolve_path(self.upm.contest_stocks(contest_name, problem_name, "test"))
        test_dst = self.file_operator.resolve_path(self.upm.contest_current("test"))
        if test_src.exists():
            test_dst.mkdir(parents=True, exist_ok=True)
            for item in test_src.iterdir():
                if item.is_file():
                    self.file_operator.copy(item, test_dst / item.name)
                elif item.is_dir():
                    self.file_operator.copytree(item, test_dst / item.name)

    def problem_exists_in_stocks(self):
        return self.stocks_exists()

    def problem_exists_in_current(self, contest_name, problem_name, language_name=None):
        dst_dir = self.file_operator.resolve_path(self.upm.contest_current())
        return dst_dir.exists() and any(dst_dir.iterdir())

    def copy_test_to_stocks(self, contest_name, problem_name):
        """
        contest_current/test 配下を contest_stocks/{contest_name}/{problem_name}/test にコピーする
        """
        info_path = self.get_current_info_path()
        manager = InfoJsonManager(info_path)
        info = manager.data
        old_contest_name = info.get("contest_name")
        old_problem_name = info.get("problem_name")
        src_dir = self.file_operator.resolve_path(self.upm.contest_current("test"))
        dst_dir = self.file_operator.resolve_path(self.upm.contest_stocks(old_contest_name, old_problem_name, "test"))
        if not src_dir.exists():
            return
        dst_dir.mkdir(parents=True, exist_ok=True)
        for item in src_dir.iterdir():
            if item.is_file():
                self.file_operator.copy(item, dst_dir / item.name)
            elif item.is_dir():
                self.file_operator.copytree(item, dst_dir / item.name)

    def prepare_problem_files(self, contest_name=None, problem_name=None, language_name=None):
        """
        system_info.jsonに contest_name, problem_name, language_name をすべて保存し、
        次回実行時の初期値として利用できるようにする。
        引数がNoneの場合はsystem_info.jsonの値を使う。
        """

        self.copy_current_to_stocks()
        self.copy_test_to_stocks(contest_name, problem_name)
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

        manager = ConfigJsonManager(str(config_path))
        manager.ensure_language_id({lang: str(5000 + i*2) for i, lang in enumerate(LANGUAGE_ENVS.keys())})
        self.copy_from_stocks_to_current(contest_name, problem_name, language_name)
        if not self.file_operator.resolve_path(self.upm.contest_current()).exists():
            if self.file_operator.resolve_path(self.upm.contest_template(language_name)).exists():
                self.copy_from_template_to_current()
            else:
                raise FileNotFoundError(f"問題ファイルがcontest_stocksにもtemplateにも存在しません")

    def move_tests_to_stocks(self, contest_name, problem_name, tests_root):
        """
        contest_current/tests配下の既存テストケースをcontest_stocksに退避する。
        指定problem_name以外のディレクトリやファイルをcontest_stocks/{contest_name}/test/{problem_name}/に移動。
        """
        tests_root = self.file_operator.resolve_path(tests_root)
        stocks_tests_root = self.file_operator.resolve_path(self.upm.contest_stocks(contest_name, "test"))
        if not tests_root.exists():
            return
        for item in tests_root.iterdir():
            # problem_name以外のディレクトリやファイルを退避
            if item.name != problem_name:
                dst = stocks_tests_root / item.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                self.file_operator.move(item, dst)

    def get_problem_files(self, contest_name, problem_name, language_name=None):
        """
        contest_current/とcontest_current/test/のパスを返す。
        Returns:
            tuple: (問題ファイルのディレクトリパス, テストファイルのディレクトリパス)
        """
        problem_dir = self.file_operator.resolve_path(self.upm.contest_current())
        test_dir = self.file_operator.resolve_path(self.upm.contest_current("test"))
        return problem_dir, test_dir 