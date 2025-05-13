import pytest
from unittest.mock import MagicMock, AsyncMock
from src.commands.command_test import CommandTest

@pytest.fixture
def dummy_test_env():
    env = MagicMock()
    env.prepare_source_code.return_value = "src.py"
    env.prepare_test_cases.return_value = "test_dir"
    env.file_ops.collect_test_cases.return_value = (["a.in"], ["a.out"])
    env.resource_manager.get_test_containers.return_value = ["cont1"]
    env.upm.to_container_path.side_effect = lambda x: f"/container/{x}"
    env.build.return_value = (True, "ok", "")
    env.run_test_cases.return_value = [
        {"result": (0, "out", ""), "expected": "out", "time": 0.1, "name": "a.in", "in_file": "a.in", "container": None, "attempt": 1}
    ]
    env.run_test_all_cases = AsyncMock(return_value=[{"result": (0, "out", ""), "expected": "out", "time": 0.1, "name": "a.in", "in_file": "a.in", "container": None, "attempt": 1}])
    return env

@pytest.fixture
def dummy_file_manager():
    fm = MagicMock()
    return fm

@pytest.mark.asyncio
def test_prepare_and_collect(dummy_file_manager, dummy_test_env):
    ct = CommandTest(dummy_file_manager, dummy_test_env)
    src, test_dir = ct.prepare_test_environment("abc", "a", "python")
    assert src == "src.py"
    assert test_dir == "test_dir"
    cases = ct.collect_test_cases("test_dir")
    assert cases == (["a.in"], ["a.out"])

def test_get_test_containers_from_info(dummy_file_manager, dummy_test_env):
    ct = CommandTest(dummy_file_manager, dummy_test_env)
    assert ct.get_test_containers_from_info() == ["cont1"]

def test_to_container_path(dummy_file_manager, dummy_test_env):
    ct = CommandTest(dummy_file_manager, dummy_test_env)
    assert ct.to_container_path("foo.txt") == "/container/foo.txt"

def test_build_in_container(dummy_file_manager, dummy_test_env):
    ct = CommandTest(dummy_file_manager, dummy_test_env)
    assert ct.build_in_container(None, None, None, None) == (True, "ok", "")

def test_collect_test_result(dummy_file_manager, dummy_test_env):
    ct = CommandTest(dummy_file_manager, dummy_test_env)
    res = ct.collect_test_result(True, "out", "", "out", "a.in", "cont1", 1)
    assert res["result"] == (0, "out", "")
    assert res["expected"] == "out"
    assert res["name"] == "a.in"
    assert res["container"] == "cont1"
    assert res["attempt"] == 1

def test_is_all_ac(dummy_file_manager, dummy_test_env):
    ct = CommandTest(dummy_file_manager, dummy_test_env)
    results = [
        {"result": (0, "ok", ""), "expected": "ok"},
        {"result": (0, "ok", ""), "expected": "ok"}
    ]
    assert ct.is_all_ac(results)
    results = [
        {"result": (1, "ng", ""), "expected": "ok"}
    ]
    assert not ct.is_all_ac(results)

@pytest.mark.asyncio
async def test_run_test_cases_and_print(dummy_file_manager, dummy_test_env, capsys):
    ct = CommandTest(dummy_file_manager, dummy_test_env)
    results = await ct.run_test_cases("src.py", ["a.in"], "python")
    assert isinstance(results, list)
    ct.print_test_results(results)
    out = capsys.readouterr().out
    assert "a.in" in out

@pytest.mark.asyncio
async def test_run_test_and_return(dummy_file_manager, dummy_test_env):
    ct = CommandTest(dummy_file_manager, dummy_test_env)
    await ct.run_test("abc", "a", "python")
    results = await ct.run_test_return_results("abc", "a", "python")
    assert isinstance(results, list) 