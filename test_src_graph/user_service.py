
# ユーザーサービス
from .types import UserDict
from .validators import validate_user

class UserService:
    def create_user(self, data: UserDict) -> UserDict:
        if validate_user(data):
            return data
        raise ValueError("Invalid user data")
