RUST_CONFIGS = {
    "1.70": {
        "dockerfile_path": "contest_env/rust.Dockerfile",
        "build_cmd": ["cargo", "build", "--release"],
        "run_cmd": ["{bin_path}"],
        "bin_path": "target/release/rust",
        "copy_mode": "dir",
        "exclude_patterns": ["target"]
    },
    # 他バージョンもここに追加可能
} 