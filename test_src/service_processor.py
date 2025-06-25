
# サービス処理（data_managerとconfig_handlerに依存）
from .data_manager import manage_data
from .config_handler import handle_config

def process_service():
    return manage_data() + "_" + handle_config()
