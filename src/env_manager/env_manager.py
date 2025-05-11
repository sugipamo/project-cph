from .env_initializer import EnvInitializer
from .env_profile_manager import EnvProfileManager
from .source_preparer import SourcePreparer
from .path_manager import PathManager
from .run_test_executor import RunTestExecutor
from .ojtools_manager import OjtoolsManager
from .system_info_manager import SystemInfoManager

class EnvManager:
    def __init__(self):
        self.env_initializer = EnvInitializer()
        self.profile_manager = EnvProfileManager()
        self.source_preparer = SourcePreparer()
        self.path_manager = PathManager()
        self.test_executor = RunTestExecutor()
        self.ojtools_manager = OjtoolsManager()
        self.system_info_manager = SystemInfoManager()
    # 利用側はenv_manager.method()で各機能を呼び出す
    pass 