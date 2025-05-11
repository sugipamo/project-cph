from src.file.info_json_manager import InfoJsonManager

class SystemInfoManager:
    def __init__(self, info_path):
        self.info_path = info_path
        self.manager = InfoJsonManager(info_path)

    def load_info(self):
        return self.manager.data

    def save_info(self, data):
        self.manager.data = data
        self.manager.save()

    def get_containers(self, type=None):
        return self.manager.get_containers(type=type)

    def set_containers(self, containers):
        self.manager.data["containers"] = containers
        self.manager.save() 