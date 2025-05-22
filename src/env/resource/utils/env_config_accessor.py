class EnvConfigAccessor:
    def __init__(self, config):
        self.config = config

    @property
    def source_file_name(self) -> str:
        return self.config.env_json.get("source_file_name") 