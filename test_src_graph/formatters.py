
# フォーマッター
from .constants import API_VERSION

def format_version(prefix: str = "") -> str:
    return f"{prefix}v{API_VERSION}"
