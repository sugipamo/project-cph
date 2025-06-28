"""Provider for Docker naming conventions."""


def get_docker_image_name(contest_name: str, env_name: str, language: str) -> str:
    """Generate Docker image name following naming convention."""
    normalized_contest = contest_name.lower().replace(" ", "_")
    normalized_env = env_name.lower()
    normalized_lang = language.lower()
    return f"cph_{normalized_contest}_{normalized_env}_{normalized_lang}"


def get_docker_container_name(contest_name: str, env_name: str, language: str) -> str:
    """Generate Docker container name following naming convention."""
    return f"{get_docker_image_name(contest_name, env_name, language)}_container"


def get_docker_network_name(contest_name: str) -> str:
    """Generate Docker network name following naming convention."""
    normalized_contest = contest_name.lower().replace(" ", "_")
    return f"cph_{normalized_contest}_network"


class DockerNamingProvider:
    """Provider for Docker naming conventions."""
    
    def get_docker_image_name(self, language: str, dockerfile_content: str) -> str:
        """Generate Docker image name for a language."""
        # Extract contest and env from dockerfile content or use defaults
        contest_name = "default"
        env_name = "default"
        return get_docker_image_name(contest_name, env_name, language)
    
    def get_docker_container_name(self, language: str, dockerfile_content: str) -> str:
        """Generate Docker container name for a language."""
        # Extract contest and env from dockerfile content or use defaults
        contest_name = "default"
        env_name = "default"
        return get_docker_container_name(contest_name, env_name, language)
    
    def get_oj_image_name(self, oj_dockerfile_content: str) -> str:
        """Generate Docker image name for online judge."""
        return "cph_oj_default"
    
    def get_oj_container_name(self, oj_dockerfile_content: str) -> str:
        """Generate Docker container name for online judge."""
        return "cph_oj_default_container"