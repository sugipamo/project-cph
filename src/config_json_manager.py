import json
import os

class ConfigJsonManager:
    def __init__(self, path="contest_current/config.json"):
        self.path = path
        self.data = self.load()

    def load(self):
        if not os.path.exists(self.path):
            return {}
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get_moveignore(self):
        return self.data.get("moveignore", [])

    def get_language_id(self):
        return self.data.get("language_id", {})

    def set_language_id(self, lang_id_dict):
        self.data["language_id"] = lang_id_dict
        self.save()

    def ensure_language_id(self, default_dict):
        if "language_id" not in self.data:
            self.data["language_id"] = default_dict
            self.save()

    def validate(self):
        # 必要に応じてバリデーションを追加
        pass 