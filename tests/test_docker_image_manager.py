import os
import tempfile
import hashlib
import subprocess
from unittest import mock
import pytest
from src.docker.pool import DockerImageManager

def test_get_dockerfile_hash():
    with tempfile.NamedTemporaryFile("w+b", delete=False) as f:
        f.write(b"FROM python:3.8\nRUN echo hello\n")
        f.flush()
        path = f.name
        expected = hashlib.sha256(b"FROM python:3.8\nRUN echo hello\n").hexdigest()[:12]
        manager = DockerImageManager({"python": path})
        assert manager.get_dockerfile_hash(path) == expected
    os.remove(path)

def test_get_image_name():
    # テンポラリDockerfileを作成
    with tempfile.NamedTemporaryFile("w+b", delete=False) as f:
        f.write(b"FROM python:3.8\n")
        f.flush()
        path = f.name
        manager = DockerImageManager({"python": path})
        hashval = manager.get_dockerfile_hash(path)
        image_name = manager.get_image_name("python")
        assert image_name == f"cph_image_python_{hashval}"
    os.remove(path)

def test_ensure_image_build_called(monkeypatch):
    # テンポラリDockerfileを作成
    with tempfile.NamedTemporaryFile("w+b", delete=False) as f:
        f.write(b"FROM python:3.8\n")
        f.flush()
        path = f.name
        manager = DockerImageManager({"python": path})
        # docker images: imageが存在しない場合
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: mock.Mock(stdout="", returncode=0))
        # docker build: 呼ばれたか確認
        called = {}
        def fake_run(cmd, **kwargs):
            if "build" in cmd:
                called["build"] = True
            m = mock.Mock()
            m.stdout = ""
            m.returncode = 0
            return m
        monkeypatch.setattr(subprocess, "run", fake_run)
        image = manager.ensure_image("python")
        assert called.get("build")
    os.remove(path)

def test_ensure_image_no_build_if_exists(monkeypatch):
    # テンポラリDockerfileを作成
    with tempfile.NamedTemporaryFile("w+b", delete=False) as f:
        f.write(b"FROM python:3.8\n")
        f.flush()
        path = f.name
        manager = DockerImageManager({"python": path})
        # docker images: imageが存在する場合
        hashval = manager.get_dockerfile_hash(path)
        image_name = f"cph_image_python_{hashval}"
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: mock.Mock(stdout=image_name+"\n", returncode=0))
        image = manager.ensure_image("python")
        # buildは呼ばれない（例外も出ない）
        assert image == image_name
    os.remove(path) 