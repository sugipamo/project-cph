from pathlib import Path
from src.language_env.profiles import get_profile
import fnmatch

class SourcePreparer:
    def __init__(self, file_operator=None, upm=None):
        self.file_operator = file_operator
        self.upm = upm

    # ソースコード・テストケースの準備
    def prepare_source_code(self, contest_name, problem_name, language_name, env_type='local'):
        profile = get_profile(language_name, env_type)
        config = profile.language_config
        temp_dir = Path(profile.env_config.temp_dir)
        # コピー元・先の決定
        if config.copy_mode == "file":
            src = self.upm.contest_current(language_name, config.source_file)
            dst_dir = temp_dir / language_name
            dst = dst_dir / config.source_file
        else:
            src = self.upm.contest_current(language_name)
            dst_dir = temp_dir / language_name
            dst = dst_dir
        exclude = config.exclude_patterns
        if self.file_operator:
            if not self.file_operator.exists(dst_dir):
                self.file_operator.makedirs(dst_dir)
            if config.copy_mode == "dir":
                self._copytree_with_exclude(src, dst, exclude)
            else:
                self.file_operator.copy(src, dst)
        else:
            dst_dir.mkdir(parents=True, exist_ok=True)
            import shutil
            if config.copy_mode == "dir":
                def ignore_patterns(_, names):
                    ignored = set()
                    for pat in exclude:
                        ignored.update(fnmatch.filter(names, pat))
                    return ignored
                shutil.copytree(src, dst, dirs_exist_ok=True, ignore=ignore_patterns)
            else:
                shutil.copy(src, dst)
        return str(dst if config.copy_mode == "file" else dst_dir)

    def _copytree_with_exclude(self, src, dst, exclude_patterns):
        # file_operator用の除外付きcopytree
        for item in Path(src).iterdir():
            if any(fnmatch.fnmatch(item.name, pat) for pat in exclude_patterns):
                continue
            if item.is_dir():
                self.file_operator.copytree(item, Path(dst) / item.name)
            else:
                self.file_operator.copy(item, Path(dst) / item.name)

    def prepare_test_cases(self, contest_name, problem_name, env_type='local'):
        profile = get_profile("testcase", env_type)
        temp_dir = Path(profile.env_config.temp_dir)
        test_dir = self.upm.contest_current("test")
        temp_test_dir = temp_dir / "test"
        if self.file_operator:
            if not self.file_operator.exists(temp_test_dir):
                self.file_operator.copytree(test_dir, temp_test_dir)
        else:
            if test_dir.exists():
                import shutil
                shutil.copytree(test_dir, temp_test_dir, dirs_exist_ok=True)
        return str(temp_test_dir) 