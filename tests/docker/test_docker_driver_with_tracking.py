"""Tests for LocalDockerDriverWithTracking."""
import hashlib
import time
from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.di_container import DIKey
from src.infrastructure.drivers.docker.docker_driver_with_tracking import LocalDockerDriverWithTracking


class TestLocalDockerDriverWithTracking:
    """Test LocalDockerDriverWithTracking functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_container = MagicMock()
        self.mock_container_repo = MagicMock()
        self.mock_image_repo = MagicMock()

        # Configure container to return mocks
        def mock_resolve(key):
            if key == DIKey.DOCKER_CONTAINER_REPOSITORY:
                return self.mock_container_repo
            if key == DIKey.DOCKER_IMAGE_REPOSITORY:
                return self.mock_image_repo
            return None

        self.mock_container.resolve.side_effect = mock_resolve
        self.driver = LocalDockerDriverWithTracking(self.mock_container)

    def test_init(self):
        """Test driver initialization."""
        assert self.driver.di_container == self.mock_container
        assert self.driver._container_repo is None
        assert self.driver._image_repo is None

    def test_lazy_loading_properties(self):
        """Test lazy loading of repository properties."""
        # Test container_repo property
        container_repo = self.driver.container_repo
        assert container_repo == self.mock_container_repo
        assert self.driver._container_repo == self.mock_container_repo

        # Test image_repo property
        image_repo = self.driver.image_repo
        assert image_repo == self.mock_image_repo
        assert self.driver._image_repo == self.mock_image_repo

    @patch('src.infrastructure.drivers.docker.docker_driver.LocalDockerDriver.run_container')
    def test_run_container_success_with_tracking(self, mock_super_run):
        """Test successful container run with tracking."""
        # Setup
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        mock_super_run.return_value = mock_result

        # Execute
        result = self.driver.run_container("ubuntu", name="test-container", options={"port": "8080"}, show_output=True)

        # Assert
        assert result == mock_result
        mock_super_run.assert_called_once_with("ubuntu", name="test-container", options={"port": "8080"}, show_output=True)

        # Verify tracking calls
        self.mock_container_repo.update_container_status.assert_called_once_with(
            "test-container", "running", "started_at"
        )
        self.mock_container_repo.add_lifecycle_event.assert_called_once_with(
            "test-container", "started", {"image": "ubuntu", "options": {"port": "8080"}}
        )
        self.mock_container_repo.update_container_id.assert_called_once_with(
            "test-container", "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        )

    @patch('src.infrastructure.drivers.docker.docker_driver.LocalDockerDriver.run_container')
    def test_run_container_success_no_container_id(self, mock_super_run):
        """Test successful container run without container ID."""
        # Setup
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "short_id"  # Not 64 characters
        mock_super_run.return_value = mock_result

        # Execute
        result = self.driver.run_container("ubuntu", name="test-container", options={}, show_output=True)

        # Assert
        assert result == mock_result
        self.mock_container_repo.update_container_status.assert_called_once()
        self.mock_container_repo.add_lifecycle_event.assert_called_once()
        self.mock_container_repo.update_container_id.assert_not_called()

    @patch('src.infrastructure.drivers.docker.docker_driver.LocalDockerDriver.run_container')
    def test_run_container_success_no_name(self, mock_super_run):
        """Test successful container run without name."""
        # Setup
        mock_result = MagicMock()
        mock_result.success = True
        mock_super_run.return_value = mock_result

        # Execute
        result = self.driver.run_container("ubuntu", name=None, options={}, show_output=True)

        # Assert
        assert result == mock_result
        self.mock_container_repo.update_container_status.assert_not_called()
        self.mock_container_repo.add_lifecycle_event.assert_not_called()

    @patch('src.infrastructure.drivers.docker.docker_driver.LocalDockerDriver.run_container')
    def test_run_container_failure(self, mock_super_run):
        """Test failed container run."""
        # Setup
        mock_result = MagicMock()
        mock_result.success = False
        mock_super_run.return_value = mock_result

        # Execute
        result = self.driver.run_container("ubuntu", name="test-container", options={}, show_output=True)

        # Assert
        assert result == mock_result
        self.mock_container_repo.update_container_status.assert_not_called()
        self.mock_container_repo.add_lifecycle_event.assert_not_called()


    @patch('src.infrastructure.drivers.docker.docker_driver.LocalDockerDriver.stop_container')
    def test_stop_container_success(self, mock_super_stop):
        """Test successful container stop with tracking."""
        # Setup
        mock_result = MagicMock()
        mock_result.success = True
        mock_super_stop.return_value = mock_result

        # Execute
        result = self.driver.stop_container("test-container")

        # Assert
        assert result == mock_result
        mock_super_stop.assert_called_once_with("test-container", True)

        # Verify tracking calls
        self.mock_container_repo.update_container_status.assert_called_once_with(
            "test-container", "stopped", "stopped_at"
        )
        self.mock_container_repo.add_lifecycle_event.assert_called_once_with(
            "test-container", "stopped"
        )

    @patch('src.infrastructure.drivers.docker.docker_driver.LocalDockerDriver.stop_container')
    def test_stop_container_failure(self, mock_super_stop):
        """Test failed container stop."""
        # Setup
        mock_result = MagicMock()
        mock_result.success = False
        mock_super_stop.return_value = mock_result

        # Execute
        result = self.driver.stop_container("test-container")

        # Assert
        assert result == mock_result
        self.mock_container_repo.update_container_status.assert_not_called()
        self.mock_container_repo.add_lifecycle_event.assert_not_called()


    @patch('src.infrastructure.drivers.docker.docker_driver.LocalDockerDriver.remove_container')
    def test_remove_container_success(self, mock_super_remove):
        """Test successful container removal with tracking."""
        # Setup
        mock_result = MagicMock()
        mock_result.success = True
        mock_super_remove.return_value = mock_result

        # Execute
        result = self.driver.remove_container("test-container", force=True)

        # Assert
        assert result == mock_result
        mock_super_remove.assert_called_once_with("test-container", True, True)

        # Verify tracking calls
        self.mock_container_repo.mark_container_removed.assert_called_once_with("test-container")
        self.mock_container_repo.add_lifecycle_event.assert_called_once_with(
            "test-container", "removed", {"force": True}
        )

    @patch('src.infrastructure.drivers.docker.docker_driver.LocalDockerDriver.remove_container')
    def test_remove_container_failure(self, mock_super_remove):
        """Test failed container removal."""
        # Setup
        mock_result = MagicMock()
        mock_result.success = False
        mock_super_remove.return_value = mock_result

        # Execute
        result = self.driver.remove_container("test-container")

        # Assert
        assert result == mock_result
        self.mock_container_repo.mark_container_removed.assert_not_called()
        self.mock_container_repo.add_lifecycle_event.assert_not_called()

    @patch('time.time')
    @patch('src.infrastructure.drivers.docker.docker_driver.LocalDockerDriver.build_docker_image')
    def test_build_success_with_image_id(self, mock_super_build, mock_time):
        """Test successful image build with tracking."""
        # Setup
        mock_time.side_effect = [1000.0, 1002.5]  # 2.5 second build time

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "Step 3/3 : CMD echo hello\nSuccessfully built abc123def456\nSuccessfully tagged test:latest"
        mock_super_build.return_value = mock_result

        dockerfile_text = "FROM ubuntu\nCMD echo hello"
        expected_hash = hashlib.sha256(dockerfile_text.encode('utf-8')).hexdigest()[:12]

        # Execute
        result = self.driver.build_docker_image(dockerfile_text, tag="test:latest", options={}, show_output=True)

        # Assert
        assert result == mock_result
        mock_super_build.assert_called_once_with(dockerfile_text, tag="test:latest", options={}, show_output=True)

        # Verify tracking calls
        self.mock_image_repo.create_or_update_image.assert_called_once_with(
            name="test:latest",
            dockerfile_hash=expected_hash,
            build_command="docker build -t test:latest",
            build_status="building"
        )
        self.mock_image_repo.update_image_build_result.assert_called_once_with(
            name="test:latest",
            tag="latest",
            image_id="abc123def456",
            build_status="success",
            build_time_ms=2500
        )

    @patch('time.time')
    @patch('src.infrastructure.drivers.docker.docker_driver.LocalDockerDriver.build_docker_image')
    def test_build_success_no_image_id(self, mock_super_build, mock_time):
        """Test successful image build without image ID."""
        # Setup
        mock_time.side_effect = [1000.0, 1001.0]  # 1 second build time

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "Step 3/3 : CMD echo hello"  # No "Successfully built" line
        mock_super_build.return_value = mock_result

        dockerfile_text = "FROM ubuntu"

        # Execute
        result = self.driver.build_docker_image(dockerfile_text, tag="test", options={}, show_output=True)

        # Assert
        assert result == mock_result
        self.mock_image_repo.update_image_build_result.assert_called_once_with(
            name="test",
            tag="latest",
            image_id=None,
            build_status="success",
            build_time_ms=1000
        )

    @patch('time.time')
    @patch('src.infrastructure.drivers.docker.docker_driver.LocalDockerDriver.build_docker_image')
    def test_build_failure(self, mock_super_build, mock_time):
        """Test failed image build."""
        # Setup
        mock_time.side_effect = [1000.0, 1001.5]  # 1.5 second build time

        mock_result = MagicMock()
        mock_result.success = False
        mock_super_build.return_value = mock_result

        dockerfile_text = "FROM invalid"

        # Execute
        result = self.driver.build_docker_image(dockerfile_text, tag="test", options={}, show_output=True)

        # Assert
        assert result == mock_result
        self.mock_image_repo.update_image_build_result.assert_called_once_with(
            name="test",
            tag="latest",
            build_status="failed",
            build_time_ms=1500
        )

    @patch('src.infrastructure.drivers.docker.docker_driver.LocalDockerDriver.build_docker_image')
    def test_build_no_tag(self, mock_super_build):
        """Test image build without tag."""
        # Setup
        mock_result = MagicMock()
        mock_result.success = True
        mock_super_build.return_value = mock_result

        dockerfile_text = "FROM ubuntu"

        # Execute
        result = self.driver.build_docker_image(dockerfile_text, tag=None, options={}, show_output=True)

        # Assert
        assert result == mock_result
        self.mock_image_repo.create_or_update_image.assert_not_called()
        self.mock_image_repo.update_image_build_result.assert_not_called()

    @patch('src.infrastructure.drivers.docker.docker_driver.LocalDockerDriver.image_rm')
    def test_image_rm_success_with_tag(self, mock_super_rm):
        """Test successful image removal with tag."""
        # Setup
        mock_result = MagicMock()
        mock_result.success = True
        mock_super_rm.return_value = mock_result

        # Execute
        result = self.driver.image_rm("test:v1.0")

        # Assert
        assert result == mock_result
        mock_super_rm.assert_called_once_with("test:v1.0", True)

        # Verify tracking call
        self.mock_image_repo.delete_image.assert_called_once_with("test", "v1.0")

    @patch('src.infrastructure.drivers.docker.docker_driver.LocalDockerDriver.image_rm')
    def test_image_rm_success_no_tag(self, mock_super_rm):
        """Test successful image removal without tag."""
        # Setup
        mock_result = MagicMock()
        mock_result.success = True
        mock_super_rm.return_value = mock_result

        # Execute
        result = self.driver.image_rm("test")

        # Assert
        assert result == mock_result

        # Verify tracking call - should default to "latest"
        self.mock_image_repo.delete_image.assert_called_once_with("test", "latest")

    @patch('src.infrastructure.drivers.docker.docker_driver.LocalDockerDriver.image_rm')
    def test_image_rm_failure(self, mock_super_rm):
        """Test failed image removal."""
        # Setup
        mock_result = MagicMock()
        mock_result.success = False
        mock_super_rm.return_value = mock_result

        # Execute
        result = self.driver.image_rm("test")

        # Assert
        assert result == mock_result
        self.mock_image_repo.delete_image.assert_not_called()
