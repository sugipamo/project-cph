"""
Test Docker naming utilities
"""
import pytest

from src.infrastructure.drivers.docker.utils.docker_naming import (
    calculate_dockerfile_hash,
    get_docker_container_name,
    get_docker_image_name,
    get_oj_container_name,
    get_oj_image_name,
)


class TestCalculateDockerfileHash:
    """Test dockerfile hash calculation"""

    def test_calculate_hash_with_content(self):
        """Test hash calculation with actual content"""
        dockerfile_text = "FROM python:3.9\nRUN pip install requests"
        hash_result = calculate_dockerfile_hash(dockerfile_text)

        assert hash_result is not None
        assert len(hash_result) == 12
        assert hash_result.isalnum()

    def test_calculate_hash_empty_content(self):
        """Test hash calculation with empty content"""
        assert calculate_dockerfile_hash("") is None
        assert calculate_dockerfile_hash("   ") is None
        assert calculate_dockerfile_hash(None) is None

    def test_calculate_hash_consistent(self):
        """Test hash calculation is consistent"""
        dockerfile_text = "FROM python:3.9\nRUN pip install requests"
        hash1 = calculate_dockerfile_hash(dockerfile_text)
        hash2 = calculate_dockerfile_hash(dockerfile_text)

        assert hash1 == hash2

    def test_calculate_hash_different_content(self):
        """Test different content produces different hashes"""
        dockerfile1 = "FROM python:3.9\nRUN pip install requests"
        dockerfile2 = "FROM python:3.10\nRUN pip install flask"

        hash1 = calculate_dockerfile_hash(dockerfile1)
        hash2 = calculate_dockerfile_hash(dockerfile2)

        assert hash1 != hash2


class TestGetDockerImageName:
    """Test Docker image name generation"""

    def test_image_name_without_dockerfile(self):
        """Test image name generation without custom dockerfile"""
        result = get_docker_image_name("python", "")
        assert result == "python"

    def test_image_name_with_dockerfile(self):
        """Test image name generation with custom dockerfile"""
        dockerfile_text = "FROM python:3.9\nRUN pip install requests"
        result = get_docker_image_name("python", dockerfile_text)

        assert result.startswith("python_")
        assert len(result.split("_")) == 2
        assert len(result.split("_")[1]) == 12

    def test_image_name_empty_dockerfile(self):
        """Test image name generation with empty dockerfile"""
        result = get_docker_image_name("python", "")
        assert result == "python"

        result = get_docker_image_name("python", "   ")
        assert result == "python"


class TestGetDockerContainerName:
    """Test Docker container name generation (fixed naming, no hash)"""

    def test_container_name_without_dockerfile(self):
        """Test container name generation without custom dockerfile"""
        result = get_docker_container_name("python", "")
        assert result == "cph_python"

    def test_container_name_with_dockerfile(self):
        """Test container name generation with custom dockerfile (same as without)"""
        dockerfile_text = "FROM python:3.9\nRUN pip install requests"
        result = get_docker_container_name("python", dockerfile_text)

        # Container names are now fixed regardless of dockerfile content
        assert result == "cph_python"

    def test_container_name_consistency(self):
        """Test that container names are consistent regardless of dockerfile"""
        dockerfile1 = "FROM python:3.9\nRUN pip install requests"
        dockerfile2 = "FROM python:3.10\nRUN pip install flask"

        result1 = get_docker_container_name("python", dockerfile1)
        result2 = get_docker_container_name("python", dockerfile2)
        result3 = get_docker_container_name("python", None)

        assert result1 == result2 == result3 == "cph_python"


class TestGetOjImageName:
    """Test OJ image name generation"""

    def test_oj_image_name_without_dockerfile(self):
        """Test OJ image name generation without custom dockerfile"""
        result = get_oj_image_name("")
        assert result == "ojtools"

    def test_oj_image_name_with_dockerfile(self):
        """Test OJ image name generation with custom dockerfile"""
        dockerfile_text = "FROM python:3.9\nRUN pip install online-judge-tools"
        result = get_oj_image_name(dockerfile_text)

        assert result.startswith("ojtools_")
        assert len(result.split("_")) == 2
        assert len(result.split("_")[1]) == 12


class TestGetOjContainerName:
    """Test OJ container name generation (fixed naming, no hash)"""

    def test_oj_container_name_without_dockerfile(self):
        """Test OJ container name generation without custom dockerfile"""
        result = get_oj_container_name("")
        assert result == "cph_ojtools"

    def test_oj_container_name_with_dockerfile(self):
        """Test OJ container name generation with custom dockerfile (same as without)"""
        dockerfile_text = "FROM python:3.9\nRUN pip install online-judge-tools"
        result = get_oj_container_name(dockerfile_text)

        # Container names are now fixed regardless of dockerfile content
        assert result == "cph_ojtools"

    def test_oj_container_name_consistency(self):
        """Test that OJ container names are consistent regardless of dockerfile"""
        dockerfile1 = "FROM python:3.9\nRUN pip install online-judge-tools"
        dockerfile2 = "FROM ubuntu:20.04\nRUN apt-get update && apt-get install -y python3"

        result1 = get_oj_container_name(dockerfile1)
        result2 = get_oj_container_name(dockerfile2)
        result3 = get_oj_container_name(None)

        assert result1 == result2 == result3 == "cph_ojtools"


class TestIntegration:
    """Test integration scenarios"""

    def test_naming_consistency_with_dockerfile(self):
        """Test that image names have hash but container names are fixed"""
        dockerfile_text = "FROM python:3.9\nRUN pip install requests"

        image_name = get_docker_image_name("python", dockerfile_text)
        container_name = get_docker_container_name("python", dockerfile_text)

        # Image name should have hash
        assert image_name.startswith("python_")
        assert len(image_name.split("_")[1]) == 12

        # Container name should be fixed
        assert container_name == "cph_python"

    def test_naming_consistency_without_dockerfile(self):
        """Test naming without dockerfile content"""
        image_name = get_docker_image_name("python", None)
        container_name = get_docker_container_name("python", None)

        # Both should be base names
        assert image_name == "python"
        assert container_name == "cph_python"

    def test_oj_naming_consistency_with_dockerfile(self):
        """Test that OJ image names have hash but container names are fixed"""
        dockerfile_text = "FROM python:3.9\nRUN pip install online-judge-tools"

        oj_image_name = get_oj_image_name(dockerfile_text)
        oj_container_name = get_oj_container_name(dockerfile_text)

        # Image name should have hash
        assert oj_image_name.startswith("ojtools_")
        assert len(oj_image_name.split("_")[1]) == 12

        # Container name should be fixed
        assert oj_container_name == "cph_ojtools"

    def test_oj_naming_consistency_without_dockerfile(self):
        """Test OJ naming without dockerfile content"""
        oj_image_name = get_oj_image_name(None)
        oj_container_name = get_oj_container_name(None)

        # Both should be base names
        assert oj_image_name == "ojtools"
        assert oj_container_name == "cph_ojtools"
