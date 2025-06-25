
# 設定管理（constantsに依存）
from .constants import MAX_RETRIES

class Config:
    def __init__(self):
        self.retries = MAX_RETRIES
    
    def get_retry_count(self):
        return self.retries
