import inspect
import os

class RequestDebugInfoMixin:
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