class EnvConfigAccessor:
    def __init__(self, config):
        self.config = config

    @property
    def source_file_name(self) -> str:
        lang = self.config.language
        lang_conf = self.config.env_json[lang]
        if lang_conf["source_file_name"] is None:
            raise ValueError("source_file_nameがNoneです。必ず有効なパスを指定してください。")
        return lang_conf["source_file_name"] 