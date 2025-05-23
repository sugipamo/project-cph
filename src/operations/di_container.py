class DIContainer:
    def __init__(self):
        self._providers = {}

    def register(self, key, provider):
        """
        key: strや型など（依存の識別子）
        provider: インスタンス生成関数（例: lambda: LocalFileDriver()）
        """
        self._providers[key] = provider

    def resolve(self, key):
        provider = self._providers[key]
        if provider is None:
            raise ValueError(f"{key} is not registered")
        return provider()

# --- 使い方例 ---
# from src.operations.file.local_file_driver import LocalFileDriver
# container = DIContainer()
# container.register("file_driver", lambda: LocalFileDriver())
# driver = container.resolve("file_driver") 