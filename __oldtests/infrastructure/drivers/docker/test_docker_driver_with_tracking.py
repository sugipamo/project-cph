"""Tests for LocalDockerDriverWithTracking"""
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.infrastructure.di_container import DIKey
from src.infrastructure.drivers.docker.docker_driver_with_tracking import LocalDockerDriverWithTracking
from src.operations.results.docker_result import DockerResult


class TestLocalDockerDriverWithTracking:
    """Test suite for LocalDockerDriverWithTracking"""

    @pytest.fixture
    def mock_file_driver(self):
        """Create mock file driver"""
        return Mock()

    @pytest.fixture
    def mock_container(self):
        """Create mock DI container"""
        container = Mock()
        container.resolve = Mock(side_effect=self._mock_resolve)
        self.mock_container_repo = Mock()
        self.mock_image_repo = Mock()
        return container

    def _mock_resolve(self, key):
        """Mock resolve method for DI container"""
        if key == DIKey.DOCKER_CONTAINER_REPOSITORY:
            return self.mock_container_repo
        if key == DIKey.DOCKER_IMAGE_REPOSITORY:
            return self.mock_image_repo
        return None

    @pytest.fixture
    def driver(self, mock_file_driver, mock_container):
        """Create driver instance with mocked dependencies"""
        return LocalDockerDriverWithTracking(mock_file_driver, mock_container)

    def test_init(self, mock_file_driver, mock_container):
        """Test driver initialization"""
        driver = LocalDockerDriverWithTracking(mock_file_driver, mock_container)
        assert driver.di_container == mock_container
        assert driver._container_repo is None
        assert driver._image_repo is None

    def test_container_repo_lazy_load(self, driver, mock_container):
        """Test lazy loading of container repository"""
        # First access should resolve from container
        repo = driver.container_repo
        assert repo == self.mock_container_repo
        mock_container.resolve.assert_called_with(DIKey.DOCKER_CONTAINER_REPOSITORY)

        # Second access should use cached value
        mock_container.resolve.reset_mock()
        repo2 = driver.container_repo
        assert repo2 == self.mock_container_repo
        mock_container.resolve.assert_not_called()

    def test_image_repo_lazy_load(self, driver, mock_container):
        """Test lazy loading of image repository"""
        # First access should resolve from container
        repo = driver.image_repo
        assert repo == self.mock_image_repo
        mock_container.resolve.assert_called_with(DIKey.DOCKER_IMAGE_REPOSITORY)

        # Second access should use cached value
        mock_container.resolve.reset_mock()
        repo2 = driver.image_repo
        assert repo2 == self.mock_image_repo
        mock_container.resolve.assert_not_called()

    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.LocalDockerDriver.run_container')
    def test_run_container_success_with_name(self, mock_super_run, driver):
        """Test successful container run with tracking"""
        # Setup
        mock_result = DockerResult(
            # command="docker run",
            stdout="abc123def456abc123def456abc123def456abc123def456abc123def456abc1",
            stderr="",
            returncode=0,
            container_id="container_123",
            image="test_image"
        )
        mock_super_run.return_value = mock_result

        # Execute
        result = driver.run_container("test_image", "test_container", {"ports": "8080:80"}, show_output=True)

        # Verify
        assert result == mock_result
        mock_super_run.assert_called_once_with("test_image", "test_container", {"ports": "8080:80"}, True)

        # Verify tracking calls
        driver.container_repo.update_container_status.assert_called_once_with("test_container", "running", "started_at")
        driver.container_repo.add_lifecycle_event.assert_called_once_with(
            "test_container",
            "started",
            {"image": "test_image", "options": {"ports": "8080:80"}}
        )
        driver.container_repo.update_container_id.assert_called_once_with(
            "test_container",
            "abc123def456abc123def456abc123def456abc123def456abc123def456abc1"
        )

    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.LocalDockerDriver.run_container')
    def test_run_container_success_without_name(self, mock_super_run, driver):
        """Test successful container run without name (no tracking)"""
        # Setup
        mock_result = DockerResult(
            # command="docker run",
            stdout="container_id_123",
            stderr="",
            returncode=0,
            container_id="container_123",
            image="test_image"
        )
        mock_super_run.return_value = mock_result

        # Execute
        result = driver.run_container("test_image", None, {}, show_output=False)

        # Verify
        assert result == mock_result
        mock_super_run.assert_called_once_with("test_image", None, {}, False)

        # Verify no tracking calls
        driver.container_repo.update_container_status.assert_not_called()
        driver.container_repo.add_lifecycle_event.assert_not_called()
        driver.container_repo.update_container_id.assert_not_called()

    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.LocalDockerDriver.run_container')
    def test_run_container_failure(self, mock_super_run, driver):
        """Test failed container run (no tracking)"""
        # Setup
        mock_result = DockerResult(
            # command="docker run",
            stdout="",
            stderr="Error: image not found",
            returncode=1,
            container_id=None,
            image="test_image"
        )
        mock_super_run.return_value = mock_result

        # Execute
        result = driver.run_container("test_image", "test_container", {}, show_output=True)

        # Verify
        assert result == mock_result

        # Verify no tracking calls
        driver.container_repo.update_container_status.assert_not_called()
        driver.container_repo.add_lifecycle_event.assert_not_called()

    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.LocalDockerDriver.run_container')
    def test_run_container_tracking_exception(self, mock_super_run, driver):
        """Test container run with tracking exception (should not fail operation)"""
        # Setup
        mock_result = DockerResult(
            # command="docker run",
            stdout="container_id",
            stderr="",
            returncode=0,
            container_id="container_123",
            image="test_image"
        )
        mock_super_run.return_value = mock_result
        driver.container_repo.update_container_status.side_effect = Exception("DB Error")

        # Execute
        result = driver.run_container("test_image", "test_container", {}, show_output=True)

        # Verify operation still succeeds
        assert result == mock_result

    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.LocalDockerDriver.stop_container')
    def test_stop_container_success(self, mock_super_stop, driver):
        """Test successful container stop with tracking"""
        # Setup
        mock_result = DockerResult(
            # command="docker stop",
            stdout="test_container",
            stderr="",
            returncode=0,
            container_id="container_123",
            image=None
        )
        mock_super_stop.return_value = mock_result

        # Execute
        result = driver.stop_container("test_container", show_output=True)

        # Verify
        assert result == mock_result
        mock_super_stop.assert_called_once_with("test_container", True)

        # Verify tracking calls
        driver.container_repo.update_container_status.assert_called_once_with("test_container", "stopped", "stopped_at")
        driver.container_repo.add_lifecycle_event.assert_called_once_with("test_container", "stopped", None)

    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.LocalDockerDriver.stop_container')
    def test_stop_container_failure(self, mock_super_stop, driver):
        """Test failed container stop (no tracking)"""
        # Setup
        mock_result = DockerResult(
            # command="docker stop",
            stdout="",
            stderr="Error: No such container",
            returncode=1,
            container_id=None,
            image=None
        )
        mock_super_stop.return_value = mock_result

        # Execute
        result = driver.stop_container("test_container", show_output=False)

        # Verify
        assert result == mock_result

        # Verify no tracking calls
        driver.container_repo.update_container_status.assert_not_called()
        driver.container_repo.add_lifecycle_event.assert_not_called()

    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.LocalDockerDriver.remove_container')
    def test_remove_container_success(self, mock_super_remove, driver):
        """Test successful container removal with tracking"""
        # Setup
        mock_result = DockerResult(
            # command="docker rm",
            stdout="test_container",
            stderr="",
            returncode=0,
            container_id="container_123",
            image=None
        )
        mock_super_remove.return_value = mock_result

        # Execute
        result = driver.remove_container("test_container", force=True, show_output=True)

        # Verify
        assert result == mock_result
        mock_super_remove.assert_called_once_with("test_container", True, True)

        # Verify tracking calls
        driver.container_repo.mark_container_removed.assert_called_once_with("test_container")
        driver.container_repo.add_lifecycle_event.assert_called_once_with(
            "test_container",
            "removed",
            {"force": True}
        )

    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.LocalDockerDriver.remove_container')
    def test_remove_container_without_force(self, mock_super_remove, driver):
        """Test container removal without force"""
        # Setup
        mock_result = DockerResult(
            # command="docker rm",
            stdout="test_container",
            stderr="",
            returncode=0,
            container_id="container_123",
            image=None
        )
        mock_super_remove.return_value = mock_result

        # Execute
        driver.remove_container("test_container", force=False, show_output=False)

        # Verify tracking includes force=False
        driver.container_repo.add_lifecycle_event.assert_called_once_with(
            "test_container",
            "removed",
            {"force": False}
        )

    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.LocalDockerDriver.build_docker_image')
    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.time.time')
    def test_build_docker_image_success(self, mock_time, mock_super_build, driver):
        """Test successful image build with tracking"""
        # Setup
        mock_time.side_effect = [1000.0, 1002.5]  # 2.5 seconds build time
        mock_result = DockerResult(
            # command="docker build",
            stdout="Step 1/3 : FROM alpine\nStep 2/3 : RUN echo hello\nSuccessfully built abc123def456",
            stderr="",
            returncode=0,
            container_id=None,
            image="test_image:latest"
        )
        mock_super_build.return_value = mock_result

        # Execute
        result = driver.build_docker_image("FROM alpine\nRUN echo hello", "test_image", {}, show_output=True)

        # Verify
        assert result == mock_result
        mock_super_build.assert_called_once_with("FROM alpine\nRUN echo hello", "test_image", {}, True)

        # Verify tracking calls
        driver.image_repo.create_or_update_image.assert_called_once()
        call_args = driver.image_repo.create_or_update_image.call_args[1]
        assert call_args["name"] == "test_image"
        assert call_args["tag"] == "latest"
        assert call_args["build_status"] == "building"
        assert call_args["build_command"] == "docker build -t test_image"
        assert len(call_args["dockerfile_hash"]) == 12  # SHA256 truncated to 12 chars

        driver.image_repo.update_image_build_result.assert_called_once_with(
            name="test_image",
            tag="latest",
            image_id="abc123def456",
            build_status="success",
            build_time_ms=2500,
            size_bytes=None
        )

    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.LocalDockerDriver.build_docker_image')
    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.time.time')
    def test_build_docker_image_failure(self, mock_time, mock_super_build, driver):
        """Test failed image build with tracking"""
        # Setup
        mock_time.side_effect = [1000.0, 1001.0]  # 1 second build time
        mock_result = DockerResult(
            # command="docker build",
            stdout="",
            stderr="Error: Invalid Dockerfile",
            returncode=1,
            container_id=None,
            image=None
        )
        mock_super_build.return_value = mock_result

        # Execute
        result = driver.build_docker_image("INVALID", "test_image", {}, show_output=False)

        # Verify
        assert result == mock_result

        # Verify failure tracking
        driver.image_repo.update_image_build_result.assert_called_once_with(
            name="test_image",
            tag="latest",
            image_id=None,
            build_status="failed",
            build_time_ms=1000,
            size_bytes=None
        )

    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.LocalDockerDriver.build_docker_image')
    def test_build_docker_image_without_tag(self, mock_super_build, driver):
        """Test image build without tag (no tracking)"""
        # Setup
        mock_result = DockerResult(
            # command="docker build",
            stdout="Successfully built abc123",
            stderr="",
            returncode=0,
            container_id=None,
            image=None
        )
        mock_super_build.return_value = mock_result

        # Execute
        driver.build_docker_image("FROM alpine", None, {}, show_output=True)

        # Verify no tracking calls
        driver.image_repo.create_or_update_image.assert_not_called()
        driver.image_repo.update_image_build_result.assert_not_called()

    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.LocalDockerDriver.image_rm')
    def test_image_rm_success_with_tag(self, mock_super_rm, driver):
        """Test successful image removal with tag"""
        # Setup
        mock_result = DockerResult(
            # command="docker rmi",
            stdout="Untagged: test_image:v1.0\nDeleted: sha256:abc123",
            stderr="",
            returncode=0,
            container_id=None,
            image=None
        )
        mock_super_rm.return_value = mock_result

        # Execute
        result = driver.image_rm("test_image:v1.0", show_output=True)

        # Verify
        assert result == mock_result
        mock_super_rm.assert_called_once_with("test_image:v1.0", True)

        # Verify tracking
        driver.image_repo.delete_image.assert_called_once_with("test_image", "v1.0")

    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.LocalDockerDriver.image_rm')
    def test_image_rm_success_without_tag(self, mock_super_rm, driver):
        """Test successful image removal without tag (defaults to latest)"""
        # Setup
        mock_result = DockerResult(
            # command="docker rmi",
            stdout="Untagged: test_image:latest\nDeleted: sha256:abc123",
            stderr="",
            returncode=0,
            container_id=None,
            image=None
        )
        mock_super_rm.return_value = mock_result

        # Execute
        driver.image_rm("test_image", show_output=False)

        # Verify
        driver.image_repo.delete_image.assert_called_once_with("test_image", "latest")

    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.LocalDockerDriver.image_rm')
    def test_image_rm_failure(self, mock_super_rm, driver):
        """Test failed image removal (no tracking)"""
        # Setup
        mock_result = DockerResult(
            # command="docker rmi",
            stdout="",
            stderr="Error: No such image",
            returncode=1,
            container_id=None,
            image=None
        )
        mock_super_rm.return_value = mock_result

        # Execute
        driver.image_rm("test_image", show_output=True)

        # Verify no tracking
        driver.image_repo.delete_image.assert_not_called()

    @patch('src.infrastructure.drivers.docker.docker_driver_with_tracking.LocalDockerDriver.image_rm')
    def test_image_rm_tracking_exception(self, mock_super_rm, driver):
        """Test image removal with tracking exception (should not fail operation)"""
        # Setup
        mock_result = DockerResult(
            # command="docker rmi",
            stdout="Deleted",
            stderr="",
            returncode=0,
            container_id=None,
            image=None
        )
        mock_super_rm.return_value = mock_result
        driver.image_repo.delete_image.side_effect = Exception("DB Error")

        # Execute
        result = driver.image_rm("test_image", show_output=True)

        # Verify operation still succeeds
        assert result == mock_result
