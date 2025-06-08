"""Tests for Docker repositories - container and image management."""
import os
import tempfile

import pytest

from src.infrastructure.persistence.sqlite.repositories.docker_container_repository import (
    DockerContainerRepository,
)
from src.infrastructure.persistence.sqlite.repositories.docker_image_repository import (
    DockerImageRepository,
)
from src.infrastructure.persistence.sqlite.sqlite_manager import SQLiteManager


class TestDockerContainerRepository:
    """Test DockerContainerRepository functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        yield temp_path
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def sqlite_manager(self, temp_db_path):
        """Create SQLiteManager with temporary database."""
        return SQLiteManager(temp_db_path)

    @pytest.fixture
    def container_repo(self, sqlite_manager):
        """Create DockerContainerRepository."""
        return DockerContainerRepository(sqlite_manager)

    @pytest.fixture
    def image_repo(self, sqlite_manager):
        """Create DockerImageRepository."""
        return DockerImageRepository(sqlite_manager)

    def test_create_container_basic(self, container_repo, image_repo):
        """Test creating a basic container."""
        # First create the image that the container references
        image_repo.create_or_update_image(
            name="python",
            tag="3.9",
            dockerfile_hash="abc123"
        )

        container_id = container_repo.create_container(
            container_name="test_container",
            image_name="python",
            image_tag="3.9",
            language="python"
        )

        assert container_id is not None
        assert isinstance(container_id, int)

    def test_create_container_with_full_config(self, container_repo, image_repo):
        """Test creating container with full configuration."""
        # Create required image first
        image_repo.create_or_update_image(
            name="cpp",
            tag="latest",
            dockerfile_hash="def456"
        )

        volumes = [{"host": "/host/path", "container": "/container/path"}]
        environment = {"ENV_VAR": "value", "DEBUG": "true"}
        ports = [{"host": 8080, "container": 80}]

        container_id = container_repo.create_container(
            container_name="full_container",
            image_name="cpp",
            image_tag="latest",
            language="cpp",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            volumes=volumes,
            environment=environment,
            ports=ports
        )

        assert container_id is not None

        # Verify stored data
        container = container_repo.find_container_by_name("full_container")
        assert container is not None
        assert container["container_name"] == "full_container"
        assert container["image_name"] == "cpp"
        assert container["image_tag"] == "latest"
        assert container["language"] == "cpp"
        assert container["contest_name"] == "abc123"
        assert container["problem_name"] == "a"
        assert container["env_type"] == "docker"
        assert container["status"] == "created"
        assert container["volumes"] == volumes
        assert container["environment"] == environment
        assert container["ports"] == ports

    def test_update_container_id(self, container_repo, image_repo):
        """Test updating container Docker ID."""
        # Create image and container
        image_repo.create_or_update_image("python", "3.9", "abc123")
        container_repo.create_container("test_container", "python", "3.9")

        # Update container ID
        container_repo.update_container_id("test_container", "docker_id_123")

        # Verify update
        container = container_repo.find_container_by_name("test_container")
        assert container["container_id"] == "docker_id_123"

    def test_update_container_status(self, container_repo, image_repo):
        """Test updating container status."""
        # Create image and container
        image_repo.create_or_update_image("python", "3.9", "abc123")
        container_repo.create_container("test_container", "python", "3.9")

        # Update status to running
        container_repo.update_container_status("test_container", "running", "started_at")

        # Verify update
        container = container_repo.find_container_by_name("test_container")
        assert container["status"] == "running"
        assert container["started_at"] is not None

    def test_find_container_by_name_existing(self, container_repo, image_repo):
        """Test finding existing container by name."""
        image_repo.create_or_update_image("python", "3.9", "abc123")
        container_repo.create_container("test_container", "python", "3.9", language="python")

        container = container_repo.find_container_by_name("test_container")
        assert container is not None
        assert container["container_name"] == "test_container"
        assert container["language"] == "python"

    def test_find_container_by_name_nonexistent(self, container_repo):
        """Test finding non-existent container."""
        container = container_repo.find_container_by_name("nonexistent")
        assert container is None

    def test_find_containers_by_status(self, container_repo, image_repo):
        """Test finding containers by status."""
        # Create image and containers with different statuses
        image_repo.create_or_update_image("python", "3.9", "abc123")

        container_repo.create_container("container1", "python", "3.9")
        container_repo.create_container("container2", "python", "3.9")
        container_repo.create_container("container3", "python", "3.9")

        # Update statuses
        container_repo.update_container_status("container1", "running")
        container_repo.update_container_status("container2", "running")
        container_repo.update_container_status("container3", "stopped")

        # Find running containers
        running_containers = container_repo.find_containers_by_status("running")
        assert len(running_containers) == 2
        assert all(c["status"] == "running" for c in running_containers)

        # Find stopped containers
        stopped_containers = container_repo.find_containers_by_status("stopped")
        assert len(stopped_containers) == 1
        assert stopped_containers[0]["status"] == "stopped"

    def test_find_containers_by_language(self, container_repo, image_repo):
        """Test finding containers by language."""
        # Create images and containers with different languages
        image_repo.create_or_update_image("python", "3.9", "abc123")
        image_repo.create_or_update_image("cpp", "latest", "def456")

        container_repo.create_container("py_container1", "python", "3.9", language="python")
        container_repo.create_container("py_container2", "python", "3.9", language="python")
        container_repo.create_container("cpp_container1", "cpp", "latest", language="cpp")

        # Find Python containers
        python_containers = container_repo.find_containers_by_language("python")
        assert len(python_containers) == 2
        assert all(c["language"] == "python" for c in python_containers)

        # Find C++ containers
        cpp_containers = container_repo.find_containers_by_language("cpp")
        assert len(cpp_containers) == 1
        assert cpp_containers[0]["language"] == "cpp"

    def test_get_active_containers(self, container_repo, image_repo):
        """Test getting active containers."""
        # Create image and containers with different statuses
        image_repo.create_or_update_image("python", "3.9", "abc123")

        container_repo.create_container("container1", "python", "3.9")  # created
        container_repo.create_container("container2", "python", "3.9")
        container_repo.create_container("container3", "python", "3.9")

        # Update statuses
        container_repo.update_container_status("container2", "running")
        container_repo.update_container_status("container3", "stopped")

        # Get active containers (created, running, started)
        active_containers = container_repo.get_active_containers()
        assert len(active_containers) == 2  # created and running, not stopped
        statuses = [c["status"] for c in active_containers]
        assert "created" in statuses
        assert "running" in statuses
        assert "stopped" not in statuses

    def test_mark_container_removed(self, container_repo, image_repo):
        """Test marking container as removed."""
        image_repo.create_or_update_image("python", "3.9", "abc123")
        container_repo.create_container("test_container", "python", "3.9")

        # Mark as removed
        container_repo.mark_container_removed("test_container")

        # Verify status and timestamp
        container = container_repo.find_container_by_name("test_container")
        assert container["status"] == "removed"
        assert container["removed_at"] is not None

    def test_find_unused_containers(self, container_repo, image_repo, sqlite_manager):
        """Test finding unused containers."""
        # Create image and containers
        image_repo.create_or_update_image("python", "3.9", "abc123")
        container_repo.create_container("recent_container", "python", "3.9")
        container_repo.create_container("old_container", "python", "3.9")

        # Manually set last_used_at to simulate old container
        with sqlite_manager.get_connection() as conn:
            conn.execute("""
                UPDATE docker_containers
                SET last_used_at = datetime('now', '-10 days')
                WHERE container_name = 'old_container'
            """)

        # Find unused containers (older than 7 days)
        unused = container_repo.find_unused_containers(days=7)
        assert len(unused) == 1
        assert unused[0]["container_name"] == "old_container"

    def test_repository_interface_methods(self, container_repo, image_repo):
        """Test RepositoryInterface implementation."""
        # Create image first
        image_repo.create_or_update_image("python", "3.9", "abc123")

        # Test create via interface
        entity = {
            "container_name": "interface_test",
            "image_name": "python",
            "image_tag": "3.9",
            "language": "python"
        }
        result = container_repo.create(entity)
        assert result is not None

        # Test find_by_id via interface (uses container name)
        found = container_repo.find_by_id("interface_test")
        assert found is not None
        assert found["container_name"] == "interface_test"

        # Test update via interface
        success = container_repo.update("interface_test", {"status": "running"})
        assert success is True

        # Test find_all via interface
        all_containers = container_repo.find_all()
        assert len(all_containers) >= 1

        # Test delete via interface
        success = container_repo.delete("interface_test")
        assert success is True

        # Verify deletion (marked as removed)
        found = container_repo.find_by_id("interface_test")
        assert found["status"] == "removed"

    def test_json_field_parsing(self, container_repo, image_repo):
        """Test proper JSON field parsing."""
        image_repo.create_or_update_image("python", "3.9", "abc123")

        # Test with valid JSON
        volumes = [{"host": "/host", "container": "/container"}]
        environment = {"VAR1": "value1", "VAR2": "value2"}

        container_repo.create_container(
            "json_test",
            "python", "3.9",
            volumes=volumes,
            environment=environment
        )

        container = container_repo.find_container_by_name("json_test")
        assert container["volumes"] == volumes
        assert container["environment"] == environment

    def test_json_field_parsing_invalid(self, container_repo, sqlite_manager):
        """Test handling of invalid JSON in fields."""
        # Manually insert invalid JSON
        with sqlite_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO docker_images (name, tag, dockerfile_hash)
                VALUES ('python', '3.9', 'abc123')
            """)
            conn.execute("""
                INSERT INTO docker_containers (container_name, image_name, image_tag, volumes)
                VALUES ('invalid_json_test', 'python', '3.9', 'invalid json {')
            """)

        container = container_repo.find_container_by_name("invalid_json_test")
        assert container["volumes"] is None  # Should be parsed as None for invalid JSON


class TestDockerImageRepository:
    """Test DockerImageRepository functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        yield temp_path
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def sqlite_manager(self, temp_db_path):
        """Create SQLiteManager with temporary database."""
        return SQLiteManager(temp_db_path)

    @pytest.fixture
    def image_repo(self, sqlite_manager):
        """Create DockerImageRepository."""
        return DockerImageRepository(sqlite_manager)

    def test_create_or_update_image_new(self, image_repo):
        """Test creating a new image."""
        result = image_repo.create_or_update_image(
            name="python",
            tag="3.9",
            dockerfile_hash="abc123",
            build_status="success"
        )

        assert result is not None

        # Verify image was created
        image = image_repo.find_image("python", "3.9")
        assert image is not None
        assert image["name"] == "python"
        assert image["tag"] == "3.9"
        assert image["dockerfile_hash"] == "abc123"
        assert image["build_status"] == "success"

    def test_create_or_update_image_update_existing(self, image_repo):
        """Test updating an existing image."""
        # Create initial image
        image_repo.create_or_update_image("python", "3.9", "abc123", "success")

        # Update with new hash
        image_repo.create_or_update_image("python", "3.9", "def456", "success")

        # Verify update
        image = image_repo.find_image("python", "3.9")
        assert image["dockerfile_hash"] == "def456"

    def test_find_image_existing(self, image_repo):
        """Test finding existing image."""
        image_repo.create_or_update_image("python", "3.9", "abc123")

        image = image_repo.find_image("python", "3.9")
        assert image is not None
        assert image["name"] == "python"
        assert image["tag"] == "3.9"

    def test_find_image_by_name_only(self, image_repo):
        """Test finding image by name only (defaults to latest tag)."""
        image_repo.create_or_update_image("python", "latest", "abc123")

        image = image_repo.find_image("python")  # Should default to latest
        assert image is not None
        assert image["name"] == "python"
        assert image["tag"] == "latest"

    def test_find_image_nonexistent(self, image_repo):
        """Test finding non-existent image."""
        image = image_repo.find_image("nonexistent", "1.0")
        assert image is None

    def test_find_images_by_name_prefix(self, image_repo):
        """Test finding all images with names starting with prefix."""
        # Create multiple versions of same image
        image_repo.create_or_update_image("python", "3.8", "hash1")
        image_repo.create_or_update_image("python", "3.9", "hash2")
        image_repo.create_or_update_image("python", "3.10", "hash3")
        image_repo.create_or_update_image("node", "16", "hash4")

        python_images = image_repo.find_images_by_name_prefix("python")
        assert len(python_images) == 3
        assert all(img["name"] == "python" for img in python_images)

        tags = [img["tag"] for img in python_images]
        assert "3.8" in tags
        assert "3.9" in tags
        assert "3.10" in tags

    def test_find_images_by_status(self, image_repo):
        """Test finding images by build status."""
        image_repo.create_or_update_image("python", "3.9", "abc123", build_status="success")
        image_repo.create_or_update_image("cpp", "latest", "def456", build_status="failed")
        image_repo.create_or_update_image("java", "11", "ghi789", build_status="success")

        success_images = image_repo.find_images_by_status("success")
        assert len(success_images) == 2
        assert all(img["build_status"] == "success" for img in success_images)

        failed_images = image_repo.find_images_by_status("failed")
        assert len(failed_images) == 1
        assert failed_images[0]["build_status"] == "failed"

    def test_update_image_build_result(self, image_repo):
        """Test updating image build results."""
        image_repo.create_or_update_image("python", "3.9", "abc123", build_status="building")

        image_repo.update_image_build_result(
            name="python",
            tag="3.9",
            image_id="docker_image_123",
            build_status="success",
            build_time_ms=15000,
            size_bytes=500000000
        )

        image = image_repo.find_image("python", "3.9")
        assert image["image_id"] == "docker_image_123"
        assert image["build_status"] == "success"
        assert image["build_time_ms"] == 15000
        assert image["size_bytes"] == 500000000

    def test_get_all_images(self, image_repo):
        """Test getting all images."""
        # Create multiple images
        image_repo.create_or_update_image("python", "3.9", "abc123")
        image_repo.create_or_update_image("cpp", "latest", "def456")
        image_repo.create_or_update_image("java", "11", "ghi789")

        all_images = image_repo.get_all_images()
        assert len(all_images) == 3

        names = [img["name"] for img in all_images]
        assert "python" in names
        assert "cpp" in names
        assert "java" in names

    def test_repository_interface_methods(self, image_repo):
        """Test RepositoryInterface implementation."""
        # Test create via interface
        entity = {
            "name": "interface_test",
            "tag": "1.0",
            "dockerfile_hash": "abc123"
        }
        result = image_repo.create(entity)
        assert result is not None

        # Test find_by_id via interface (uses image name:tag format)
        found = image_repo.find_by_id("interface_test:1.0")
        assert found is not None
        assert found["name"] == "interface_test"

        # Test update via interface
        success = image_repo.update("interface_test:1.0", {"build_status": "success"})
        assert success is True

        # Test find_all via interface
        all_images = image_repo.find_all()
        assert len(all_images) >= 1

        # Test delete via interface
        success = image_repo.delete("interface_test:1.0")
        assert success is True  # Should return True if image was deleted

    def test_find_unused_images(self, image_repo, sqlite_manager):
        """Test finding unused images."""
        image_repo.create_or_update_image("recent_image", "latest", "abc123")
        image_repo.create_or_update_image("old_image", "latest", "def456")

        # Manually set last_used_at to simulate old image
        with sqlite_manager.get_connection() as conn:
            conn.execute("""
                UPDATE docker_images
                SET last_used_at = datetime('now', '-35 days')
                WHERE name = 'old_image'
            """)

        # Find unused images (older than 30 days)
        unused = image_repo.find_unused_images(days=30)
        assert len(unused) == 1
        assert unused[0]["name"] == "old_image"

    def test_update_last_used(self, image_repo, sqlite_manager):
        """Test updating last used timestamp."""
        image_repo.create_or_update_image("python", "3.9", "abc123")

        # Manually set an old timestamp to ensure we can detect the change
        with sqlite_manager.get_connection() as conn:
            conn.execute("""
                UPDATE docker_images
                SET last_used_at = datetime('now', '-1 hour')
                WHERE name = 'python' AND tag = '3.9'
            """)

        # Get initial timestamp
        initial_image = image_repo.find_image("python", "3.9")
        initial_timestamp = initial_image["last_used_at"]

        # Update last used
        image_repo.update_last_used("python", "3.9")

        # Verify timestamp changed
        updated_image = image_repo.find_image("python", "3.9")
        assert updated_image["last_used_at"] != initial_timestamp

    def test_delete_image(self, image_repo):
        """Test deleting an image."""
        image_repo.create_or_update_image("temp_image", "1.0", "abc123")

        # Verify it exists
        assert image_repo.find_image("temp_image", "1.0") is not None

        # Delete it
        result = image_repo.delete_image("temp_image", "1.0")
        assert result is True

        # Verify it's gone
        assert image_repo.find_image("temp_image", "1.0") is None

    def test_get_image_stats(self, image_repo):
        """Test getting image statistics."""
        # Create images with different statuses and sizes
        image_repo.create_or_update_image("python", "3.9", "abc123", build_status="success")
        image_repo.update_image_build_result("python", "3.9", size_bytes=100000000)

        image_repo.create_or_update_image("cpp", "latest", "def456", build_status="failed")
        image_repo.create_or_update_image("java", "11", "ghi789", build_status="success")
        image_repo.update_image_build_result("java", "11", size_bytes=200000000)

        stats = image_repo.get_image_stats()

        assert stats["total"] == 3
        assert stats["by_status"]["success"] == 2
        assert stats["by_status"]["failed"] == 1
        assert stats["total_size_bytes"] == 300000000  # 100MB + 200MB

    def test_concurrent_image_operations(self, image_repo):
        """Test concurrent operations on same image."""
        # This tests the update behavior when image already exists
        image_repo.create_or_update_image("python", "3.9", "hash1", build_status="building")
        image_repo.create_or_update_image("python", "3.9", "hash2", build_status="success")

        # Should have one record with latest values
        image = image_repo.find_image("python", "3.9")
        assert image["dockerfile_hash"] == "hash2"
        assert image["build_status"] == "success"
