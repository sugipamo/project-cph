import pytest
from unittest.mock import Mock, MagicMock
from src.env.run_workflow_builder import RunWorkflowBuilder
from src.env.run_step import RunSteps, ShellRunStep, CopyRunStep, PythonRunStep
from src.context.resolver.config_node import ConfigNode
from src.operations.composite.composite_request import CompositeRequest
from src.operations.composite.driver_bound_request import DriverBoundRequest
from src.operations.file.file_request import FileRequest
from src.operations.shell.shell_request import ShellRequest
from src.operations.python.python_request import PythonRequest


class TestRunWorkflowBuilder:
    """RunWorkflowBuilderのテスト"""
    
    def setup_method(self):
        """テスト前の共通セットアップ"""
        self.mock_controller = Mock()
        self.mock_controller.env_context = Mock()
        self.mock_controller.env_context.env_type = "local"
        self.mock_controller.format_string = lambda x: x  # パススルー
        
        self.mock_operations = Mock()
        self.mock_file_driver = Mock()
        self.mock_operations.resolve.return_value = self.mock_file_driver
        
        self.builder = RunWorkflowBuilder(self.mock_controller, self.mock_operations)
        
    def create_config_node(self, key, value, next_nodes=None):
        """テスト用のConfigNodeを作成"""
        node = ConfigNode(key, value)
        if next_nodes:
            node.next_nodes = next_nodes
        else:
            node.next_nodes = []
        return node
        
    def test_build_from_nodes_single_shell_request(self):
        """単一のShellRequestを含むワークフローのビルド"""
        node = self.create_config_node(
            'shell',
            {
                'type': 'shell',
                'cmd': ['echo', 'Hello World']
            }
        )
        
        composite_request = self.builder.build_from_nodes([node])
        
        assert isinstance(composite_request, CompositeRequest)
        assert len(composite_request.requests) == 1
        assert isinstance(composite_request.requests[0], ShellRequest)
        assert composite_request.requests[0].cmd == ['echo', 'Hello World']
        
    def test_build_from_nodes_file_request_wrapped(self):
        """FileRequestがDriverBoundRequestでラップされることを確認"""
        node = self.create_config_node(
            'copy',
            {
                'type': 'copy',
                'cmd': ['/src/file.txt', '/dst/file.txt']
            }
        )
        
        composite_request = self.builder.build_from_nodes([node])
        
        assert isinstance(composite_request, CompositeRequest)
        assert len(composite_request.requests) == 1
        assert isinstance(composite_request.requests[0], DriverBoundRequest)
        assert isinstance(composite_request.requests[0].req, FileRequest)
        assert composite_request.requests[0].driver == self.mock_file_driver
        
    def test_build_from_nodes_multiple_requests(self):
        """複数のリクエストを含むワークフローのビルド"""
        nodes = [
            self.create_config_node(
                'shell',
                {
                    'type': 'shell',
                    'cmd': ['mkdir', '-p', '/test']
                }
            ),
            self.create_config_node(
                'copy',
                {
                    'type': 'copy',
                    'cmd': ['/src/file.txt', '/test/file.txt']
                }
            ),
            self.create_config_node(
                'python',
                {
                    'type': 'python',
                    'cmd': ['print("Task completed")']
                }
            )
        ]
        
        composite_request = self.builder.build_from_nodes(nodes)
        
        assert isinstance(composite_request, CompositeRequest)
        assert len(composite_request.requests) == 3
        
        # 1つ目: ShellRequest
        assert isinstance(composite_request.requests[0], ShellRequest)
        
        # 2つ目: DriverBoundRequest (FileRequestをラップ)
        assert isinstance(composite_request.requests[1], DriverBoundRequest)
        assert isinstance(composite_request.requests[1].req, FileRequest)
        
        # 3つ目: PythonRequest
        assert isinstance(composite_request.requests[2], PythonRequest)
        
    def test_build_from_nodes_with_allow_failure(self):
        """allow_failure属性が正しく伝播されることを確認"""
        node = self.create_config_node(
            'movetree',
            {
                'type': 'movetree',
                'cmd': ['/src/dir', '/dst/dir'],
                'allow_failure': True,
                'show_output': False
            }
        )
        
        composite_request = self.builder.build_from_nodes([node])
        
        assert len(composite_request.requests) == 1
        driver_bound_request = composite_request.requests[0]
        assert isinstance(driver_bound_request, DriverBoundRequest)
        assert driver_bound_request.allow_failure is True
        assert driver_bound_request.show_output is False
        
    def test_build_from_nodes_skip_unknown_type(self):
        """未知のtypeを持つnodeはスキップされる"""
        nodes = [
            self.create_config_node(
                'shell',
                {
                    'type': 'shell',
                    'cmd': ['echo', 'Valid']
                }
            ),
            self.create_config_node(
                'unknown',
                {
                    'type': 'unknown_type',
                    'cmd': ['unknown', 'command']
                }
            )
        ]
        
        composite_request = self.builder.build_from_nodes(nodes)
        
        # unknown_typeはスキップされるので、リクエストは1つだけ
        assert len(composite_request.requests) == 1
        assert isinstance(composite_request.requests[0], ShellRequest)
        
    def test_build_from_nodes_empty_list(self):
        """空のnodeリストからのビルド"""
        composite_request = self.builder.build_from_nodes([])
        
        assert isinstance(composite_request, CompositeRequest)
        assert len(composite_request.requests) == 0
        
    def test_build_legacy_method(self):
        """従来のbuildメソッドのテスト"""
        run_steps = RunSteps([
            ShellRunStep(cmd=['echo', 'Step 1']),
            CopyRunStep(cmd=['/src/file.txt', '/dst/file.txt']),
            PythonRunStep(cmd=['print("Step 3")'])
        ])
        
        composite_request = self.builder.build(run_steps)
        
        assert isinstance(composite_request, CompositeRequest)
        assert len(composite_request.requests) == 3
        
        # ShellRequest
        assert isinstance(composite_request.requests[0], ShellRequest)
        
        # DriverBoundRequest (FileRequestをラップ)
        assert isinstance(composite_request.requests[1], DriverBoundRequest)
        
        # PythonRequest
        assert isinstance(composite_request.requests[2], PythonRequest)
        
    def test_build_from_nodes_with_nested_config(self):
        """ネストしたConfigNodeを持つnodeのビルド"""
        cmd_nodes = [
            self.create_config_node(0, 'cp'),
            self.create_config_node(1, '{source_file}'),
            self.create_config_node(2, '{dest_file}')
        ]
        cmd_node = self.create_config_node('cmd', ['cp', '{source_file}', '{dest_file}'], cmd_nodes)
        
        node = self.create_config_node(
            'shell',
            {
                'type': 'shell',
                'cmd': ['cp', '{source_file}', '{dest_file}'],
                'cwd': '{workspace_path}'
            },
            [cmd_node]
        )
        
        composite_request = self.builder.build_from_nodes([node])
        
        assert len(composite_request.requests) == 1
        assert isinstance(composite_request.requests[0], ShellRequest)
        # フォーマット処理はファクトリー内で行われる
        
    def test_file_driver_resolution(self):
        """file_driverが正しく解決されることを確認"""
        node = self.create_config_node(
            'mkdir',
            {
                'type': 'mkdir',
                'target': '/new/directory'
            }
        )
        
        composite_request = self.builder.build_from_nodes([node])
        
        # resolveメソッドが'file_driver'で呼ばれたことを確認
        self.mock_operations.resolve.assert_called_with('file_driver')
        
        # DriverBoundRequestにfile_driverが設定されていることを確認
        assert composite_request.requests[0].driver == self.mock_file_driver