import importlib
import pkgutil
import os

# --- 言語ごとのハンドラ ---
HANDLERS = {}
language_env_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../language_env')
for _, module_name, _ in pkgutil.iter_modules([language_env_dir]):
    if module_name.startswith("__"): continue
    mod = importlib.import_module(f"src.language_env.{module_name}")
    handler_dict = getattr(mod, "HANDLER", None)
    if handler_dict:
        for env_type, handler in handler_dict.items():
            HANDLERS[(module_name, env_type)] = handler

def get_handler(language, env_type):
    return HANDLERS[(language, env_type)] 