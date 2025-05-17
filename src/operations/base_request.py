import inspect
import os

class BaseRequest:
    def __init__(self, name=None, debug_tag=None):
        self.name = name
        self._set_debug_info(debug_tag)

    def set_name(self, name: str):
        self.name = name
        return self

    def _set_debug_info(self, debug_tag=None):
        if os.environ.get("CPH_DEBUG_REQUEST_INFO", "1") != "1":
            self.debug_info = None
            return
        frame = inspect.stack()[2]
        self.debug_info = {
            "file": frame.filename,
            "line": frame.lineno,
            "function": frame.function,
            "debug_tag": debug_tag,
        } 