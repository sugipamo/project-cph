from contest_env.base import BaseLanguageEnv

class RustEnv(BaseLanguageEnv):
    dockerfile_path = "contest_env/rust/Dockerfile"
    build_cmd = ["cargo", "build", "--release"]
    run_cmd = ["{bin_path}"]
    bin_path = "target/release/rust"
    copy_mode = "dir"
    exclude_patterns = ["target"]
    LANGUAGE_ID = "5054"  # 例: AtCoder Rust (1.70.0) 