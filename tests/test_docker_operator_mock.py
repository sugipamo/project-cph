from src.docker_operator import MockDockerOperator
import pytest

@pytest.mark.asyncio
async def test_run_records_call():
    op = MockDockerOperator()
    rc, out, err = await op.run('img', ['echo', 'hi'], {'/host': '/cont'}, '/cont', None)
    assert rc == 0 and out == 'mock-stdout' and err == 'mock-stderr'
    assert op.calls[0][0] == 'run'

@pytest.mark.asyncio
async def test_build_records_call():
    op = MockDockerOperator()
    rc, out, err = await op.build('Dockerfile', 'img:tag')
    assert rc == 0 and out == 'mock-stdout' and err == 'mock-stderr'
    assert op.calls[0][0] == 'build'

@pytest.mark.asyncio
async def test_exec_records_call():
    op = MockDockerOperator()
    rc, out, err = await op.exec('cont_id', ['ls', '/'])
    assert rc == 0 and out == 'mock-stdout' and err == 'mock-stderr'
    assert op.calls[0][0] == 'exec'

@pytest.mark.asyncio
async def test_run_oj_records_call():
    op = MockDockerOperator()
    rc, out, err = await op.run_oj(['login'], {'/h': '/c'}, '/w', False)
    assert rc == 0 and out == 'mock-stdout' and err == 'mock-stderr'
    assert op.calls[0][0] == 'run_oj'

def test_run_oj_download_records_call():
    op = MockDockerOperator()
    ok = op.run_oj_download('url', 'cookie', 'testdir')
    assert ok is True
    assert op.calls[0][0] == 'run_oj_download' 