"""
依存関係テスト用の一時的なファイル群を作成
実際の依存関係がある場合の移動計画をテストするため
"""

from pathlib import Path

def create_test_project():
    """テスト用の依存関係があるプロジェクト構造を作成"""
    
    test_src = Path("test_src")
    test_src.mkdir(exist_ok=True)
    
    # 基底ファイル（深度0）
    (test_src / "base_utils.py").write_text("""
# 基底ユーティリティ（誰にも依存しない）
def basic_function():
    return "basic"
""")
    
    # 中間ファイル（深度1）
    (test_src / "data_manager.py").write_text("""
# データ管理（base_utilsに依存）
from .base_utils import basic_function

def manage_data():
    return basic_function() + "_managed"
""")
    
    (test_src / "config_handler.py").write_text("""
# 設定管理（base_utilsに依存）  
from .base_utils import basic_function

def handle_config():
    return basic_function() + "_config"
""")
    
    # 上位ファイル（深度2）
    (test_src / "service_processor.py").write_text("""
# サービス処理（data_managerとconfig_handlerに依存）
from .data_manager import manage_data
from .config_handler import handle_config

def process_service():
    return manage_data() + "_" + handle_config()
""")
    
    # 最上位ファイル（深度3）
    (test_src / "application_controller.py").write_text("""
# アプリケーション制御（service_processorに依存）
from .service_processor import process_service

def control_application():
    return process_service() + "_controlled"
""")
    
    # __init__.pyファイル
    (test_src / "__init__.py").write_text("")
    
    print("テスト用プロジェクト構造を作成しました:")
    print("test_src/")
    print("  base_utils.py          # 深度0")
    print("  data_manager.py        # 深度1 -> base_utils")  
    print("  config_handler.py      # 深度1 -> base_utils")
    print("  service_processor.py   # 深度2 -> data_manager, config_handler")
    print("  application_controller.py # 深度3 -> service_processor")

if __name__ == "__main__":
    create_test_project()