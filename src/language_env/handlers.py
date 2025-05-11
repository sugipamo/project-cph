from .profiles import get_profile

class GenericTestHandler:
    def __init__(self, language, env_type):
        self.profile = get_profile(language, env_type)
        self.config = self.profile.language_config

    def build_command(self, temp_source_path):
        if self.config.build_cmd:
            cmd = [c.format(source=str(temp_source_path)) for c in self.config.build_cmd]
            return cmd
        else:
            return None

    def get_bin_path(self, temp_source_path):
        if self.config.name == "rust":
            import os
            return os.path.join(temp_source_path, "target/release/rust")
        elif self.config.name in ("python", "pypy"):
            return temp_source_path
        elif self.config.bin_path:
            import os
            return os.path.join(temp_source_path, self.config.bin_path)
        else:
            return temp_source_path

    def run_command(self, temp_source_path):
        bin_path = self.get_bin_path(temp_source_path)
        cmd = [c.format(source=str(temp_source_path), bin_path=bin_path) for c in self.config.run_cmd]
        return cmd

# 言語・環境ごとのhandlerを一元管理
HANDLERS = {
    ("python", "local"): GenericTestHandler("python", "local"),
    ("python", "docker"): GenericTestHandler("python", "docker"),
    ("pypy", "local"): GenericTestHandler("pypy", "local"),
    ("rust", "local"): GenericTestHandler("rust", "local"),
    ("rust", "docker"): GenericTestHandler("rust", "docker"),
}

def get_handler(language, env_type):
    return HANDLERS[(language, env_type)] 