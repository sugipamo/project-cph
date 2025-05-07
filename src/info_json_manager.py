import json
import os
from src.path_manager.unified_path_manager import UnifiedPathManager

class InfoJsonManager:
    def __init__(self, path=None):
        if path is None:
            upm = UnifiedPathManager()
            path = upm.info_json()
        self.path = path
        self.data = self.load()

    def load(self):
        if not os.path.exists(self.path):
            return {}
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self):
        # __commentを必ず付与
        self.data["__comment"] = "通常、このファイルを編集する必要はありません"
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get_containers(self, type=None, language=None):
        containers = self.data.get("containers", [])
        if type:
            containers = [c for c in containers if c.get("type") == type]
        if language:
            containers = [c for c in containers if c.get("language") == language]
        return containers

    def update_containers(self, containers):
        self.data["containers"] = containers
        self.save()

    def validate(self):
        # 重複や不正な記載を検出（例: name重複）
        names = [c["name"] for c in self.data.get("containers", [])]
        if len(names) != len(set(names)):
            print("[WARN] info.json: コンテナ名が重複しています")
        # 他にも必要に応じてバリデーション追加 