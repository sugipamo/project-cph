import pytest
import pytest_asyncio
from src.podman_operator import PodmanOperator, LocalPodmanOperator, MockPodmanOperator
import asyncio
import types
import sys

class DummyLocalPodmanOperator(LocalPodmanOperator):
    def __init__(self):
        self.calls = []
    async def run(self, image, command, volumes=None, workdir=None, interactive=False):
        self.calls.append(('run', image, command, volumes, workdir, interactive))
        return 0, 'dummy-stdout', 'dummy-stderr'
    async def build(self, dockerfile, tag):
        self.calls.append(('build', dockerfile, tag))
        return 0, 'dummy-stdout', 'dummy-stderr'
    async def exec(self, container, command):
        self.calls.append(('exec', container, command))
        return 0, 'dummy-stdout', 'dummy-stderr'

class DummyProc:
    def __init__(self, returncode=0, stdout=b'dummy-out', stderr=b'dummy-err'):
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr
    async def communicate(self):
        return self._stdout, self._stderr
    async def wait(self):
        return self.returncode

@pytest.mark.asyncio
async def test_mock_podman_operator():
    op = MockPodmanOperator()
    rc1, out1, err1 = await op.run('img', ['echo', 'hi'], {'/host': '/cont'}, '/cont', None)
    rc2, out2, err2 = await op.build('Dockerfile', 'img:tag')
    rc3, out3, err3 = await op.exec('cont_id', ['ls', '/'])
    assert op.calls == [
        ('run', 'img', ['echo', 'hi'], {'/host': '/cont'}, '/cont', None, False),
        ('build', 'Dockerfile', 'img:tag'),
        ('exec', 'cont_id', ['ls', '/'])
    ]
    assert rc1 == 0 and out1 == 'mock-stdout' and err1 == 'mock-stderr'
    assert rc2 == 0 and out2 == 'mock-stdout' and err2 == 'mock-stderr'
    assert rc3 == 0 and out3 == 'mock-stdout' and err3 == 'mock-stderr'

@pytest.mark.asyncio
async def test_local_podman_operator_interface():
    op = DummyLocalPodmanOperator()
    rc1, out1, err1 = await op.run('img', ['echo', 'hi'], {'/host': '/cont'}, '/cont')
    rc2, out2, err2 = await op.build('Dockerfile', 'img:tag')
    rc3, out3, err3 = await op.exec('cont_id', ['ls', '/'])
    assert op.calls == [
        ('run', 'img', ['echo', 'hi'], {'/host': '/cont'}, '/cont', False),
        ('build', 'Dockerfile', 'img:tag'),
        ('exec', 'cont_id', ['ls', '/'])
    ]
    assert rc1 == 0 and out1 == 'dummy-stdout' and err1 == 'dummy-stderr'
    assert rc2 == 0 and out2 == 'dummy-stdout' and err2 == 'dummy-stderr'
    assert rc3 == 0 and out3 == 'dummy-stdout' and err3 == 'dummy-stderr'

def test_podman_operator_is_abstract():
    with pytest.raises(TypeError):
        PodmanOperator()  # ABCは直接インスタンス化できない 

@pytest.mark.asyncio
async def test_mockpodmanoperator_run():
    op = MockPodmanOperator()
    rc, out, err = await op.run("img", ["echo", "hi"], {"/host": "/cont"}, "/work", True)
    assert rc == 0
    assert out == 'mock-stdout'
    assert err == 'mock-stderr'
    assert op.calls[0][0] == 'run'

@pytest.mark.asyncio
async def test_mockpodmanoperator_build():
    op = MockPodmanOperator()
    rc, out, err = await op.build("Dockerfile", "tag")
    assert rc == 0
    assert out == 'mock-stdout'
    assert err == 'mock-stderr'
    assert op.calls[0][0] == 'build'

@pytest.mark.asyncio
async def test_mockpodmanoperator_exec():
    op = MockPodmanOperator()
    rc, out, err = await op.exec("cont", ["ls", "/"])
    assert rc == 0
    assert out == 'mock-stdout'
    assert err == 'mock-stderr'
    assert op.calls[0][0] == 'exec'

@pytest.mark.asyncio
async def test_mockpodmanoperator_run_oj():
    op = MockPodmanOperator()
    rc, out, err = await op.run_oj(["login"], {"/h": "/c"}, "/w", False)
    assert rc == 0
    assert out == 'mock-stdout'
    assert err == 'mock-stderr'
    assert op.calls[0][0] == 'run_oj'

def test_localpodmanoperator_run(monkeypatch):
    async def dummy_create_subprocess_exec(*args, **kwargs):
        if kwargs.get('stdin') == sys.stdin:
            return DummyProc(returncode=123)
        return DummyProc(returncode=0, stdout=b'out', stderr=b'err')
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', dummy_create_subprocess_exec)
    op = LocalPodmanOperator()
    # 非対話モード
    rc, out, err = asyncio.run(op.run('img', ['ls'], {'/h': '/c'}, '/w', None, interactive=False))
    assert rc == 0
    assert out == 'out'
    assert err == 'err'
    # 対話モード
    rc2, out2, err2 = asyncio.run(op.run('img', ['ls'], {'/h': '/c'}, '/w', None, interactive=True))
    assert rc2 == 123
    assert out2 is None and err2 is None

def test_localpodmanoperator_build(monkeypatch):
    async def dummy_create_subprocess_exec(*args, **kwargs):
        return DummyProc(returncode=0, stdout=b'build-out', stderr=b'build-err')
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', dummy_create_subprocess_exec)
    op = LocalPodmanOperator()
    rc, out, err = asyncio.run(op.build('Dockerfile', 'tag'))
    assert rc == 0
    assert out == 'build-out'
    assert err == 'build-err'

def test_localpodmanoperator_exec(monkeypatch):
    async def dummy_create_subprocess_exec(*args, **kwargs):
        return DummyProc(returncode=0, stdout=b'exec-out', stderr=b'exec-err')
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', dummy_create_subprocess_exec)
    op = LocalPodmanOperator()
    rc, out, err = asyncio.run(op.exec('cont', ['ls']))
    assert rc == 0
    assert out == 'exec-out'
    assert err == 'exec-err'

def test_localpodmanoperator_run_oj(monkeypatch):
    async def dummy_create_subprocess_exec(*args, **kwargs):
        return DummyProc(returncode=0, stdout=b'oj-out', stderr=b'oj-err')
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', dummy_create_subprocess_exec)
    op = LocalPodmanOperator()
    rc, out, err = asyncio.run(op.run_oj(['login'], {'/h': '/c'}, '/w', interactive=False))
    assert rc == 0
    assert out == 'oj-out'
    assert err == 'oj-err' 