class ExecutionCommandBuilder:
    def __init__(self, language_config):
        self.config = language_config

    def build_command(self, source_path):
        """
        ビルドコマンドを生成する。ビルド不要な場合はNoneを返す。
        """
        if self.config.build_cmd:
            return [c.format(source=str(source_path)) for c in self.config.build_cmd]
        return None

    def run_command(self, source_path, bin_path=None):
        """
        実行コマンドを生成する。
        bin_pathはRustなどバイナリ実行時に利用。
        """
        if hasattr(self.config, 'run_cmd') and self.config.run_cmd:
            return [
                c.format(source=str(source_path), bin_path=bin_path or str(source_path))
                for c in self.config.run_cmd
            ]
        return None 