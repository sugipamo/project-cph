from typing import List, Any
from src.execution_client.container.orchestrator import ContainerOrchestrator

class OrchestrationManager:
    def __init__(self):
        self.orchestrator = None

    def prepare_environments(self, language_envs: List[Any]):
        """
        language_envs: 各言語・環境のenvインスタンスのリスト
        必要なrequirements_mapを自動生成し、orchestratorを初期化して環境を準備
        """
        requirements_map = self._generate_requirements_map(language_envs)
        # docker指定が含まれていればojtoolsも追加
        if any(getattr(env, "env_type") == "docker" for env in language_envs):
            requirements_map[("ojtools", "default")] = "contest_env/oj.Dockerfile"
        self.orchestrator = ContainerOrchestrator(requirements_map)
        requirements = self._analyze_requirements(language_envs)
        self.orchestrator.orchestrate(requirements)

    def _generate_requirements_map(self, language_envs: List[Any]) -> dict:
        """
        language_envからrequirements_map（key: (language, version), value: dockerfile_path等）を生成
        """
        requirements_map = {}
        for env in language_envs:
            key = (getattr(env, "language_name"), getattr(env, "version"))
            dockerfile_path = getattr(env, "dockerfile_path", None)
            if key[0] and dockerfile_path:
                requirements_map[key] = dockerfile_path
        return requirements_map

    def _analyze_requirements(self, language_envs: List[Any]) -> List[dict]:
        """
        language_envsから必要なコンテナ・環境情報を抽出してリスト化
        ここではtype, language, count, volumes等を例示
        """
        requirements = []
        for env in language_envs:
            req = {
                "type": getattr(env, "env_type"),
                "language": getattr(env, "language_name"),
                "version": getattr(env, "version"),
                "count": 1,  # 必要に応じて拡張
                "volumes": getattr(env, "volumes"),  # 必要なら
            }
            requirements.append(req)
        return requirements 