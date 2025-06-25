
# バリデーター
from .types import UserDict

def validate_user(user: UserDict) -> bool:
    return "name" in user and "email" in user
