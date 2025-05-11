from abc import ABC, abstractmethod

class ExecutionResourceManager(ABC):
    @abstractmethod
    def adjust_resources(self, requirements, contest_name=None, problem_name=None, language_name=None):
        pass

    @abstractmethod
    def get_test_containers(self):
        pass

    @abstractmethod
    def get_ojtools_container(self):
        pass

    @abstractmethod
    def update_info(self, **kwargs):
        pass

class LocalResourceManager(ExecutionResourceManager):
    def adjust_resources(self, requirements, contest_name=None, problem_name=None, language_name=None):
        return []
    def get_test_containers(self):
        return ["local_test"]
    def get_ojtools_container(self):
        return None
    def update_info(self, **kwargs):
        pass

class DockerResourceManager(ExecutionResourceManager):
    def __init__(self, upm):
        from src.file.info_json_manager import InfoJsonManager
        self.upm = upm
        self.info_manager = InfoJsonManager(self.upm.info_json())
    def adjust_resources(self, requirements, contest_name=None, problem_name=None, language_name=None):
        # TODO: ContainerPool等で必要なコンテナを調整
        containers = []  # 実際はContainerPool等で調整
        self.info_manager.data["contest_name"] = contest_name
        self.info_manager.data["problem_name"] = problem_name
        self.info_manager.data["language_name"] = language_name
        self.info_manager.data["containers"] = containers
        self.info_manager.save()
        return containers
    def get_test_containers(self):
        return [c["name"] for c in self.info_manager.get_containers(type="test")]
    def get_ojtools_container(self):
        lst = self.info_manager.get_containers(type="ojtools")
        return lst[0]["name"] if lst else None
    def update_info(self, **kwargs):
        self.info_manager.data.update(kwargs)
        self.info_manager.save()

class CloudResourceManager(ExecutionResourceManager):
    def adjust_resources(self, requirements, contest_name=None, problem_name=None, language_name=None):
        pass
    def get_test_containers(self):
        pass
    def get_ojtools_container(self):
        pass
    def update_info(self, **kwargs):
        pass 