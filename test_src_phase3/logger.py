
# ロガー
from .config import DEBUG

def log(message):
    if DEBUG:
        print(f"LOG: {message}")
