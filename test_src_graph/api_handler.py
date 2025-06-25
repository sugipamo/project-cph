
# APIハンドラー
from .user_service import UserService
from .config_service import ConfigService
from .types import UserDict, ConfigDict

class APIHandler:
    def __init__(self):
        self.user_service = UserService()
        self.config_service = ConfigService()
    
    def handle_request(self, user_data: UserDict) -> dict:
        user = self.user_service.create_user(user_data)
        config = self.config_service.get_config()
        return {"user": user, "config": config}
