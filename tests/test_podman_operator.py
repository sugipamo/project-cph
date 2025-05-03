import pytest
import pytest_asyncio
from src.podman_operator import PodmanOperator, LocalPodmanOperator, MockPodmanOperator

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

@pytest.mark.asyncio
async def test_mock_podman_operator():
    op = MockPodmanOperator()
    rc1, out1, err1 = await op.run('img', ['echo', 'hi'], {'/host': '/cont'}, '/cont')
    rc2, out2, err2 = await op.build('Dockerfile', 'img:tag')
    rc3, out3, err3 = await op.exec('cont_id', ['ls', '/'])
    assert op.calls == [
        ('run', 'img', ['echo', 'hi'], {'/host': '/cont'}, '/cont', False),
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