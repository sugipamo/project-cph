class ExecutionEnvConfig:
    def __init__(self, type, image=None, mounts=None, env_vars=None):
        self.type = type  # "docker" or "local"
        self.image = image
        self.mounts = mounts or []
        self.env_vars = env_vars or {} 