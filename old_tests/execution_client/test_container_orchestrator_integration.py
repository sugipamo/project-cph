import pytest
import time
from src.execution_client.client.container import ContainerClient
from src.execution_client.container.orchestrator import ContainerOrchestrator

IMAGE = "alpine:latest"
REQUIREMENTS_MAP = { ("alpine", "latest"): IMAGE }

@pytest.fixture
def client():
    return ContainerClient()

@pytest.fixture
def orchestrator(client):
    return ContainerOrchestrator(REQUIREMENTS_MAP, max_workers=2, timeout=10, client=client)

def test_orchestrate_containers(orchestrator, client):
    # 事前クリーンアップ
    for name in client.list_containers(prefix="cph_test_"):
        try:
            client.remove_container(name)
        except Exception:
            pass
    requirements = [
        {"type": "test", "language": "alpine", "version": "latest", "count": 2},
    ]
    result = orchestrator.orchestrate(requirements)
    # 2つのコンテナが起動していること
    names = [c["name"] for c in result]
    running = [n for n in names if client.is_container_running(n)]
    assert len(running) == 2
    # orchestrateで不要なコンテナが消えること
    # 1つだけに減らす
    requirements2 = [
        {"type": "test", "language": "alpine", "version": "latest", "count": 1},
    ]
    orchestrator.orchestrate(requirements2)
    names2 = [f"cph_test_alpine_latest_{i+1}" for i in range(1)]
    for n in names2:
        assert client.is_container_running(n)
    # 2つ目は消えている
    assert not client.is_container_running("cph_test_alpine_latest_2")
    # 後始末
    for n in client.list_containers(prefix="cph_test_"):
        try:
            client.remove_container(n)
        except Exception:
            pass 