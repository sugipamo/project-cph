
# 設定サービス
from .types import ConfigDict
from .constants import DEBUG
from .formatters import format_version

class ConfigService:
    def get_config(self) -> ConfigDict:
        return {
            "debug": DEBUG,
            "version": format_version("API ")
        }
