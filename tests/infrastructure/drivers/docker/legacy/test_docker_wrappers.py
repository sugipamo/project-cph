"""Tests for Docker wrapper utilities"""
from unittest.mock import Mock, patch

import pytest

from src.infrastructure.drivers.docker.legacy.docker_wrappers import (
    build_docker_build_command_wrapper,
    build_docker_cp_command_wrapper,
    build_docker_inspect_command_wrapper,
    build_docker_ps_command_wrapper,
    build_docker_remove_command_wrapper,
    build_docker_run_command_wrapper,
    build_docker_stop_command_wrapper,
    validate_docker_image_name_wrapper,
)


class TestDockerWrappers:
    """Test Docker wrapper functions"""

    @patch('src.infrastructure.drivers.docker.utils.docker_command_builder.build_docker_run_command')
    def test_build_docker_run_command_wrapper(self, mock_build_run):
        """Test docker run command wrapper"""
        mock_build_run.return_value = ['docker', 'run', 'test-image']

        result = build_docker_run_command_wrapper('test-image')

        mock_build_run.assert_called_once_with('test-image')
        assert result == ['docker', 'run', 'test-image']

    @patch('src.infrastructure.drivers.docker.utils.docker_command_builder.build_docker_run_command')
    def test_build_docker_run_command_wrapper_with_kwargs(self, mock_build_run):
        """Test docker run command wrapper with kwargs"""
        mock_build_run.return_value = ['docker', 'run', '-d', 'test-image']

        result = build_docker_run_command_wrapper('test-image', detach=True)

        mock_build_run.assert_called_once_with('test-image', detach=True)
        assert result == ['docker', 'run', '-d', 'test-image']

    @patch('src.infrastructure.drivers.docker.utils.docker_command_builder.build_docker_build_command')
    def test_build_docker_build_command_wrapper(self, mock_build_build):
        """Test docker build command wrapper"""
        mock_build_build.return_value = ['docker', 'build', '/path']

        result = build_docker_build_command_wrapper('/path')

        mock_build_build.assert_called_once_with('/path')
        assert result == ['docker', 'build', '/path']

    @patch('src.infrastructure.drivers.docker.utils.docker_command_builder.build_docker_build_command')
    def test_build_docker_build_command_wrapper_with_kwargs(self, mock_build_build):
        """Test docker build command wrapper with kwargs"""
        mock_build_build.return_value = ['docker', 'build', '-t', 'test:latest', '/path']

        result = build_docker_build_command_wrapper('/path', tag='test:latest')

        mock_build_build.assert_called_once_with('/path', tag='test:latest')
        assert result == ['docker', 'build', '-t', 'test:latest', '/path']

    @patch('src.infrastructure.drivers.docker.utils.docker_command_builder.build_docker_stop_command')
    def test_build_docker_stop_command_wrapper(self, mock_build_stop):
        """Test docker stop command wrapper"""
        mock_build_stop.return_value = ['docker', 'stop', 'container-id']

        result = build_docker_stop_command_wrapper('container-id')

        mock_build_stop.assert_called_once_with('container-id')
        assert result == ['docker', 'stop', 'container-id']

    @patch('src.infrastructure.drivers.docker.utils.docker_command_builder.build_docker_stop_command')
    def test_build_docker_stop_command_wrapper_with_kwargs(self, mock_build_stop):
        """Test docker stop command wrapper with kwargs"""
        mock_build_stop.return_value = ['docker', 'stop', '-t', '10', 'container-id']

        result = build_docker_stop_command_wrapper('container-id', timeout=10)

        mock_build_stop.assert_called_once_with('container-id', timeout=10)
        assert result == ['docker', 'stop', '-t', '10', 'container-id']

    @patch('src.infrastructure.drivers.docker.utils.docker_command_builder.build_docker_remove_command')
    def test_build_docker_remove_command_wrapper(self, mock_build_remove):
        """Test docker remove command wrapper"""
        mock_build_remove.return_value = ['docker', 'rm', 'container-id']

        result = build_docker_remove_command_wrapper('container-id')

        mock_build_remove.assert_called_once_with('container-id')
        assert result == ['docker', 'rm', 'container-id']

    @patch('src.infrastructure.drivers.docker.utils.docker_command_builder.build_docker_remove_command')
    def test_build_docker_remove_command_wrapper_with_kwargs(self, mock_build_remove):
        """Test docker remove command wrapper with kwargs"""
        mock_build_remove.return_value = ['docker', 'rm', '-f', 'container-id']

        result = build_docker_remove_command_wrapper('container-id', force=True)

        mock_build_remove.assert_called_once_with('container-id', force=True)
        assert result == ['docker', 'rm', '-f', 'container-id']

    @patch('src.infrastructure.drivers.docker.utils.docker_command_builder.build_docker_ps_command')
    def test_build_docker_ps_command_wrapper(self, mock_build_ps):
        """Test docker ps command wrapper"""
        mock_build_ps.return_value = ['docker', 'ps']

        result = build_docker_ps_command_wrapper()

        mock_build_ps.assert_called_once_with()
        assert result == ['docker', 'ps']

    @patch('src.infrastructure.drivers.docker.utils.docker_command_builder.build_docker_ps_command')
    def test_build_docker_ps_command_wrapper_with_kwargs(self, mock_build_ps):
        """Test docker ps command wrapper with kwargs"""
        mock_build_ps.return_value = ['docker', 'ps', '-a']

        result = build_docker_ps_command_wrapper(all=True)

        mock_build_ps.assert_called_once_with(all=True)
        assert result == ['docker', 'ps', '-a']

    @patch('src.infrastructure.drivers.docker.utils.docker_command_builder.build_docker_inspect_command')
    def test_build_docker_inspect_command_wrapper(self, mock_build_inspect):
        """Test docker inspect command wrapper"""
        mock_build_inspect.return_value = ['docker', 'inspect', 'container-id']

        result = build_docker_inspect_command_wrapper('container-id')

        mock_build_inspect.assert_called_once_with('container-id')
        assert result == ['docker', 'inspect', 'container-id']

    @patch('src.infrastructure.drivers.docker.utils.docker_command_builder.build_docker_inspect_command')
    def test_build_docker_inspect_command_wrapper_with_kwargs(self, mock_build_inspect):
        """Test docker inspect command wrapper with kwargs"""
        mock_build_inspect.return_value = ['docker', 'inspect', '--format', '{{.State}}', 'container-id']

        result = build_docker_inspect_command_wrapper('container-id', format='{{.State}}')

        mock_build_inspect.assert_called_once_with('container-id', format='{{.State}}')
        assert result == ['docker', 'inspect', '--format', '{{.State}}', 'container-id']

    @patch('src.infrastructure.drivers.docker.utils.docker_command_builder.build_docker_cp_command')
    def test_build_docker_cp_command_wrapper(self, mock_build_cp):
        """Test docker cp command wrapper"""
        mock_build_cp.return_value = ['docker', 'cp', 'source', 'destination']

        result = build_docker_cp_command_wrapper('source', 'destination')

        mock_build_cp.assert_called_once_with('source', 'destination')
        assert result == ['docker', 'cp', 'source', 'destination']

    @patch('src.infrastructure.drivers.docker.utils.docker_command_builder.build_docker_cp_command')
    def test_build_docker_cp_command_wrapper_with_kwargs(self, mock_build_cp):
        """Test docker cp command wrapper with kwargs"""
        mock_build_cp.return_value = ['docker', 'cp', '-a', 'source', 'destination']

        result = build_docker_cp_command_wrapper('source', 'destination', archive=True)

        mock_build_cp.assert_called_once_with('source', 'destination', archive=True)
        assert result == ['docker', 'cp', '-a', 'source', 'destination']

    @patch('src.infrastructure.drivers.docker.utils.docker_utils.validate_docker_image_name')
    def test_validate_docker_image_name_wrapper_valid(self, mock_validate):
        """Test docker image name validation wrapper with valid name"""
        mock_validate.return_value = True

        result = validate_docker_image_name_wrapper('test-image:latest')

        mock_validate.assert_called_once_with('test-image:latest')
        assert result is True

    @patch('src.infrastructure.drivers.docker.utils.docker_utils.validate_docker_image_name')
    def test_validate_docker_image_name_wrapper_invalid(self, mock_validate):
        """Test docker image name validation wrapper with invalid name"""
        mock_validate.return_value = False

        result = validate_docker_image_name_wrapper('invalid name')

        mock_validate.assert_called_once_with('invalid name')
        assert result is False
