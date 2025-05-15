import os
import tempfile
import pytest
import time
import shutil
import uuid
from src.execution_client.client.container import ContainerClient

CONTAINER_NAME = "test_integration_container"
IMAGE = "alpine:latest"

@pytest.fixture
def client():
    return ContainerClient()

@pytest.fixture
def setup_container(client):
    # 事前にクリーンアップ
    try:
        client.remove_container(CONTAINER_NAME)
    except Exception:
        pass
    # 起動
    client.run_container(CONTAINER_NAME, IMAGE, command=["sleep", "10"])
    yield
    # 後始末
    try:
        client.stop_container(CONTAINER_NAME)
    except Exception:
        pass
    try:
        client.remove_container(CONTAINER_NAME)
    except Exception:
        pass

def test_run_container(client):
    client.run_container(CONTAINER_NAME, IMAGE, command=["echo", "hello"])
    # 1回だけのコマンドなので即終了
    assert not client.is_container_running(CONTAINER_NAME)
    client.remove_container(CONTAINER_NAME)

def test_exec_in_container(client, setup_container):
    proc = client.exec_in_container(CONTAINER_NAME, ["echo", "abc"])
    assert proc.returncode == 0
    assert proc.stdout.strip() == "abc"

def test_copy_to_and_from_container(client, setup_container):
    # .temp配下にランダムなディレクトリを作成
    temp_dir = os.path.join(".temp", f"test_container_{uuid.uuid4().hex}")
    os.makedirs(temp_dir, exist_ok=True)
    try:
        src_file = os.path.join(temp_dir, "hostfile.txt")
        with open(src_file, "w") as f:
            f.write("testdata")
        assert os.path.exists(src_file)
        # コンテナにコピー
        client.copy_to_container(CONTAINER_NAME, src_file, "/tmp/containerfile.txt")
        time.sleep(0.2)
        # コンテナからホストにコピー
        dst_file = os.path.join(temp_dir, "hostfile2.txt")
        client.copy_from_container(CONTAINER_NAME, "/tmp/containerfile.txt", dst_file)
        with open(dst_file, "r") as f:
            data = f.read()
        assert data == "testdata"
    finally:
        shutil.rmtree(temp_dir)

def test_stop_and_remove_container(client):
    client.run_container(CONTAINER_NAME, IMAGE, command=["sleep", "10"])
    assert client.is_container_running(CONTAINER_NAME)
    client.stop_container(CONTAINER_NAME)
    assert not client.is_container_running(CONTAINER_NAME)
    client.remove_container(CONTAINER_NAME)
    assert not client.is_container_running(CONTAINER_NAME) 