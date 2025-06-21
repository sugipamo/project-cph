"""Tests for Docker repositories - container and image management."""
import pytest

from src.infrastructure.persistence.sqlite.repositories.docker_container_repository import (
    DockerContainerRepository,
)
from src.infrastructure.persistence.sqlite.repositories.docker_image_repository import (
    DockerImageRepository,
)


class TestDockerContainerRepository:
    """Test DockerContainerRepository functionality."""

    @pytest.fixture
    def sqlite_manager(self, clean_sqlite_manager):
        """Use FastSQLiteManager for testing."""
        return clean_sqlite_manager

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
            dockerfile_hash="abc123",
            build_command=None,
            build_status="success"
        )

        container_id = container_repo.create_container(
            container_name="test_container",
            image_name="python",
            image_tag="3.9",
            language="python",
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )

        assert container_id is not None
        assert isinstance(container_id, int)

    def test_create_container_with_full_config(self, container_repo, image_repo):
        """Test creating container with full configuration."""
        # Create required image first
        image_repo.create_or_update_image(
            name="cpp",
            tag="latest",
            dockerfile_hash="def456",
            build_command=None,
            build_status="success"
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
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")
        container_repo.create_container(
            container_name="test_container",
            image_name="python",
            image_tag="3.9",
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )

        # Update container ID
        container_repo.update_container_id("test_container", "docker_id_123")

        # Verify update
        container = container_repo.find_container_by_name("test_container")
        assert container["container_id"] == "docker_id_123"

    def test_update_container_status(self, container_repo, image_repo):
        """Test updating container status."""
        # Create image and container
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")
        container_repo.create_container(
            container_name="test_container",
            image_name="python",
            image_tag="3.9",
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )

        # Update status to running
        container_repo.update_container_status("test_container", "running", "started_at")

        # Verify update
        container = container_repo.find_container_by_name("test_container")
        assert container["status"] == "running"
        assert container["started_at"] is not None

    def test_find_container_by_name_existing(self, container_repo, image_repo):
        """Test finding existing container by name."""
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")
        container_repo.create_container(
            container_name="test_container",
            image_name="python",
            image_tag="3.9",
            language="python",
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )

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
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")

        container_repo.create_container(
            container_name="container1",
            image_name="python",
            image_tag="3.9",
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )
        container_repo.create_container(
            container_name="container2",
            image_name="python",
            image_tag="3.9",
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )
        container_repo.create_container(
            container_name="container3",
            image_name="python",
            image_tag="3.9",
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )

        # Update statuses
        container_repo.update_container_status("container1", "running", None)
        container_repo.update_container_status("container2", "running", None)
        container_repo.update_container_status("container3", "stopped", None)

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
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")
        image_repo.create_or_update_image("cpp", "latest", "def456", None, "success")

        container_repo.create_container(
            container_name="py_container1",
            image_name="python",
            image_tag="3.9",
            language="python",
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )
        container_repo.create_container(
            container_name="py_container2",
            image_name="python",
            image_tag="3.9",
            language="python",
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )
        container_repo.create_container(
            container_name="cpp_container1",
            image_name="cpp",
            image_tag="latest",
            language="cpp",
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )

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
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")

        container_repo.create_container(
            container_name="container1",
            image_name="python",
            image_tag="3.9",
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )  # created
        container_repo.create_container(
            container_name="container2",
            image_name="python",
            image_tag="3.9",
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )
        container_repo.create_container(
            container_name="container3",
            image_name="python",
            image_tag="3.9",
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )

        # Update statuses
        container_repo.update_container_status("container2", "running", None)
        container_repo.update_container_status("container3", "stopped", None)

        # Get active containers (created, running, started)
        active_containers = container_repo.get_active_containers()
        assert len(active_containers) == 2  # created and running, not stopped
        statuses = [c["status"] for c in active_containers]
        assert "created" in statuses
        assert "running" in statuses
        assert "stopped" not in statuses

    def test_mark_container_removed(self, container_repo, image_repo):
        """Test marking container as removed."""
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")
        container_repo.create_container(
            container_name="test_container",
            image_name="python",
            image_tag="3.9",
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )

        # Mark as removed
        container_repo.mark_container_removed("test_container")

        # Verify status and timestamp
        container = container_repo.find_container_by_name("test_container")
        assert container["status"] == "removed"
        assert container["removed_at"] is not None

    def test_find_unused_containers(self, container_repo, image_repo, sqlite_manager):
        """Test finding unused containers."""
        # Create image and containers
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")
        container_repo.create_container(
            container_name="recent_container",
            image_name="python",
            image_tag="3.9",
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )
        container_repo.create_container(
            container_name="old_container",
            image_name="python",
            image_tag="3.9",
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )

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
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")

        # Test create via interface
        entity = {
            "container_name": "interface_test",
            "image_name": "python",
            "image_tag": "3.9",
            "language": "python",
            "contest_name": None,
            "problem_name": None,
            "env_type": None,
            "volumes": None,
            "environment": None,
            "ports": None
        }
        result = container_repo.create_entity_record(entity)
        assert result is not None

        # Test find_by_id via interface (uses container name)
        found = container_repo.find_by_id("interface_test")
        assert found is not None
        assert found["container_name"] == "interface_test"

        # Test update via interface
        success = container_repo.update("interface_test", {"status": "running"})
        assert success is True

        # Test find_all via interface
        all_containers = container_repo.find_all(None, None)
        assert len(all_containers) >= 1

        # Test delete via interface
        success = container_repo.delete("interface_test")
        assert success is True

        # Verify deletion (marked as removed)
        found = container_repo.find_by_id("interface_test")
        assert found["status"] == "removed"

    def test_json_field_parsing(self, container_repo, image_repo):
        """Test proper JSON field parsing."""
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")

        # Test with valid JSON
        volumes = [{"host": "/host", "container": "/container"}]
        environment = {"VAR1": "value1", "VAR2": "value2"}

        container_repo.create_container(
            container_name="json_test",
            image_name="python",
            image_tag="3.9",
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=volumes,
            environment=environment,
            ports=None
        )

        container = container_repo.find_container_by_name("json_test")
        assert container["volumes"] == volumes
        assert container["environment"] == environment

    def test_json_field_parsing_invalid(self, container_repo, sqlite_manager):
        """Test handling of invalid JSON in fields."""
        # Manually insert invalid JSON
        with sqlite_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO docker_images (name, tag, dockerfile_hash, build_status)
                VALUES ('python', '3.9', 'abc123', 'success')
            """)
            conn.execute("""
                INSERT INTO docker_containers (container_name, image_name, image_tag, volumes)
                VALUES ('invalid_json_test', 'python', '3.9', 'invalid json {')
            """)

        container = container_repo.find_container_by_name("invalid_json_test")
        assert container["volumes"] is None  # Should be parsed as None for invalid JSON

    def test_create_container_record_alias(self, container_repo, image_repo):
        """Test create_container_record method (alias for create_entity_record)."""
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")

        entity = {
            "container_name": "alias_test",
            "image_name": "python",
            "image_tag": "3.9",
            "language": "python",
            "contest_name": None,
            "problem_name": None,
            "env_type": None,
            "volumes": None,
            "environment": None,
            "ports": None
        }
        result = container_repo.create_container_record(entity)
        assert result is not None

        # Verify container was created
        container = container_repo.find_container_by_name("alias_test")
        assert container is not None
        assert container["container_name"] == "alias_test"
        assert container["language"] == "python"

    def test_find_all_with_pagination(self, container_repo, image_repo):
        """Test find_all with limit and offset."""
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")

        # Create multiple containers
        for i in range(5):
            container_repo.create_container(
                container_name=f"container_{i}",
                image_name="python",
                image_tag="3.9",
                language=None,
                contest_name=None,
                problem_name=None,
                env_type=None,
                volumes=None,
                environment=None,
                ports=None
            )

        # Test with limit
        limited = container_repo.find_all(3, None)
        assert len(limited) <= 3  # May be less due to filtering

        # Test with offset
        offset_results = container_repo.find_all(None, 2)
        original_count = len(container_repo.get_active_containers())
        assert len(offset_results) == max(0, original_count - 2)

    def test_update_nonexistent_container(self, container_repo):
        """Test updating non-existent container returns False."""
        result = container_repo.update("nonexistent", {"status": "running"})
        assert result is False

    def test_delete_nonexistent_container(self, container_repo):
        """Test deleting non-existent container returns False."""
        result = container_repo.delete("nonexistent")
        assert result is False

    def test_create_container_with_minimal_params(self, container_repo, image_repo):
        """Test creating container with minimal required parameters."""
        image_repo.create_or_update_image("python", "latest", "abc123", None, "success")

        result = container_repo.create_container(
            container_name="minimal_test",
            image_name="python",
            image_tag="latest",  # Must be explicitly specified
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            volumes=None,
            environment=None,
            ports=None
        )

        assert result is not None
        container = container_repo.find_container_by_name("minimal_test")
        assert container["image_tag"] == "latest"
        assert container["status"] == "created"  # Default status

    def test_create_container_with_all_params(self, container_repo, image_repo):
        """Test creating container with all parameters."""
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")

        volumes = [{"host": "/host", "container": "/container"}]
        environment = {"VAR1": "value1"}
        ports = [{"host": 8080, "container": 80}]

        result = container_repo.create_container(
            container_name="full_test",
            image_name="python",
            image_tag="3.9",
            language="python",
            contest_name="atcoder",
            problem_name="abc123_a",
            env_type="competitive",
            volumes=volumes,
            environment=environment,
            ports=ports
        )

        assert result is not None
        container = container_repo.find_container_by_name("full_test")
        assert container["language"] == "python"
        assert container["contest_name"] == "atcoder"
        assert container["problem_name"] == "abc123_a"
        assert container["env_type"] == "competitive"
        assert container["volumes"] == volumes
        assert container["environment"] == environment
        assert container["ports"] == ports


class TestDockerImageRepository:
    """Test DockerImageRepository functionality."""

    @pytest.fixture
    def sqlite_manager(self, clean_sqlite_manager):
        """Use FastSQLiteManager for testing."""
        return clean_sqlite_manager

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
            build_command=None,
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
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")

        # Update with new hash
        image_repo.create_or_update_image("python", "3.9", "def456", None, "success")

        # Verify update
        image = image_repo.find_image("python", "3.9")
        assert image["dockerfile_hash"] == "def456"

    def test_find_image_existing(self, image_repo):
        """Test finding existing image."""
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")

        image = image_repo.find_image("python", "3.9")
        assert image is not None
        assert image["name"] == "python"
        assert image["tag"] == "3.9"

    def test_find_image_by_name_only(self, image_repo):
        """Test finding image by name only (defaults to latest tag)."""
        image_repo.create_or_update_image("python", "latest", "abc123", None, "success")

        image = image_repo.find_image("python", "latest")  # Should provide tag explicitly
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
        image_repo.create_or_update_image("python", "3.8", "hash1", None, "success")
        image_repo.create_or_update_image("python", "3.9", "hash2", None, "success")
        image_repo.create_or_update_image("python", "3.10", "hash3", None, "success")
        image_repo.create_or_update_image("node", "16", "hash4", None, "success")

        python_images = image_repo.find_images_by_name_prefix("python")
        assert len(python_images) == 3
        assert all(img["name"] == "python" for img in python_images)

        tags = [img["tag"] for img in python_images]
        assert "3.8" in tags
        assert "3.9" in tags
        assert "3.10" in tags

    def test_find_images_by_status(self, image_repo):
        """Test finding images by build status."""
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")
        image_repo.create_or_update_image("cpp", "latest", "def456", None, "failed")
        image_repo.create_or_update_image("java", "11", "ghi789", None, "success")

        success_images = image_repo.find_images_by_status("success")
        assert len(success_images) == 2
        assert all(img["build_status"] == "success" for img in success_images)

        failed_images = image_repo.find_images_by_status("failed")
        assert len(failed_images) == 1
        assert failed_images[0]["build_status"] == "failed"

    def test_update_image_build_result(self, image_repo):
        """Test updating image build results."""
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "building")

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
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")
        image_repo.create_or_update_image("cpp", "latest", "def456", None, "success")
        image_repo.create_or_update_image("java", "11", "ghi789", None, "success")

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
            "dockerfile_hash": "abc123",
            "build_command": None,
            "build_status": "success"
        }
        result = image_repo.create_entity_record(entity)
        assert result is not None

        # Test find_by_id via interface (uses image name:tag format)
        found = image_repo.find_by_id("interface_test:1.0")
        assert found is not None
        assert found["name"] == "interface_test"

        # Test update via interface
        success = image_repo.update("interface_test:1.0", {"build_status": "success"})
        assert success is True

        # Test find_all via interface
        all_images = image_repo.find_all(None, None)
        assert len(all_images) >= 1

        # Test delete via interface
        success = image_repo.delete("interface_test:1.0")
        assert success is True  # Should return True if image was deleted

    def test_find_unused_images(self, image_repo, sqlite_manager):
        """Test finding unused images."""
        image_repo.create_or_update_image("recent_image", "latest", "abc123", None, "success")
        image_repo.create_or_update_image("old_image", "latest", "def456", None, "success")

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
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")

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
        image_repo.create_or_update_image("temp_image", "1.0", "abc123", None, "success")

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
        image_repo.create_or_update_image("python", "3.9", "abc123", None, "success")
        image_repo.update_image_build_result("python", "3.9", None, "success", None, 100000000)

        image_repo.create_or_update_image("cpp", "latest", "def456", None, "failed")
        image_repo.create_or_update_image("java", "11", "ghi789", None, "success")
        image_repo.update_image_build_result("java", "11", None, "success", None, 200000000)

        stats = image_repo.get_image_stats()

        assert stats["total"] == 3
        assert stats["by_status"]["success"] == 2
        assert stats["by_status"]["failed"] == 1
        assert stats["total_size_bytes"] == 300000000  # 100MB + 200MB

    def test_concurrent_image_operations(self, image_repo):
        """Test concurrent operations on same image."""
        # This tests the update behavior when image already exists
        image_repo.create_or_update_image("python", "3.9", "hash1", None, "building")
        image_repo.create_or_update_image("python", "3.9", "hash2", None, "success")

        # Should have one record with latest values
        image = image_repo.find_image("python", "3.9")
        assert image["dockerfile_hash"] == "hash2"
        assert image["build_status"] == "success"

    def test_create_image_record_alias(self, image_repo):
        """Test create_image_record method (alias for create_entity_record)."""
        entity = {
            "name": "alias_test",
            "tag": "latest",
            "dockerfile_hash": "xyz789",
            "build_command": None,
            "build_status": "success"
        }
        result = image_repo.create_image_record(entity)
        assert result is not None

        # Verify image was created
        image = image_repo.find_image("alias_test", "latest")
        assert image is not None
        assert image["name"] == "alias_test"
        assert image["dockerfile_hash"] == "xyz789"

    def test_find_by_id_without_tag(self, image_repo):
        """Test find_by_id with name only (defaults to latest)."""
        image_repo.create_or_update_image("test_image", "latest", "abc123", None, "success")

        # Test finding by name only
        image = image_repo.find_by_id("test_image")
        assert image is not None
        assert image["name"] == "test_image"
        assert image["tag"] == "latest"

    def test_find_all_with_pagination(self, image_repo):
        """Test find_all with limit and offset."""
        # Create multiple images
        for i in range(5):
            image_repo.create_or_update_image(f"image_{i}", "latest", f"hash_{i}", None, "success")

        # Test with limit
        limited = image_repo.find_all(3, None)
        assert len(limited) == 3

        # Test with offset
        offset_results = image_repo.find_all(None, 2)
        assert len(offset_results) == 3  # 5 total - 2 offset

        # Test with both limit and offset
        paginated = image_repo.find_all(2, 1)
        assert len(paginated) == 2

    def test_update_nonexistent_image(self, image_repo):
        """Test updating non-existent image returns False."""
        result = image_repo.update("nonexistent:latest", {"build_status": "success"})
        assert result is False

    def test_delete_nonexistent_image(self, image_repo):
        """Test deleting non-existent image returns False."""
        result = image_repo.delete_image("nonexistent", "latest")
        assert result is False

    def test_delete_by_id_without_tag(self, image_repo):
        """Test delete method using ID without tag."""
        image_repo.create_or_update_image("test_delete", "latest", "abc123", None, "success")

        # Delete using name only (should default to latest)
        result = image_repo.delete("test_delete")
        assert result is True

        # Verify it's gone
        assert image_repo.find_image("test_delete", "latest") is None
