
# メインアプリケーション
from .api_handler import APIHandler

def main():
    handler = APIHandler()
    result = handler.handle_request({
        "name": "Test User",
        "email": "test@example.com"
    })
    print(result)

if __name__ == "__main__":
    main()
