PYPY_CONFIGS = {
    "7.3": {
        "dockerfile_path": "contest_env/pypy.Dockerfile",
        "build_cmd": None,
        "run_cmd": ["pypy3", "{source}"],
        "source_file": "main.py",
        "copy_mode": "file"
    },
    # 他バージョンもここに追加可能
} 