from src.execution_env.language_config import LanguageConfig

PYPY_CONFIG = LanguageConfig(
    name="pypy",
    build_cmd=None,
    run_cmd=["pypy3", "{source}"],
    source_file="main.py",
    copy_mode="file"
) 