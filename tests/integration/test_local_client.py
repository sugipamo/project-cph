import pytest
from src.execution_client.client.local import LocalAsyncClient

def test_run_detach_false_input(tmp_path):
    client = LocalAsyncClient()
    script = tmp_path / 'echo.py'
    with open(script, 'w') as f:
        f.write('print(input())')
    # 1回目
    result = client.run('test1', command=['python3', str(script.name)], detach=False, input='foo\n', cwd=tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == 'foo'
    # 2回目（同じnameで再実行できること）
    result2 = client.run('test1', command=['python3', str(script.name)], detach=False, input='bar\n', cwd=tmp_path)
    assert result2.returncode == 0
    assert result2.stdout.strip() == 'bar'

def test_run_detach_true_and_remove(tmp_path):
    client = LocalAsyncClient()
    script = tmp_path / 'sleep.py'
    with open(script, 'w') as f:
        f.write('import time; time.sleep(1); print("done")')
    # detach=Trueで実行
    result = client.run('sleep1', command=['python3', str(script)], detach=True)
    assert 'popen' in result.extra
    # プロセスが登録されている
    assert client.is_running('sleep1')
    # removeでプロセスが消える
    client.remove('sleep1')
    assert not client.is_running('sleep1')

def test_run_detach_true_input(tmp_path):
    client = LocalAsyncClient()
    script = tmp_path / 'echo.py'
    with open(script, 'w') as f:
        f.write('print(input())')
    # detach=Trueでinputをextraに含めて返す（実際の実行はしない）
    result = client.run('test2', command=['python3', str(script.name)], detach=True, input='baz\n', cwd=tmp_path)
    assert 'popen' in result.extra
    assert result.extra['input'] == 'baz\n'
    # プロセスをkillしてクリーンアップ
    client.remove('test2') 