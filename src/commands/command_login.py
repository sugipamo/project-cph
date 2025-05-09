class CommandLogin:
    def __init__(self):
        pass

    async def login(self):
        # Dockerモードでloginする場合、cookie.jarをマウントする
        requirements = [
            {"type": "ojtools", "count": 1, "volumes": {
                "/home/cphelper/.local/share/online-judge-tools/cookie.jar": "/root/.local/share/online-judge-tools/cookie.jar"
            }}
        ]
        # ここでrequirementsを使ってコンテナ起動・oj login実行処理を追加する必要あり
        raise NotImplementedError("login機能は新設計で未実装です (requirementsにcookie.jarマウント例を追加済み)") 