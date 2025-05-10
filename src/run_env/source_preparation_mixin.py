from pathlib import Path
from src.run_env.source_preparer import LANGUAGE_PREPARERS
import shutil

class SourcePreparationMixin:
    def prepare_source_code(self, contest_name, problem_name, language_name):
        temp_dir = Path(".temp")
        preparer = LANGUAGE_PREPARERS.get(language_name)
        if not preparer:
            raise NotImplementedError(f"No source preparer for language: {language_name}")
        return preparer.prepare(self.upm, self.file_operator, temp_dir, language_name)

    def prepare_test_cases(self, contest_name, problem_name):
        temp_dir = Path(".temp")
        test_dir = self.upm.contest_current("test")
        temp_test_dir = temp_dir / "test"
        if self.file_operator:
            if not self.file_operator.exists(temp_test_dir):
                self.file_operator.copytree(test_dir, temp_test_dir)
        else:
            if test_dir.exists():
                shutil.copytree(test_dir, temp_test_dir, dirs_exist_ok=True)
        return str(temp_test_dir) 