import pytest
from src.infrastructure.docker_naming_provider import (
    get_docker_image_name,
    get_docker_container_name,
    get_docker_network_name,
    DockerNamingProvider
)


class TestDockerNamingFunctions:
    """Tests for Docker naming convention functions"""
    
    def test_get_docker_image_name_simple(self):
        """Test generating Docker image name with simple inputs"""
        assert get_docker_image_name("contest", "env", "python") == "cph_contest_env_python"
        assert get_docker_image_name("ABC", "local", "cpp") == "cph_abc_local_cpp"
    
    def test_get_docker_image_name_with_spaces(self):
        """Test generating Docker image name with spaces in contest name"""
        assert get_docker_image_name("AtCoder Regular Contest", "env", "python") == "cph_atcoder_regular_contest_env_python"
        assert get_docker_image_name("Code Forces", "prod", "java") == "cph_code_forces_prod_java"
    
    def test_get_docker_image_name_case_normalization(self):
        """Test case normalization in Docker image names"""
        assert get_docker_image_name("CONTEST", "ENV", "PYTHON") == "cph_contest_env_python"
        assert get_docker_image_name("Contest", "Env", "Python") == "cph_contest_env_python"
    
    def test_get_docker_container_name(self):
        """Test generating Docker container name"""
        assert get_docker_container_name("contest", "env", "python") == "cph_contest_env_python_container"
        assert get_docker_container_name("ABC 123", "local", "cpp") == "cph_abc_123_local_cpp_container"
    
    def test_get_docker_network_name(self):
        """Test generating Docker network name"""
        assert get_docker_network_name("contest") == "cph_contest_network"
        assert get_docker_network_name("AtCoder Regular Contest") == "cph_atcoder_regular_contest_network"
        assert get_docker_network_name("CONTEST") == "cph_contest_network"


class TestDockerNamingProvider:
    """Tests for DockerNamingProvider class"""
    
    @pytest.fixture
    def provider(self):
        """Create a DockerNamingProvider instance"""
        return DockerNamingProvider()
    
    def test_get_docker_image_name_default(self, provider):
        """Test generating Docker image name with default values"""
        result = provider.get_docker_image_name("python", "dockerfile content")
        assert result == "cph_default_default_python"
        
        result = provider.get_docker_image_name("cpp", "some dockerfile")
        assert result == "cph_default_default_cpp"
    
    def test_get_docker_image_name_language_normalized(self, provider):
        """Test language normalization in Docker image name"""
        result = provider.get_docker_image_name("PYTHON", "dockerfile content")
        assert result == "cph_default_default_python"
        
        result = provider.get_docker_image_name("C++", "dockerfile content")
        assert result == "cph_default_default_c++"
    
    def test_get_docker_container_name_default(self, provider):
        """Test generating Docker container name with default values"""
        result = provider.get_docker_container_name("python", "dockerfile content")
        assert result == "cph_default_default_python_container"
        
        result = provider.get_docker_container_name("java", "some dockerfile")
        assert result == "cph_default_default_java_container"
    
    def test_get_oj_image_name(self, provider):
        """Test generating online judge Docker image name"""
        result = provider.get_oj_image_name("oj dockerfile content")
        assert result == "cph_oj_default"
        
        # Should always return the same name regardless of content
        result = provider.get_oj_image_name("different content")
        assert result == "cph_oj_default"
    
    def test_get_oj_container_name(self, provider):
        """Test generating online judge Docker container name"""
        result = provider.get_oj_container_name("oj dockerfile content")
        assert result == "cph_oj_default_container"
        
        # Should always return the same name regardless of content
        result = provider.get_oj_container_name("different content")
        assert result == "cph_oj_default_container"