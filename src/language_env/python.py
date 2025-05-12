from src.execution_env.language_config import LanguageConfig

PYTHON_CONFIG = LanguageConfig(
    name="python",
    build_cmd=None,
    run_cmd=["python3", "{source}"],
    source_file="main.py",
    copy_mode="file"
) 