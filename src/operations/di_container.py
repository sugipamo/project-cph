from enum import Enum
import inspect

class DIKey(Enum):
    # 例: FILE_DRIVER = "file_driver"
    pass

class DIContainer:
    def __init__(self):
        self._providers = {}
        self._overrides = {}

    def register(self, key, provider):
        """
        key: Enumやstrなど（依存の識別子）
        provider: インスタンス生成関数
        """
        self._providers[key] = provider

    def resolve(self, key):
        # overrideがあればそちらを優先
        if key in self._overrides:
            provider = self._overrides[key]
        else:
            provider = self._providers[key]
        if provider is None:
            raise ValueError(f"{key} is not registered")
        # providerの引数名から自動依存解決
        sig = inspect.signature(provider)
        if len(sig.parameters) == 0:
            return provider()
        kwargs = {name: self.resolve(DIKey[name.upper()] if name.upper() in DIKey.__members__ else name)
                  for name in sig.parameters}
        return provider(**kwargs)

    def override(self, key, provider):
        """
        テスト用などで依存を差し替える
        """
        self._overrides[key] = provider

    def clear_overrides(self):
        self._overrides.clear()

# --- 使い方例 ---
# from src.operations.file.local_file_driver import LocalFileDriver
# container = DIContainer()
# container.register("file_driver", lambda: LocalFileDriver())
# driver = container.resolve("file_driver") 