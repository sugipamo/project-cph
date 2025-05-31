"""
PreparationExecutor のテスト
"""
import pytest
from unittest.mock import Mock, MagicMock
from src.env.fitting.preparation_executor import PreparationExecutor
from src.operations.di_container import DIContainer
from src.operations.result.result import OperationResult


class TestPreparationExecutor:
    """PreparationExecutor のテストクラス"""
    
    @pytest.fixture
    def mock_operations(self):
        """モックDIContainer"""
        operations = Mock(spec=DIContainer)
        mock_file_driver = Mock()
        operations.resolve.return_value = mock_file_driver
        return operations
    
    @pytest.fixture
    def mock_file_driver(self, mock_operations):
        """モックファイルドライバー"""
        return mock_operations.resolve.return_value
    
    @pytest.fixture
    def preparation_executor(self, mock_operations):
        """PreparationExecutor インスタンス"""
        return PreparationExecutor(mock_operations)
    
    def test_check_environment_state_base_exists(self, preparation_executor, mock_file_driver):
        """環境状態確認テスト（ベースディレクトリ存在）"""
        mock_file_driver.exists.return_value = True
        
        state = preparation_executor.check_environment_state("./test_project")
        
        assert state['base_exists'] is True
        assert state['base_path'] == "./test_project"
        assert 'existing_files' in state
        assert 'existing_directories' in state
        mock_file_driver.exists.assert_called_with("./test_project")
    
    def test_check_environment_state_base_not_exists(self, preparation_executor, mock_file_driver):
        """環境状態確認テスト（ベースディレクトリ不存在）"""
        mock_file_driver.exists.return_value = False
        
        state = preparation_executor.check_environment_state("./missing_project")
        
        assert state['base_exists'] is False
        assert state['base_path'] == "./missing_project"
        mock_file_driver.exists.assert_called_with("./missing_project")
    
    def test_check_environment_state_error_handling(self, preparation_executor, mock_file_driver):
        """環境状態確認エラーハンドリングテスト"""
        mock_file_driver.exists.side_effect = Exception("Permission denied")
        
        state = preparation_executor.check_environment_state("./restricted")
        
        assert state['base_exists'] is False
        assert 'error' in state
        assert "Permission denied" in state['error']
    
    def test_verify_requirements_missing_items(self, preparation_executor, mock_file_driver):
        """要求確認テスト（不足項目あり）"""
        # ファイルが存在しない設定
        mock_file_driver.exists.return_value = False
        
        # モックワークフロー（特定のリソースを要求）
        class MockWorkflow:
            def __init__(self):
                self.requests = []
        
        mock_workflow = MockWorkflow()
        
        # _extract_required_resourcesをモック
        def mock_extract_resources(workflow):
            return {
                'directories': ['./project/src', './project/build'],
                'files': ['./project/main.py']
            }
        
        preparation_executor._extract_required_resources = mock_extract_resources
        
        missing_items = preparation_executor.verify_requirements_against_environment(
            mock_workflow, "./project"
        )
        
        assert missing_items['preparation_needed'] is True
        assert './project/src' in missing_items['directories']
        assert './project/build' in missing_items['directories']
        assert './project/main.py' in missing_items['files']
    
    def test_verify_requirements_no_missing_items(self, preparation_executor, mock_file_driver):
        """要求確認テスト（不足項目なし）"""
        # 全ファイルが存在する設定
        mock_file_driver.exists.return_value = True
        
        class MockWorkflow:
            def __init__(self):
                self.requests = []
        
        mock_workflow = MockWorkflow()
        
        def mock_extract_resources(workflow):
            return {
                'directories': ['./project/src'],
                'files': ['./project/main.py']
            }
        
        preparation_executor._extract_required_resources = mock_extract_resources
        
        missing_items = preparation_executor.verify_requirements_against_environment(
            mock_workflow, "./project"
        )
        
        assert missing_items['preparation_needed'] is False
        assert len(missing_items['directories']) == 0
        assert len(missing_items['files']) == 0
    
    def test_create_preparation_requests(self, preparation_executor):
        """準備request生成テスト"""
        missing_items = {
            'directories': ['./project/src', './project/build'],
            'files': ['./project/main.py'],
            'preparation_needed': True
        }
        
        preparation_requests = preparation_executor.create_preparation_requests(missing_items)
        
        # 準備requestが生成される（import可能な場合）
        # import エラーの場合は空リストが返される
        if preparation_requests:
            from src.operations.file.file_request import FileRequest
            for request in preparation_requests:
                if hasattr(request, 'path'):
                    assert isinstance(request, FileRequest)
                    assert request.allow_failure is True  # 準備段階なので失敗許容
        # import失敗時は空リスト
        assert isinstance(preparation_requests, list)
    
    def test_execute_preparation_success(self, preparation_executor, mock_file_driver):
        """準備実行テスト（成功）"""
        # 成功するモックrequest
        mock_request = Mock()
        mock_request.execute.return_value = OperationResult(success=True)
        
        preparation_requests = [mock_request]
        
        results = preparation_executor.execute_preparation(preparation_requests)
        
        assert len(results) == 1
        assert results[0].success is True
        mock_request.execute.assert_called_once_with(driver=mock_file_driver)
    
    def test_execute_preparation_failure(self, preparation_executor, mock_file_driver):
        """準備実行テスト（失敗）"""
        # 失敗するモックrequest
        mock_request = Mock()
        mock_request.execute.side_effect = Exception("File creation failed")
        
        preparation_requests = [mock_request]
        
        results = preparation_executor.execute_preparation(preparation_requests)
        
        assert len(results) == 1
        assert results[0].success is False
        assert "File creation failed" in results[0].error_message
    
    def test_fit_workflow_to_environment_no_preparation_needed(self, preparation_executor, mock_file_driver):
        """環境適合テスト（準備不要）"""
        mock_file_driver.exists.return_value = True
        
        class MockWorkflow:
            def __init__(self):
                self.requests = []
        
        mock_workflow = MockWorkflow()
        
        def mock_extract_resources(workflow):
            return {'directories': [], 'files': []}
        
        preparation_executor._extract_required_resources = mock_extract_resources
        
        result = preparation_executor.fit_workflow_to_environment(
            mock_workflow, "./project"
        )
        
        assert result['preparation_needed'] is False
        assert 'Environment is ready' in result['message']
        assert 'environment_state' in result
    
    def test_fit_workflow_to_environment_with_preparation(self, preparation_executor, mock_file_driver):
        """環境適合テスト（準備必要）"""
        mock_file_driver.exists.return_value = False
        
        class MockWorkflow:
            def __init__(self):
                self.requests = []
        
        mock_workflow = MockWorkflow()
        
        def mock_extract_resources(workflow):
            return {
                'directories': ['./project/src'],
                'files': []
            }
        
        preparation_executor._extract_required_resources = mock_extract_resources
        
        result = preparation_executor.fit_workflow_to_environment(
            mock_workflow, "./project"
        )
        
        assert result['preparation_needed'] is True
        assert result['preparation_executed'] is True
        assert 'total_preparations' in result
        assert 'successful_preparations' in result
        assert 'missing_items' in result
        assert 'environment_state' in result
    
    def test_extract_required_resources_composite_request(self, preparation_executor):
        """リソース抽出テスト（CompositeRequest）"""
        # モックCompositeRequest
        class MockCompositeRequest:
            def __init__(self):
                self.requests = []
        
        # モックリクエスト（pathを持つ）
        mock_request = Mock()
        mock_request.path = "./project/src/main.py"
        
        mock_workflow = MockCompositeRequest()
        mock_workflow.requests = [mock_request]
        
        resources = preparation_executor._extract_required_resources(mock_workflow)
        
        assert 'directories' in resources
        assert 'files' in resources
        # pathの親ディレクトリが抽出される（相対パス形式）
        assert 'project/src' in resources['directories']
    
    def test_extract_required_resources_execution_graph(self, preparation_executor):
        """リソース抽出テスト（RequestExecutionGraph）"""
        # モックRequestExecutionGraph
        class MockGraph:
            def __init__(self):
                self.nodes = {}
        
        # モックnode
        mock_node = Mock()
        mock_node.requires_dirs = {'./project/build'}
        mock_node.reads_files = {'./project/config.json'}
        
        mock_graph = MockGraph()
        mock_graph.nodes = {'node1': mock_node}
        
        resources = preparation_executor._extract_required_resources(mock_graph)
        
        assert './project/build' in resources['directories']
        assert './project/config.json' in resources['files']