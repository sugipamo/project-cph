
# 設定管理（base_utilsに依存）  
from .base_utils import basic_function

def handle_config():
    return basic_function() + "_config"
