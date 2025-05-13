import json
import os
from src.path_manager.unified_path_manager import UnifiedPathManager

class ConfigJsonManager:
    def __init__(self, path=None):
        if path is None:
            upm = UnifiedPathManager()
            path = upm.config_json()
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

    def get_entry_file(self, language_name=None):
        entry = self.data.get("entry_file", {})
        if language_name is None:
            return entry
        return entry.get(language_name)

    def set_entry_file(self, language_name):
        if "entry_file" not in self.data or not isinstance(self.data["entry_file"], dict):
            self.data["entry_file"] = {}
        self.data["entry_file"][language_name] = str(self.path)
        self.save() 