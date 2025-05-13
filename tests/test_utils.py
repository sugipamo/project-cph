from src.execution_client.utils import build_command

def test_build_command():
    assert build_command('python3', ['main.py']) == ['python3', 'main.py']
    assert build_command('echo', ['hello', 'world']) == ['echo', 'hello', 'world']
    assert build_command('ls', []) == ['ls'] 