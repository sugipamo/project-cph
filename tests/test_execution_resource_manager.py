from src.execution_env.execution_resource_manager import LocalResourceManager

# LocalResourceManagerのテスト
def test_local_resource_manager():
    mgr = LocalResourceManager()
    assert mgr.adjust_resources({}, 'c', 'p', 'py') == []
    assert mgr.get_test_containers() == ['local_test']
    assert mgr.get_ojtools_container() is None
    assert mgr.update_info() is None 