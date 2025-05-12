from contest_env.base import BaseLanguageEnv

class Rust170Env(BaseLanguageEnv):
    dockerfile_path = "contest_env/rust_1_70.Dockerfile"
    build_cmd = ["cargo", "build", "--release"]
    run_cmd = ["{bin_path}"]
    bin_path = "target/release/rust"
    copy_mode = "dir"
    exclude_patterns = ["target"] 