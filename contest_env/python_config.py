PYTHON_CONFIGS = {
    "3.8": {
        "dockerfile_path": "contest_env/python.Dockerfile",
        "build_cmd": None,
        "run_cmd": ["python3", "{source}"],
        "source_file": "main.py",
        "copy_mode": "file"
    },
    # 他バージョンもここに追加可能
} 