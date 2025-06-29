"""Docker-specific path operations.
Extracted from path_operations.py for better modularity.
"""


class DockerPathOperations:
    """Docker特化のパス操作クラス"""

    @staticmethod
    def should_build_custom_docker_image(image_name: str) -> bool:
        """Determine if a Docker image should be built locally or pulled from registry

        Args:
            image_name: Name of the Docker image

        Returns:
            True if image should be built locally, False if it should be pulled
        """
        # Custom CPH images that need to be built
        custom_image_prefixes = ['ojtools', 'cph_']

        for prefix in custom_image_prefixes:
            if image_name.startswith(prefix):
                return True

        # Check if it's a registry image (e.g., docker.io/library/python)
        # Registry images typically have format: registry/namespace/image:tag
        if '/' in image_name:
            parts = image_name.split('/')
            # Common registries
            registries = ['docker.io', 'gcr.io', 'registry.hub.docker.com', 'quay.io', 'ghcr.io']
            if parts[0] in registries or '.' in parts[0]:
                # Looks like a registry URL
                return False

        # Standard images without registry prefix (e.g., python:3.9, ubuntu)
        # These can be pulled from Docker Hub
        if ':' in image_name and '/' not in image_name:
            return False

        # Simple image names without tag (e.g., python, ubuntu, alpine)
        return '/' in image_name or '@' in image_name

    @staticmethod
    def convert_path_to_docker_mount(host_path: str,
                                   workspace_path: str,
                                   mount_path: str) -> str:
        """ホストパスをDockerコンテナマウントパスに変換

        Args:
            path: 元のパス（workspace参照を含む可能性）
            workspace_path: ホストのワークスペースパス
            mount_path: Dockerマウントパス

        Returns:
            Dockerコンテナ内で使用するパス
        """
        # パスがワークスペースパスそのものか./workspaceの場合、マウントパスを返す
        if host_path == "./workspace" or host_path == workspace_path:
            return mount_path

        # パスにワークスペースパスが含まれている場合、置換する
        if workspace_path in host_path:
            return host_path.replace(workspace_path, mount_path)

        return host_path

    @staticmethod
    def get_docker_mount_path_from_config(env_json: dict,
                                        language: str,
                                        default_mount_path: str) -> str:
        """設定からDockerマウントパスを取得

        Args:
            env_json: 環境設定JSON
            language: プログラミング言語
            default_mount_path: デフォルトマウントパス

        Returns:
            マウントパス
        """
        if not env_json:
            return default_mount_path

        # 言語固有の設定を確認
        if language in env_json:
            lang_config = env_json[language]
            if isinstance(lang_config, dict) and "mount_path" in lang_config:
                return lang_config["mount_path"]

        # グローバル設定を確認
        if "mount_path" in env_json:
            return env_json["mount_path"]

        return default_mount_path
