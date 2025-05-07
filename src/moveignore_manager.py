import re
import json
import os
from src.path_manager.unified_path_manager import UnifiedPathManager

class MoveIgnoreManager:
    def __init__(self, config_path=None):
        if config_path is None:
            upm = UnifiedPathManager()
            config_path = upm.config_json()
        self.config_path = config_path
        self.moveignore = self._load_moveignore()

    def _load_moveignore(self):
        if not os.path.exists(self.config_path):
            return []
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("moveignore", [])

    def is_ignored(self, name):
        for pat in self.moveignore:
            if re.fullmatch(pat, name):
                return True
        return False

    @staticmethod
    def is_ignored_with_patterns(name, patterns):
        for pat in patterns:
            if re.fullmatch(pat, name):
                return True
        return False

    @staticmethod
    def generate_readme(path=None):
        if path is None:
            upm = UnifiedPathManager()
            path = upm.readme_md()
        content = (
            "# contest_current/config.json の moveignore 設定例\n"
            "\n"
            "- `moveignore` は移動時に無視するファイル名の正規表現リストです。\n"
            "- 例: `['^.*\\.log$', '^debug.*']`\n"
            "\n"
            "## 設定例\n"
            "```json\n"
            "{\n    \"moveignore\": [\n        \"^.*\\\\.log$\",\n        \"^debug.*\"\n    ]\n}\n"
            "```\n"
        )
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content) 