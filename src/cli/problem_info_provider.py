import json
from typing import Dict, Any

class ApiProblemInfoProvider:
    def __init__(self, api_client):
        self.api_client = api_client
    def get_problem_info(self, problem_id: str) -> Dict[str, Any]:
        return self.api_client.get_problem_info(problem_id)

class LocalProblemInfoProvider:
    def __init__(self, base_dir: str, file_manager):
        self.base_dir = base_dir
        self.file_manager = file_manager
    def get_problem_info(self, problem_id: str) -> Dict[str, Any]:
        path = self.file_manager.join(self.base_dir, f"{problem_id}.json")
        if not self.file_manager.file_exists(path):
            return {}
        content = self.file_manager.read_file(path)
        return json.loads(content)

class DockerProblemInfoProvider:
    def __init__(self, execution_client, container_name: str, base_path: str = "/problems"):
        self.execution_client = execution_client
        self.container_name = container_name
        self.base_path = base_path
    def get_problem_info(self, problem_id: str) -> Dict[str, Any]:
        # docker execでファイルをcatして取得
        cmd = [
            "docker", "exec", self.container_name, "cat", f"{self.base_path}/{problem_id}.json"
        ]
        result = self.execution_client.run_command(cmd)
        return json.loads(result.stdout) 