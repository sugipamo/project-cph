import pytest
from src.env_resource.utils.path_utils import (
    get_workspace_path, get_contest_current_path, get_contest_env_path,
    get_contest_template_path, get_contest_temp_path, get_test_case_path,
    get_test_case_in_path, get_test_case_out_path
)
from pathlib import Path
from src.context.execution_context import ExecutionContext
import os
from src.context.resolver.config_resolver import create_config_root_from_dict


def make_local_config():
    env_json = {
        "cpp": {
            "workspace_path": "/tmp/workspace",
            "contest_current_path": "contests/abc001",
            "source_file_name": "main.cpp",
            "contest_env_path": "./env",
            "contest_template_path": "./template",
            "contest_temp_path": "./temp",
            "language_id": 1001,
            "commands": {},
            "env_types": {"local": {}}
        }
    }
    root = create_config_root_from_dict(env_json)
    return ExecutionContext(
        command_type="test",
        language="cpp",
        env_type="local",
        contest_name="abc001",
        problem_name="a",
        env_json=env_json,
        resolver=root
    )


def test_path_utils_functions():
    config = make_local_config()
    
    assert get_workspace_path(config.resolver, "cpp") == Path("/tmp/workspace")
    assert get_contest_current_path(config.resolver, "cpp") == Path("contests/abc001")
    assert get_contest_template_path(config.resolver, "cpp") == Path("./template")
    assert get_contest_temp_path(config.resolver, "cpp") == Path("./temp")
    
    contest_current = get_contest_current_path(config.resolver, "cpp")
    assert get_test_case_path(contest_current) == Path("contests/abc001/test")
    assert get_test_case_in_path(contest_current) == Path("contests/abc001/test/in")
    assert get_test_case_out_path(contest_current) == Path("contests/abc001/test/out")


def test_contest_env_path_auto_detection():
    # Test auto-detection functionality
    found = False
    cur = os.path.abspath(os.getcwd())
    while True:
        candidate = os.path.join(cur, "contest_env")
        if os.path.isdir(candidate):
            found = True
            break
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    
    if found:
        result = get_contest_env_path()
        assert result.exists()
    else:
        with pytest.raises(ValueError) as excinfo:
            get_contest_env_path()
        assert "contest_env_pathが自動検出できません" in str(excinfo.value)


def test_workspace_path_missing():
    env_json = {
        "cpp": {
            "contest_current_path": "contests/abc001",
            "source_file_name": "main.cpp",
            "contest_template_path": "./template",
            "contest_temp_path": "./temp",
        }
    }
    root = create_config_root_from_dict(env_json)
    
    with pytest.raises(TypeError) as excinfo:
        get_workspace_path(root, "cpp")
    assert "workspace_pathが設定されていません" in str(excinfo.value)


def test_contest_template_path_none():
    env_json = {
        "cpp": {
            "workspace_path": "/tmp/workspace",
            "contest_current_path": "contests/abc001",
            "contest_template_path": None,
            "contest_temp_path": "./temp",
        }
    }
    root = create_config_root_from_dict(env_json)
    
    with pytest.raises(TypeError) as excinfo:
        get_contest_template_path(root, "cpp")
    assert "contest_template_pathが設定されていません" in str(excinfo.value)


def test_contest_temp_path_none():
    env_json = {
        "cpp": {
            "workspace_path": "/tmp/workspace",
            "contest_current_path": "contests/abc001",
            "contest_template_path": "./template",
            "contest_temp_path": None,
        }
    }
    root = create_config_root_from_dict(env_json)
    
    with pytest.raises(TypeError) as excinfo:
        get_contest_temp_path(root, "cpp")
    assert "contest_temp_pathが設定されていません" in str(excinfo.value)


def test_get_source_file_name():
    env_json = {
        "python": {
            "source_file_name": "main.py"
        }
    }
    root = create_config_root_from_dict(env_json)
    
    from src.env_resource.utils.path_utils import get_source_file_name
    result = get_source_file_name(root, "python")
    assert result == "main.py"


def test_get_source_file_name_missing():
    env_json = {
        "python": {
            "workspace_path": "/tmp/workspace"
        }
    }
    root = create_config_root_from_dict(env_json)
    
    from src.env_resource.utils.path_utils import get_source_file_name
    with pytest.raises(ValueError) as excinfo:
        get_source_file_name(root, "python")
    assert "source_file_nameが設定されていません" in str(excinfo.value)


def test_get_contest_current_path_wrong_key():
    """Test case where resolve_best returns a node but with wrong key"""
    env_json = {
        "python": {
            "workspace_path": "/tmp/workspace",
            "other_path": "some_value"  # This will be matched but key is wrong
        }
    }
    root = create_config_root_from_dict(env_json)
    
    from src.env_resource.utils.path_utils import get_contest_current_path
    with pytest.raises(TypeError) as excinfo:
        get_contest_current_path(root, "python")
    assert "contest_current_pathが設定されていません" in str(excinfo.value)


def test_get_contest_env_path_no_parent():
    """Test contest_env path detection reaching root directory"""
    import os
    from unittest.mock import patch
    from src.env_resource.utils.path_utils import get_contest_env_path
    
    # Mock os.path.dirname to simulate reaching root
    with patch('os.path.dirname') as mock_dirname, \
         patch('os.path.isdir') as mock_isdir, \
         patch('os.path.abspath') as mock_abspath:
        
        mock_abspath.return_value = '/some/deep/path'
        mock_isdir.return_value = False  # No contest_env found
        mock_dirname.side_effect = ['/some/deep', '/some', '/', '/']  # Reach root
        
        with pytest.raises(ValueError) as excinfo:
            get_contest_env_path()
        assert "contest_env_pathが自動検出できませんでした" in str(excinfo.value)