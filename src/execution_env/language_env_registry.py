import importlib
import pkgutil
import inspect

BASE_DIR = "contest_env"

def _discover_handler_classes():
    handler_classes = []
    for finder, name, ispkg in pkgutil.iter_modules([BASE_DIR]):
        env_module_path = f"{BASE_DIR}.{name}.env"
        try:
            env_module = importlib.import_module(env_module_path)
            for attr in dir(env_module):
                obj = getattr(env_module, attr)
                if inspect.isclass(obj) and hasattr(obj, "language_name") and hasattr(obj, "env_type"):
                    handler_classes.append(obj)
        except Exception as e:
            print(f"[WARN] {env_module_path} import failed: {e}")
    return handler_classes

def list_languages():
    handler_classes = _discover_handler_classes()
    return sorted(set(cls.language_name for cls in handler_classes))

def list_language_envs():
    handler_classes = _discover_handler_classes()
    return sorted(set((cls.language_name, cls.env_type) for cls in handler_classes))

def get_test_handler(language: str, env: str, **kwargs):
    handler_classes = _discover_handler_classes()
    for cls in handler_classes:
        if cls.language_name == language and cls.env_type == env:
            return cls(**kwargs)
    raise ValueError(f"Handler not found for language={language}, env={env}")

class EnvController:
    def __init__(self, language_name, env_type, config=None):
        self.language_name = language_name
        self.env_type = env_type
        # handler取得
        self.handler = get_test_handler(language=language_name, env=env_type, config=config)
        # execution_envインスタンス取得（handlerが持っている想定）
        self.execution_env = getattr(self.handler, "execution_env", None)
        if self.execution_env is None:
            raise ValueError("Handler does not have execution_env")
        # execution_client_classを取得してインスタンス化
        client_class = getattr(self.execution_env.__class__, "execution_client_class", None)
        if client_class is None:
            raise ValueError("execution_env does not have execution_client_class")
        self.exec_client = client_class()

    def build(self, *args, **kwargs):
        # handlerにbuildがあれば優先して呼ぶ
        if hasattr(self.handler, "build"):
            return self.handler.build(exec_client=self.exec_client, *args, **kwargs)
        else:
            return self.exec_client.build(*args, **kwargs)

    def run(self, *args, **kwargs):
        # handlerにrunがあれば優先して呼ぶ
        if hasattr(self.handler, "run"):
            return self.handler.run(exec_client=self.exec_client, *args, **kwargs)
        else:
            return self.exec_client.run(*args, **kwargs)