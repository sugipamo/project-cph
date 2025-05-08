import os
import tempfile
import shutil
import hashlib
import pytest
from unittest.mock import patch
from src.container.image_manager import ContainerImageManager

def create_temp_dockerfile(content="FROM scratch\n"):
    temp_dir = tempfile.mkdtemp()
    dockerfile_path = os.path.join(temp_dir, "Dockerfile")
    with open(dockerfile_path, "w") as f:
        f.write(content)
    return temp_dir, dockerfile_path

def test_get_dockerfile_hash():
    temp_dir, dockerfile_path = create_temp_dockerfile("FROM python:3.10\n")
    manager = ContainerImageManager({"python": dockerfile_path})
    expected_hash = hashlib.sha256(b"FROM python:3.10\n").hexdigest()[:12]
    assert manager.get_dockerfile_hash(dockerfile_path) == expected_hash
    shutil.rmtree(temp_dir)

def test_get_image_name():
    temp_dir, dockerfile_path = create_temp_dockerfile("FROM python:3.10\n")
    manager = ContainerImageManager({"python": dockerfile_path})
    hashval = manager.get_dockerfile_hash(dockerfile_path)
    assert manager.get_image_name("python") == f"cph_image_python_{hashval}"
    shutil.rmtree(temp_dir)

@patch("subprocess.run")
def test_image_exists(mock_run):
    mock_run.return_value.stdout = "cph_image_python_123456789abc\n"
    manager = ContainerImageManager()
    assert manager.image_exists("cph_image_python_123456789abc")
    assert not manager.image_exists("not_exist_image")

@patch("subprocess.run")
def test_build_image(mock_run):
    mock_run.return_value.returncode = 0
    temp_dir, dockerfile_path = create_temp_dockerfile()
    manager = ContainerImageManager()
    assert manager.build_image(dockerfile_path, "test_image", temp_dir)
    shutil.rmtree(temp_dir)

@patch("subprocess.run")
def test_remove_image(mock_run):
    mock_run.return_value.returncode = 0
    manager = ContainerImageManager()
    assert manager.remove_image("test_image")

@patch("subprocess.run")
def test_cleanup_old_images(mock_run):
    # 2つのイメージがあり、1つだけ残す
    mock_run.return_value.stdout = "cph_image_python_aaa\ncph_image_python_bbb\n"
    manager = ContainerImageManager()
    with patch.object(manager, "remove_image") as mock_remove:
        with patch.object(manager, "get_image_name", return_value="cph_image_python_aaa"):
            manager.cleanup_old_images("python")
            mock_remove.assert_called_once_with("cph_image_python_bbb")

@patch("subprocess.run")
def test_ensure_image_builds_if_not_exists(mock_run):
    # イメージが存在しない場合はbuild_imageとcleanup_old_imagesが呼ばれる
    mock_run.return_value.stdout = ""
    temp_dir, dockerfile_path = create_temp_dockerfile()
    manager = ContainerImageManager({"python": dockerfile_path})
    with patch.object(manager, "build_image") as mock_build, \
         patch.object(manager, "cleanup_old_images") as mock_cleanup:
        mock_build.return_value = True
        image = manager.ensure_image("python", temp_dir)
        assert mock_build.called
        assert mock_cleanup.called
    shutil.rmtree(temp_dir)

@patch("subprocess.run")
def test_ensure_image_skips_if_exists(mock_run):
    temp_dir, dockerfile_path = create_temp_dockerfile()
    manager = ContainerImageManager({"python": dockerfile_path})
    image_name = manager.get_image_name("python")
    mock_run.return_value.stdout = f"{image_name}\n"
    with patch.object(manager, "build_image") as mock_build, \
         patch.object(manager, "cleanup_old_images") as mock_cleanup:
        image = manager.ensure_image("python", temp_dir)
        assert not mock_build.called
        assert not mock_cleanup.called
    shutil.rmtree(temp_dir) 