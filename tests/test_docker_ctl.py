import pytest
from src.docker.ctl import DockerCtl

class DummyResult:
    def __init__(self, returncode=0, stdout='', stderr=''):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

def test_is_container_running(monkeypatch):
    def fake_run(cmd, **kwargs):
        if 'inspect' in cmd:
            return DummyResult(0, 'true')
        return DummyResult(1, '', 'error')
    monkeypatch.setattr('subprocess.run', fake_run)
    ctl = DockerCtl()
    assert ctl.is_container_running('foo') is True
    # エラー時
    def fake_run2(cmd, **kwargs):
        return DummyResult(1, '', 'error')
    monkeypatch.setattr('subprocess.run', fake_run2)
    assert ctl.is_container_running('foo') is False

def test_start_and_remove_container(monkeypatch):
    def fake_run(cmd, **kwargs):
        return DummyResult(0, 'ok', '')
    monkeypatch.setattr('subprocess.run', fake_run)
    ctl = DockerCtl()
    assert ctl.start_container('foo', 'img') is True
    assert ctl.remove_container('foo') is True

def test_exec_in_container(monkeypatch):
    def fake_run(cmd, **kwargs):
        if 'exec' in cmd:
            return DummyResult(0, 'out', 'err')
        return DummyResult(1, '', 'error')
    monkeypatch.setattr('subprocess.run', fake_run)
    ctl = DockerCtl()
    ok, out, err = ctl.exec_in_container('foo', ['ls'])
    assert ok and out == 'out' and err == 'err'
    # エラー時
    def fake_run2(cmd, **kwargs):
        return DummyResult(1, '', 'error')
    monkeypatch.setattr('subprocess.run', fake_run2)
    ok, out, err = ctl.exec_in_container('foo', ['ls'])
    assert not ok

def test_list_cph_containers(monkeypatch):
    def fake_run(cmd, **kwargs):
        if '-a' in cmd:
            return DummyResult(0, 'cph_foo\ncph_bar\nother', '')
        if 'inspect' in cmd:
            # 1つ目だけRunning
            if 'cph_foo' in cmd:
                return DummyResult(0, 'true', '')
            else:
                return DummyResult(0, 'false', '')
        return DummyResult(1, '', 'error')
    monkeypatch.setattr('subprocess.run', fake_run)
    ctl = DockerCtl()
    result = ctl.list_cph_containers()
    assert result == ['cph_foo'] 