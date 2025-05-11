from src.language_env.profiles import get_profile

class EnvProfileManager:
    def __init__(self):
        pass

    def get_profile(self, language, env_type):
        return get_profile(language, env_type)

    # 必要に応じて他のプロファイル取得系メソッドも追加

    # 言語・環境ごとの設定・プロファイル取得
    pass 