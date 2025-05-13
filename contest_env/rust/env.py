from contest_env.base import BaseLanguageConfig, ContainerTestHandler, LocalTestHandler, register_handler

class RustConfig(BaseLanguageConfig):
    LANGUAGE_ID = "5054"  # 例: AtCoder Rust (1.70.0)
    source_file = "src/main.rs"
    exclude_patterns = ["target"]

@register_handler("rust", "container")
class RustContainerHandler(ContainerTestHandler, RustConfig):
    dockerfile_path = "contest_env/rust/Dockerfile"
    build_cmd = ["cargo", "build", "--release"]
    run_cmd = ["{bin_path}"]
    bin_path = "target/release/rust"
    copy_mode = "dir"
    exclude_patterns = ["target"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

@register_handler("rust", "local")
class RustLocalHandler(LocalTestHandler, RustConfig):
    dockerfile_path = None
    build_cmd = ["cargo", "build", "--release"]
    run_cmd = ["{bin_path}"]
    bin_path = "target/release/rust"
    copy_mode = "dir"
    exclude_patterns = ["target"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) 