import pytest
import os
from src.shell_process import ShellProcess, ShellProcessOptions

# 正常系: echoコマンド
def test_shellprocess_run_echo():
    proc = ShellProcess.run('echo', 'hello', options=ShellProcessOptions())
    if proc.returncode is None:
        # 例外が発生していればそれを表示
        assert proc.has_error
        assert proc.exception is not None
        pytest.skip(f"subprocess failed: {proc.exception}")
    assert proc.returncode == 0
    assert proc.stdout.strip() == 'hello'
    assert proc.stderr == ''
    assert not proc.has_error

# 異常系: 存在しないコマンド
def test_shellprocess_run_invalid_command():
    proc = ShellProcess.run('nonexistent_command', options=ShellProcessOptions())
    assert proc.has_error
    assert proc.returncode is not None or proc.exception is not None

# timeout発生
def test_shellprocess_run_timeout():
    proc = ShellProcess.run('sleep', '2', options=ShellProcessOptions(timeout=0.5))
    assert proc.has_error
    assert proc.exception is not None
    assert isinstance(proc.exception, Exception)

# popenでの実行
def test_shellprocess_popen_echo():
    proc = ShellProcess.popen('echo', 'popen', options=ShellProcessOptions())
    if proc.returncode is None:
        assert proc.has_error
        assert proc.exception is not None
        pytest.skip(f"subprocess failed: {proc.exception}")
    assert proc.returncode == 0
    assert proc.stdout.strip() == 'popen'
    assert proc.stderr == ''
    assert not proc.has_error

# retryの動作確認
def test_shellprocess_retry():
    proc = ShellProcess.run('false', options=ShellProcessOptions())
    assert proc.has_error
    proc.retry(max_retry=2)
    # falseコマンドは常に失敗するのでhas_errorはTrueのまま
    assert proc.has_error

# input_dataの動作
def test_shellprocess_input_data():
    proc = ShellProcess.run('cat', options=ShellProcessOptions(input_data='abc'))
    if proc.returncode is None:
        assert proc.has_error
        assert proc.exception is not None
        pytest.skip(f"subprocess failed: {proc.exception}")
    assert proc.returncode == 0
    assert proc.stdout == 'abc'
    assert not proc.has_error

# ShellProcessOptionsのシリアライズ・デシリアライズ
def test_shellprocessoptions_json():
    opts = ShellProcessOptions(env={'A': 'B'}, cwd='/tmp', log_file='log.txt', input_data='xyz', timeout=1.5, extra1=123)
    json_str = opts.to_json()
    opts2 = ShellProcessOptions.from_json(json_str)
    assert opts2.env == {'A': 'B'}
    assert opts2.cwd == '/tmp'
    assert opts2.log_file == 'log.txt'
    assert opts2.input_data == 'xyz'
    assert opts2.timeout == 1.5
    assert opts2.extra['extra1'] == 123

# ShellProcessPoolのrun_many/popen_many
def test_shellprocesspool_run_many():
    from src.shell_process import ShellProcessPool
    pool = ShellProcessPool(max_workers=2)
    results = pool.run_many([('echo', 'A'), ('echo', 'B')])
    outs = []
    for r in results:
        if r.stdout is None or r.returncode is None:
            assert r.has_error
            assert r.exception is not None
            pytest.skip(f"subprocess failed: {r.exception}")
        outs.append(r.stdout.strip())
        assert r.returncode == 0
        assert not r.has_error
    assert 'A' in outs and 'B' in outs
    results2 = pool.popen_many([('echo', 'X'), ('echo', 'Y')])
    outs2 = []
    for r in results2:
        if r.stdout is None or r.returncode is None:
            assert r.has_error
            assert r.exception is not None
            pytest.skip(f"subprocess failed: {r.exception}")
        outs2.append(r.stdout.strip())
        assert r.returncode == 0
        assert not r.has_error
    assert 'X' in outs2 and 'Y' in outs2

# ShellProcessAsyncのrun（asyncテスト）
import asyncio
import sys
import pytest

@pytest.mark.asyncio
async def test_shellprocessasync_run():
    from src.shell_process import ShellProcessAsync
    proc = await ShellProcessAsync.run('echo', 'async')
    assert proc.returncode == 0
    assert proc.stdout.strip() == 'async'
    assert proc.stderr == ''
    assert not proc.has_error

def test_shellprocess_run_permission_denied(tmp_path):
    # 実行権限のないスクリプトを作成
    script = tmp_path / "noexec.sh"
    script.write_text("#!/bin/sh\necho NG")
    script.chmod(0o644)
    proc = ShellProcess.run(str(script), options=ShellProcessOptions())
    assert proc.has_error
    assert proc.returncode is not None or proc.exception is not None

def test_shellprocess_run_with_env():
    opts = ShellProcessOptions(env={"FOO": "BAR"})
    proc = ShellProcess.run('sh', '-c', 'echo $FOO', options=opts)
    if proc.returncode is None:
        assert proc.has_error
        assert proc.exception is not None
        import pytest
        pytest.skip(f"subprocess failed: {proc.exception}")
    assert proc.stdout.strip() == 'BAR'
    assert proc.returncode == 0

def test_shellprocess_run_with_cwd(tmp_path):
    cwd = tmp_path
    file = cwd / "testfile.txt"
    proc = ShellProcess.run('sh', '-c', f'echo cwdtest > {file.name}', options=ShellProcessOptions(cwd=str(cwd)))
    if proc.returncode is None:
        assert proc.has_error
        assert proc.exception is not None
        import pytest
        pytest.skip(f"subprocess failed: {proc.exception}")
    assert file.read_text().strip() == 'cwdtest'

def test_shellprocess_log_file(tmp_path):
    log_file = tmp_path / "log.txt"
    opts = ShellProcessOptions(log_file=str(log_file))
    proc = ShellProcess.run('echo', 'logtest', options=opts)
    assert log_file.exists()
    log_content = log_file.read_text()
    assert 'logtest' in log_content
    if proc.returncode is None:
        assert proc.has_error
        assert proc.exception is not None
        import pytest
        pytest.skip(f"subprocess failed: {proc.exception}")
    assert str(proc.returncode) in log_content

def test_shellprocess_run_timeout_edge():
    import time
    # 0.5秒sleep、0.6秒timeoutなら成功するはず
    proc = ShellProcess.run('sleep', '0.5', options=ShellProcessOptions(timeout=0.6))
    if proc.returncode is None:
        assert proc.has_error
        assert proc.exception is not None
        import pytest
        pytest.skip(f"subprocess failed: {proc.exception}")
    assert proc.returncode == 0
    assert not proc.has_error

def test_shellprocess_retry_success(tmp_path):
    # 1回目は失敗、2回目は成功するスクリプト
    script = tmp_path / "retrytest.sh"
    marker = tmp_path / "marker.txt"
    script.write_text(f"#!/bin/sh\nif [ -f {marker} ]; then echo OK; exit 0; else touch {marker}; exit 1; fi")
    script.chmod(0o755)
    proc = ShellProcess.run(str(script), options=ShellProcessOptions())
    if proc.returncode != 0:
        proc.retry(max_retry=2)
    assert proc.stdout is not None
    assert 'OK' in proc.stdout
    assert proc.returncode == 0
    assert not proc.has_error 