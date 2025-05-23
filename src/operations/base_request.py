import inspect
import os
from src.operations.constants.operation_type import OperationType
from abc import ABC, abstractmethod

class BaseRequest(ABC):
    def __init__(self, name=None, debug_tag=None):
        self.name = name
        self._set_debug_info(debug_tag)
        self._executed = False
        self._result = None

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

    @property
    @abstractmethod
    def operation_type(self):
        pass

    def execute(self, driver=None):
        if self._executed:
            raise RuntimeError(f"This {self.__class__.__name__} has already been executed.")
        # driver必須かどうかはサブクラスで制御
        if getattr(self, '_require_driver', True) and driver is None:
            raise ValueError(f"{self.__class__.__name__}.execute()にはdriverが必須です")
        self._result = self._execute_core(driver)
        self._executed = True
        return self._result

    @abstractmethod
    def _execute_core(self, driver):
        pass 