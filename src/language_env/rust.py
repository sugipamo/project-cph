from src.execution_env.language_config import LanguageConfig

RUST_CONFIG = LanguageConfig(
    name="rust",
    build_cmd=["cargo", "build", "--release"],
    run_cmd=["{bin_path}"],
    bin_path="target/release/rust",
    copy_mode="dir",
    exclude_patterns=["target"]
) 