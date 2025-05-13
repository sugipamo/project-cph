import pytest
from unittest.mock import patch, MagicMock
from src.execution_client.container.image_manager import ContainerImageManager
import subprocess
import os

def test_build_image_success():
    manager = ContainerImageManager()
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        result = manager.build_image('Dockerfile', 'img')
        assert result is True

def test_build_image_failure():
    manager = ContainerImageManager()
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, 'docker', stderr='fail')
        result = manager.build_image('Dockerfile', 'img')
        assert result is False

def test_remove_image_success():
    manager = ContainerImageManager()
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        result = manager.remove_image('img')
        assert result is True

def test_remove_image_failure():
    manager = ContainerImageManager()
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, 'docker', stderr='fail')
        result = manager.remove_image('img')
        assert result is False

def test_image_exists_true():
    manager = ContainerImageManager()
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = 'img\nother\n'
        result = manager.image_exists('img')
        assert result is True

def test_image_exists_false():
    manager = ContainerImageManager()
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = 'other\n'
        result = manager.image_exists('img')
        assert result is False

def test_get_dockerfile_hash(tmp_path):
    manager = ContainerImageManager()
    dockerfile = tmp_path / 'Dockerfile'
    dockerfile.write_text('FROM python:3.8')
    hashval = manager.get_dockerfile_hash(str(dockerfile))
    assert isinstance(hashval, str) and len(hashval) == 12

def test_get_image_name_ojtools():
    manager = ContainerImageManager()
    name = manager.get_image_name(('ojtools', None))
    assert name == 'cph_image_ojtools'

def test_get_image_name_fallback():
    manager = ContainerImageManager()
    name = manager.get_image_name(('python', '3.8'))
    assert name == 'python_3.8'

def test_get_image_name_with_dockerfile(tmp_path):
    dockerfile = tmp_path / 'Dockerfile'
    dockerfile.write_text('FROM python:3.8')
    manager = ContainerImageManager({('python', '3.8'): str(dockerfile)})
    name = manager.get_image_name(('python', '3.8'))
    assert name.startswith('cph_image_python_3.8_')
    assert len(name.split('_')[-1]) == 12

def test_cleanup_old_images():
    manager = ContainerImageManager()
    with patch.object(manager, 'get_image_name', return_value='cph_image_python_3.8_hash'):
        with patch('subprocess.run') as mock_run, patch.object(manager, 'remove_image') as mock_remove:
            mock_run.return_value.stdout = 'cph_image_python_3.8_hash\ncph_image_python_3.8_old\nother\n'
            manager.cleanup_old_images('python_3.8')
            mock_remove.assert_called_with('cph_image_python_3.8_old')

def test_ensure_image_build_and_cleanup(tmp_path):
    dockerfile = tmp_path / 'Dockerfile'
    dockerfile.write_text('FROM python:3.8')
    key = ('python', '3.8')
    manager = ContainerImageManager({key: str(dockerfile)})
    with patch('subprocess.run') as mock_run, \
         patch.object(manager, 'build_image') as mock_build, \
         patch.object(manager, 'cleanup_old_images') as mock_cleanup:
        # イメージがまだ存在しない場合
        mock_run.return_value.stdout = 'other\n'
        manager.ensure_image(key, context_dir=str(tmp_path))
        mock_build.assert_called_once()
        mock_cleanup.assert_called_once()
    # 既にイメージが存在する場合
    with patch('subprocess.run') as mock_run, \
         patch.object(manager, 'build_image') as mock_build, \
         patch.object(manager, 'cleanup_old_images') as mock_cleanup:
        mock_run.return_value.stdout = manager.get_image_name(key) + '\nother\n'
        manager.ensure_image(key, context_dir=str(tmp_path))
        mock_build.assert_not_called()
        mock_cleanup.assert_not_called() 