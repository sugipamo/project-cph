CONFIG = {
    "dockerfile_path": "contest_env/pypy_7_3.Dockerfile",
    "build_cmd": None,
    "run_cmd": ["pypy3", "{source}"],
    "source_file": "main.py",
    "copy_mode": "file"
} 