import pytest
from src.execution_client.utils import build_command

def test_build_command_basic():
    assert build_command('python', ['main.py']) == ['python', 'main.py']

def test_build_command_empty_args():
    assert build_command('ls', []) == ['ls']

def test_build_command_multiple_args():
    assert build_command('cp', ['a.txt', 'b.txt', '-r']) == ['cp', 'a.txt', 'b.txt', '-r'] 