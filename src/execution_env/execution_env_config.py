import os

class ExecutionEnvConfig:
    def __init__(self, type, image=None, mounts=None, env_vars=None, temp_dir=".temp", workspace_dir="./workspace", host_project_root=None):
        self.type = type  # "docker" or "local"
        self.image = image
        self.mounts = mounts or []
        self.env_vars = env_vars or {}
        self.temp_dir = temp_dir
        self.workspace_dir = workspace_dir
        self.host_project_root = host_project_root or os.path.abspath(".") 