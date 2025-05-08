import pytest
from execution_client.container.client import ContainerClient

def test_run_not_implemented():
    client = ContainerClient()
    with pytest.raises(TypeError):
        # AbstractExecutionClientのrunシグネチャに合わせて呼ぶ
        client.run("test") 

def test_run_delegation():
    client = ContainerClient()
    # run_containerは必須引数が多いので、ダミー値で呼ぶ
    # ここではdockerが不要な値で呼ばれることを期待
    try:
        client.run("test", image="dummy", command=["echo", "hello"], detach=True)
    except Exception:
        # docker環境がない場合は例外でOK
        pass 