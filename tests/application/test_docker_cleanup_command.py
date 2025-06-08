"""Tests for DockerCleanupCommand."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.application.commands.docker_cleanup_command import CleanupResult, DockerCleanupCommand
from src.infrastructure.di_container import DIKey


class TestDockerCleanupCommand:
    """Test DockerCleanupCommand functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_container = MagicMock()
        self.mock_container_repo = MagicMock()
        self.mock_image_repo = MagicMock()
        self.mock_docker_driver = MagicMock()

        # Configure container to return mocks
        def mock_resolve(key):
            if key == DIKey.DOCKER_CONTAINER_REPOSITORY:
                return self.mock_container_repo
            if key == DIKey.DOCKER_IMAGE_REPOSITORY:
                return self.mock_image_repo
            if key == DIKey.DOCKER_DRIVER:
                return self.mock_docker_driver
            return None

        self.mock_container.resolve.side_effect = mock_resolve
        self.command = DockerCleanupCommand(self.mock_container)

    def test_init(self):
        """Test command initialization."""
        assert self.command.container == self.mock_container
        assert self.command._container_repo is None
        assert self.command._image_repo is None
        assert self.command._docker_driver is None

    def test_lazy_loading_properties(self):
        """Test lazy loading of repository properties."""
        # Test container_repo property
        container_repo = self.command.container_repo
        assert container_repo == self.mock_container_repo
        assert self.command._container_repo == self.mock_container_repo

        # Test image_repo property
        image_repo = self.command.image_repo
        assert image_repo == self.mock_image_repo
        assert self.command._image_repo == self.mock_image_repo

        # Test docker_driver property
        docker_driver = self.command.docker_driver
        assert docker_driver == self.mock_docker_driver
        assert self.command._docker_driver == self.mock_docker_driver

    def test_find_unused_containers(self):
        """Test finding unused containers."""
        expected_containers = [{'container_name': 'test_container'}]
        self.mock_container_repo.find_unused_containers.return_value = expected_containers

        result = self.command.find_unused_containers(7)

        assert result == expected_containers
        self.mock_container_repo.find_unused_containers.assert_called_once_with(7)

    def test_find_unused_images(self):
        """Test finding unused images."""
        expected_images = [{'name': 'test_image', 'tag': 'latest'}]
        self.mock_image_repo.find_unused_images.return_value = expected_images

        result = self.command.find_unused_images(30)

        assert result == expected_images
        self.mock_image_repo.find_unused_images.assert_called_once_with(30)

    def test_cleanup_containers_dry_run(self):
        """Test container cleanup in dry run mode."""
        unused_containers = [
            {'container_name': 'test_container1', 'last_used_at': '2023-01-01'},
            {'container_name': 'test_container2', 'last_used_at': '2023-01-02'}
        ]
        self.mock_container_repo.find_unused_containers.return_value = unused_containers

        with patch('builtins.print') as mock_print:
            result = self.command.cleanup_containers(dry_run=True)

        assert len(result.containers_removed) == 2
        assert 'test_container1' in result.containers_removed
        assert 'test_container2' in result.containers_removed
        assert len(result.errors) == 0
        assert mock_print.call_count == 2

    def test_cleanup_containers_with_exclusions(self):
        """Test container cleanup with exclusion patterns."""
        unused_containers = [
            {'container_name': 'test_container1', 'last_used_at': '2023-01-01'},
            {'container_name': 'exclude_me', 'last_used_at': '2023-01-02'}
        ]
        self.mock_container_repo.find_unused_containers.return_value = unused_containers

        with patch('builtins.print'):
            result = self.command.cleanup_containers(
                dry_run=True,
                exclude_patterns=['exclude_']
            )

        assert len(result.containers_removed) == 1
        assert 'test_container1' in result.containers_removed
        assert 'exclude_me' not in result.containers_removed

    def test_cleanup_containers_successful_removal(self):
        """Test successful container removal."""
        unused_containers = [{'container_name': 'test_container', 'last_used_at': '2023-01-01'}]
        self.mock_container_repo.find_unused_containers.return_value = unused_containers

        # Mock Docker driver responses
        self.mock_docker_driver.ps.return_value = ['test_container']
        mock_result = MagicMock()
        mock_result.success = True
        self.mock_docker_driver.remove_container.return_value = mock_result

        with patch('builtins.print') as mock_print:
            result = self.command.cleanup_containers(dry_run=False)

        assert len(result.containers_removed) == 1
        assert 'test_container' in result.containers_removed
        assert len(result.errors) == 0
        mock_print.assert_called_once_with("Removed container: test_container")

    def test_cleanup_containers_not_in_docker(self):
        """Test cleanup when container not in Docker."""
        unused_containers = [{'container_name': 'test_container', 'last_used_at': '2023-01-01'}]
        self.mock_container_repo.find_unused_containers.return_value = unused_containers

        # Container not in Docker
        self.mock_docker_driver.ps.return_value = []

        with patch('builtins.print') as mock_print:
            result = self.command.cleanup_containers(dry_run=False)

        assert len(result.containers_removed) == 1
        assert 'test_container' in result.containers_removed
        self.mock_container_repo.mark_container_removed.assert_called_once_with('test_container')
        mock_print.assert_called_once_with("Marked container as removed (not in Docker): test_container")

    def test_cleanup_images_dry_run(self):
        """Test image cleanup in dry run mode."""
        unused_images = [
            {'name': 'test_image', 'tag': 'latest', 'last_used_at': '2023-01-01'}
        ]
        self.mock_image_repo.find_unused_images.return_value = unused_images
        self.mock_container_repo.find_containers_by_status.return_value = []

        with patch('builtins.print') as mock_print:
            result = self.command.cleanup_images(dry_run=True)

        assert len(result.images_removed) == 1
        assert 'test_image:latest' in result.images_removed
        mock_print.assert_called_once()

    def test_cleanup_images_successful_removal(self):
        """Test successful image removal."""
        unused_images = [
            {'name': 'test_image', 'tag': 'latest', 'size_bytes': 1024000}
        ]
        self.mock_image_repo.find_unused_images.return_value = unused_images
        self.mock_container_repo.find_containers_by_status.return_value = []

        mock_result = MagicMock()
        mock_result.success = True
        self.mock_docker_driver.image_rm.return_value = mock_result

        with patch('builtins.print') as mock_print:
            result = self.command.cleanup_images(dry_run=False)

        assert len(result.images_removed) == 1
        assert 'test_image:latest' in result.images_removed
        assert result.space_freed_bytes == 1024000
        mock_print.assert_called_once_with("Removed image: test_image:latest")

    def test_cleanup_images_skips_in_use(self):
        """Test that images in use are skipped."""
        unused_images = [
            {'name': 'test_image', 'tag': 'latest'}
        ]
        containers_using = [
            {'image_name': 'test_image', 'status': 'running'}
        ]

        self.mock_image_repo.find_unused_images.return_value = unused_images
        self.mock_container_repo.find_containers_by_status.return_value = containers_using

        result = self.command.cleanup_images(dry_run=False)

        assert len(result.images_removed) == 0
        self.mock_docker_driver.image_rm.assert_not_called()

    def test_cleanup_all(self):
        """Test cleanup_all combines container and image cleanup."""
        # Mock container cleanup
        self.mock_container_repo.find_unused_containers.return_value = [
            {'container_name': 'container1', 'last_used_at': '2023-01-01'}
        ]

        # Mock image cleanup
        self.mock_image_repo.find_unused_images.return_value = [
            {'name': 'image1', 'tag': 'latest', 'size_bytes': 1024}
        ]
        self.mock_container_repo.find_containers_by_status.return_value = []

        # Mock Docker operations
        self.mock_docker_driver.ps.return_value = []
        mock_result = MagicMock()
        mock_result.success = True
        self.mock_docker_driver.image_rm.return_value = mock_result

        with patch('builtins.print'):
            result = self.command.cleanup_all(dry_run=False)

        assert len(result.containers_removed) == 1
        assert len(result.images_removed) == 1
        assert result.space_freed_bytes == 1024

    def test_get_cleanup_summary(self):
        """Test getting cleanup summary."""
        # Mock different day ranges for containers
        def mock_find_unused_containers(days):
            if days == 7:
                return [1, 2]
            if days == 14:
                return [1, 2, 3]
            if days == 30:
                return [1, 2, 3, 4]
            return []

        # Mock different day ranges for images
        def mock_find_unused_images(days):
            if days == 30:
                return [{'size_bytes': 1024}, {'size_bytes': 2048}]
            if days == 60:
                return [1, 2, 3]
            if days == 90:
                return [1, 2, 3, 4]
            return []

        self.mock_container_repo.find_unused_containers.side_effect = mock_find_unused_containers
        self.mock_image_repo.find_unused_images.side_effect = mock_find_unused_images

        summary = self.command.get_cleanup_summary()

        assert summary['containers']['7_days'] == 2
        assert summary['containers']['14_days'] == 3
        assert summary['containers']['30_days'] == 4
        assert summary['images']['30_days'] == 2
        assert summary['images']['60_days'] == 3
        assert summary['images']['90_days'] == 4
        assert summary['potential_space_freed_mb'] == (1024 + 2048) / (1024 * 1024)


class TestCleanupResult:
    """Test CleanupResult dataclass."""

    def test_cleanup_result_creation(self):
        """Test CleanupResult creation."""
        result = CleanupResult(
            containers_removed=['container1'],
            images_removed=['image1'],
            errors=['error1'],
            space_freed_bytes=1024
        )

        assert result.containers_removed == ['container1']
        assert result.images_removed == ['image1']
        assert result.errors == ['error1']
        assert result.space_freed_bytes == 1024

    def test_cleanup_result_defaults(self):
        """Test CleanupResult with default values."""
        result = CleanupResult(
            containers_removed=[],
            images_removed=[],
            errors=[]
        )

        assert result.space_freed_bytes == 0
