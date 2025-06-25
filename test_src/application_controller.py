
# アプリケーション制御（service_processorに依存）
from .service_processor import process_service

def control_application():
    return process_service() + "_controlled"
