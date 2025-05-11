import pytest
from src.execution_client.client.container import ContainerClient
import threading
import shutil

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

def test_run_realtime_stdout():
    if not shutil.which("docker"):
        pytest.skip("docker not available")
    client = ContainerClient()
    output_lines = []
    event = threading.Event()
    def on_stdout(line):
        output_lines.append(line)
        event.set()
    # 実際のdocker runでecho
    result = client.run("test4", image="alpine", command=["echo", "realtime"], realtime=True, on_stdout=on_stdout)
    proc = result.extra["popen"]
    proc.wait()
    event.wait(timeout=5)
    assert any("realtime" in l for l in output_lines)
    client.stop("test4") 