import pytest
import time
import uuid
from src.execution_client.client.container import ContainerClient

@pytest.fixture(scope="module")
def client():
    return ContainerClient()

@pytest.fixture
def unique_container_name():
    # テストごとにユニークな名前
    return f"testcontainer-cph-{uuid.uuid4().hex[:8]}"

@pytest.fixture
def running_container(client, unique_container_name):
    # テスト用のalpineコンテナを起動
    client.run_container(unique_container_name, "alpine", ["sleep", "60"])
    # 起動まで少し待つ
    for _ in range(10):
        if client.is_container_running(unique_container_name):
            break
        time.sleep(0.2)
    yield unique_container_name
    # 終了後に必ず削除
    try:
        client.remove_container(unique_container_name)
    except Exception:
        pass

def test_run_container_and_is_running(client, unique_container_name):
    client.run_container(name=unique_container_name, image="alpine", command=["sleep", "10"], timeout=10)
    for _ in range(10):
        if client.is_container_running(unique_container_name):
            break
        time.sleep(0.2)
    assert client.is_container_running(unique_container_name)
    assert unique_container_name in client.list_containers()
    # 後始末
    client.remove_container(unique_container_name)

def test_exec_in_container(client, running_container):
    out_proc = client.exec_in_container(running_container, ["echo", "hello"], timeout=10)
    assert out_proc.returncode == 0
    assert "hello" in (out_proc.stdout or "")

def test_stop_and_remove_container(client, running_container):
    stopped = client.stop_container(running_container)
    assert stopped
    for _ in range(10):
        if not client.is_container_running(running_container):
            break
    assert not client.is_container_running(running_container)
    removed = client.remove_container(running_container)
    assert removed
    assert running_container not in client.list_containers() 