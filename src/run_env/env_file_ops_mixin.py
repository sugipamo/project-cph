from pathlib import Path
import shutil
from src.language_env.language_config import LANGUAGE_CONFIGS
from abc import ABC, abstractmethod

# 言語ごとの準備クラス
class SourcePreparerBase(ABC):
    @abstractmethod
    def prepare(self, upm, file_operator, temp_dir, language_name):
        pass

class PythonSourcePreparer(SourcePreparerBase):
    def prepare(self, upm, file_operator, temp_dir, language_name):
        config = LANGUAGE_CONFIGS[language_name]
        source_file = getattr(config, "source_file", "main.py")
        src = upm.contest_current(language_name, source_file)
        dst_dir = temp_dir / language_name
        dst = dst_dir / source_file
        if file_operator:
            if not file_operator.exists(dst_dir):
                file_operator.makedirs(dst_dir)
            file_operator.copy(src, dst)
        else:
            dst_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
        return str(dst)

class PypySourcePreparer(PythonSourcePreparer):
    pass  # Pythonと同じ手順

class RustSourcePreparer(SourcePreparerBase):
    def prepare(self, upm, file_operator, temp_dir, language_name):
        src_dir = upm.contest_current("rust")
        dst_dir = temp_dir / "rust"
        if file_operator:
            if not file_operator.exists(dst_dir):
                file_operator.makedirs(dst_dir)
            if file_operator.exists(dst_dir):
                resolved = file_operator.resolve_path(dst_dir)
                resolved_path = Path(resolved)
                for item in resolved_path.iterdir():
                    if item.name != "target":
                        if item.is_dir():
                            file_operator.rmtree(item)
                        else:
                            item.unlink()
            else:
                file_operator.makedirs(dst_dir)
            file_operator.copytree(src_dir, dst_dir)
        else:
            dst_dir.mkdir(parents=True, exist_ok=True)
            if dst_dir.exists():
                for item in dst_dir.iterdir():
                    if item.name != "target":
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
            else:
                dst_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
        return str(dst_dir)

LANGUAGE_PREPARERS = {
    "python": PythonSourcePreparer(),
    "pypy": PypySourcePreparer(),
    "rust": RustSourcePreparer(),
}

class RunEnvFileOpsMixin:
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