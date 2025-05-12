class LanguageConfig:
    def __init__(self, name, build_cmd=None, run_cmd=None, bin_path=None, source_file=None, copy_mode="file", exclude_patterns=None):
        self.name = name
        self.build_cmd = build_cmd  # 例: ["cargo", "build", "--release"] や None
        self.run_cmd = run_cmd      # 例: ["python3", "{source}"] など
        self.bin_path = bin_path    # Rustのみ: "target/release/rust" など
        self.source_file = source_file  # 例: "main.py" など
        self.copy_mode = copy_mode  # "file" or "dir"
        self.exclude_patterns = exclude_patterns or [] 