from contest_env.base import BaseLanguageConfig, ContainerTestHandler, LocalTestHandler, register_handler

class RustConfig(BaseLanguageConfig):
    LANGUAGE_ID = "5054"  # 例: AtCoder Rust (1.70.0)
    source_file = "src/main.rs"
    exclude_patterns = ["target"]

@register_handler
class RustContainerHandler(ContainerTestHandler, RustConfig):
    language_name = "rust"
    env_type = "docker"
    dockerfile_path = "contest_env/rust/Dockerfile"
    build_cmd = ["cargo", "build", "--release"]
    run_cmd = ["{bin_path}"]
    bin_path = "target/release/rust"
    copy_mode = "dir"
    exclude_patterns = ["target"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

@register_handler
class RustLocalHandler(LocalTestHandler, RustConfig):
    language_name = "rust"
    env_type = "local"
    dockerfile_path = None
    build_cmd = ["cargo", "build", "--release"]
    run_cmd = ["{bin_path}"]
    bin_path = "target/release/rust"
    copy_mode = "dir"
    exclude_patterns = ["target"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) 