"""
Test for new conftest.py fixtures
"""
from pathlib import Path

import pytest


def test_temp_workspace_fixture(temp_workspace):
    """Test temporary workspace fixture"""
    assert isinstance(temp_workspace, Path)
    assert temp_workspace.exists()

    # Create a test file
    test_file = temp_workspace / "test.txt"
    test_file.write_text("test content")
    assert test_file.exists()


def test_mock_infrastructure_fixture(mock_infrastructure):
    """Test mock infrastructure fixture"""
    assert mock_infrastructure is not None

    # Test that drivers can be resolved
    file_driver = mock_infrastructure.resolve('file_driver')
    shell_driver = mock_infrastructure.resolve('shell_driver')
    docker_driver = mock_infrastructure.resolve('docker_driver')
    python_driver = mock_infrastructure.resolve('python_driver')

    assert file_driver is not None
    assert shell_driver is not None
    assert docker_driver is not None
    assert python_driver is not None


def test_mock_drivers_fixture(mock_drivers):
    """Test mock drivers fixture"""
    assert 'file_driver' in mock_drivers
    assert 'shell_driver' in mock_drivers
    assert 'docker_driver' in mock_drivers
    assert 'python_driver' in mock_drivers

    # Test that drivers are accessible
    file_driver = mock_drivers['file_driver']
    assert hasattr(file_driver, 'files')
    assert hasattr(file_driver, 'contents')


def test_clean_mock_state_fixture(clean_mock_state):
    """Test clean mock state fixture"""
    # Should receive clean mock drivers
    file_driver = clean_mock_state['file_driver']
    shell_driver = clean_mock_state['shell_driver']

    # Verify they are clean
    assert len(file_driver.files) == 0
    assert len(file_driver.contents) == 0
    assert len(file_driver.operations) == 0
    assert len(shell_driver._commands_executed) == 0


def test_di_container_fixture(di_container):
    """Test DI container fixture"""
    assert di_container is not None

    # Test that request types are registered
    docker_request = di_container.resolve("DockerRequest")
    file_request = di_container.resolve("FileRequest")
    shell_request = di_container.resolve("ShellRequest")
    python_request = di_container.resolve("PythonRequest")

    assert docker_request is not None
    assert file_request is not None
    assert shell_request is not None
    assert python_request is not None


def test_mock_env_context_fixture(mock_env_context):
    """Test mock environment context fixture"""
    assert mock_env_context.contest_name == "test_contest"
    assert mock_env_context.problem_name == "a"
    assert mock_env_context.language == "python"
    assert mock_env_context.command_type == "test"
    assert mock_env_context.env_type == "local"
