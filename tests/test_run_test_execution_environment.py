import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.execution_env.run_test_execution_environment import RunTestExecutionEnvironment
from src.execution_env.handlers import HANDLERS

@pytest.fixture
def dummy_upm():
    upm = MagicMock()
    upm.info_json.return_value = "dummy.json"
    return upm

@pytest.fixture
def dummy_exec_manager():
    em = MagicMock()
    em.client = MagicMock()
    return em

@pytest.fixture
def dummy_file_ops():
    fo = MagicMock()
    fo.prepare_source_code.return_value = "src.py"
    fo.prepare_test_cases.return_value = "test_dir"
    fo.collect_test_cases.return_value = (["a.in"], ["a.out"])
    fo.download_testcases = MagicMock()
    return fo

@pytest.fixture
def dummy_resource_manager():
    rm = MagicMock()
    rm.adjust_resources.return_value = ["cont1"]
    rm.get_test_containers.return_value = ["cont1"]
    return rm

@pytest.fixture
def dummy_handler():
    h = MagicMock()
    h.build.return_value = (True, "ok", "")
    h.run.return_value = (True, "out", "")
    h.config = MagicMock()
    h.env_config = MagicMock()
    return h

@pytest.fixture
def dummy_env(dummy_upm, dummy_exec_manager, dummy_file_ops, dummy_resource_manager, dummy_handler):
    env = RunTestExecutionEnvironment(
        upm=dummy_upm,
        exec_manager=dummy_exec_manager,
        env_type="docker",
        file_operator=None,
        file_ops=dummy_file_ops,
        resource_manager=dummy_resource_manager,
        ctl=MagicMock()
    )
    # handler取得をpatch
    env.get_handler = MagicMock(return_value=dummy_handler)
    return env

@patch('src.execution_env.run_test_execution_environment.get_handler')
def test_build(mock_get_handler, dummy_env, dummy_handler):
    mock_get_handler.return_value = dummy_handler
    ok, out, err = dummy_env.build("python", "cont1", "src.py")
    assert ok

@patch('src.execution_env.run_test_execution_environment.get_handler')
def test_prepare_source_code(mock_get_handler, dummy_env, dummy_file_ops, dummy_handler):
    mock_get_handler.return_value = dummy_handler
    result = dummy_env.prepare_source_code("abc", "a", "python")
    assert result == "src.py"

@patch('src.execution_env.run_test_execution_environment.get_handler')
def test_prepare_test_cases(mock_get_handler, dummy_env, dummy_file_ops, dummy_handler):
    mock_get_handler.return_value = dummy_handler
    result = dummy_env.prepare_test_cases("abc", "a")
    assert result == "test_dir"

@patch('src.execution_env.run_test_execution_environment.get_handler')
def test_run_test_case(mock_get_handler, dummy_env, dummy_handler):
    mock_get_handler.return_value = dummy_handler
    ok, out, err, attempt = dummy_env.run_test_case("python", "cont1", "a.in", "src.py")
    assert ok
    assert attempt == 1

@patch('src.execution_env.run_test_execution_environment.get_handler')
def test_run_test_cases(mock_get_handler, dummy_env, dummy_handler):
    mock_get_handler.return_value = dummy_handler
    dummy_env.build = MagicMock(return_value=(True, "", ""))
    results = dummy_env.run_test_cases("src.py", ["a.in"], "python")
    assert isinstance(results, list)
    assert results[0]["name"] == "a.in"

def test_run_test_all_cases(dummy_env, dummy_file_ops, dummy_handler):
    dummy_env.prepare_source_code = MagicMock(return_value="src.py")
    dummy_env.prepare_test_cases = MagicMock(return_value="test_dir")
    dummy_env.file_ops.collect_test_cases = MagicMock(return_value=( ["a.in"], ["a.out"] ))
    dummy_env.build = MagicMock(return_value=(True, "", ""))
    dummy_env.resource_manager.adjust_resources = MagicMock()
    dummy_env.run_test_cases = MagicMock(return_value=[{"result": (0, "out", ""), "expected": "out", "name": "a.in"}])
    with patch('src.execution_env.run_test_execution_environment.get_handler', return_value=dummy_handler):
        results = dummy_env.run_test_all_cases("abc", "a", "python")
    assert isinstance(results, list)
    assert results[0]["name"] == "a.in"

def test_all_handlers_have_language_and_env_type():
    seen = set()
    for key, handler_cls in HANDLERS.items():
        # language_name, env_typeがNoneや空でないこと
        assert getattr(handler_cls, 'language_name', None), f"{handler_cls.__name__} に language_name がありません"
        assert getattr(handler_cls, 'env_type', None), f"{handler_cls.__name__} に env_type がありません"
        # 重複がないこと
        assert key not in seen, f"HANDLERSのキー {key} が重複しています"
        seen.add(key) 