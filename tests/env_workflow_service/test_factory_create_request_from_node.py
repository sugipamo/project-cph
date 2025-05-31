import pytest
from unittest.mock import Mock, MagicMock
from src.env_factories.unified_factory import UnifiedCommandRequestFactory
from src.context.resolver.config_node import ConfigNode
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.shell.shell_request import ShellRequest
from src.operations.python.python_request import PythonRequest
from src.operations.docker.docker_request import DockerRequest


class TestUnifiedFactoryCreateRequestFromNode:
    """UnifiedCommandRequestFactoryのcreate_request_from_nodeメソッドのテスト"""
    
    def setup_method(self):
        """テスト前の共通セットアップ"""
        self.mock_controller = Mock()
        self.mock_controller.env_context = Mock()
        self.mock_controller.env_context.env_type = "local"
        self.mock_controller.format_string = lambda x: x  # パススルー
        self.mock_controller.format_value = lambda val, node: val  # パススルー
        self.mock_operations = Mock()
        
    def create_config_node(self, key, value, next_nodes=None):
        """テスト用のConfigNodeを作成"""
        node = ConfigNode(key, value)
        if next_nodes:
            node.next_nodes = next_nodes
        else:
            node.next_nodes = []
        return node
        
    def test_python_factory_create_request_from_node(self):
        """UnifiedCommandRequestFactory (Python)のテスト"""
        factory = UnifiedCommandRequestFactory(self.mock_controller)
        
        # コードを含むnode
        node = self.create_config_node(
            'python_step',
            {
                'type': 'python',
                'cmd': ['import sys', 'print(sys.version)'],
                'cwd': '/test/dir',
                'show_output': False
            }
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, PythonRequest)
        assert request.code_or_file == ['import sys', 'print(sys.version)']
        assert request.cwd == '/test/dir'
        assert request.show_output is False
        
    def test_shell_factory_create_request_from_node(self):
        """UnifiedCommandRequestFactory (Shell)のテスト"""
        factory = UnifiedCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'shell_step',
            {
                'type': 'shell',
                'cmd': ['ls', '-la'],
                'cwd': '/home/user',
                'show_output': True,
                'allow_failure': True
            }
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, ShellRequest)
        assert request.cmd == ['ls', '-la']
        assert request.cwd == '/home/user'
        assert request.show_output is True
        assert request.allow_failure is True
        
    def test_copy_factory_create_request_from_node(self):
        """UnifiedCommandRequestFactory (Copy)のテスト"""
        factory = UnifiedCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'copy_step',
            {
                'type': 'copy',
                'cmd': ['/src/file.txt', '/dst/file.txt']
            }
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.COPY
        assert request.path == '/src/file.txt'
        assert request.dst_path == '/dst/file.txt'
        # FileRequest doesn't have allow_failure or show_output attributes
        
    def test_build_factory_create_request_from_node(self):
        """UnifiedCommandRequestFactory (Build)のテスト"""
        factory = UnifiedCommandRequestFactory(self.mock_controller)
        
        # Build is actually a Docker request in the unified factory
        node = self.create_config_node(
            'build_step',
            {'type': 'build', 'dockerfile': 'FROM ubuntu:20.04'}
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, DockerRequest)
        
    def test_mkdir_factory_create_request_from_node(self):
        """UnifiedCommandRequestFactory (Mkdir)のテスト"""
        factory = UnifiedCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'mkdir_step',
            {
                'type': 'mkdir',
                'target': '/new/directory'
            }
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.MKDIR
        assert request.path == '/new/directory'
        
    def test_mkdir_factory_missing_target(self):
        """Mkdirでtargetが欠けている場合"""
        factory = UnifiedCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'mkdir_step', 
            {'type': 'mkdir'}
        )
        
        with pytest.raises(ValueError):
            factory.create_request_from_node(node)
            
    def test_touch_factory_create_request_from_node(self):
        """UnifiedCommandRequestFactory (Touch)のテスト"""
        factory = UnifiedCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'touch_step',
            {
                'type': 'touch',
                'target': '/new/file.txt'
            }
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.TOUCH
        assert request.path == '/new/file.txt'
        
    def test_remove_factory_create_request_from_node(self):
        """UnifiedCommandRequestFactory (Remove)のテスト"""
        factory = UnifiedCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'remove_step',
            {
                'type': 'remove',
                'target': '/old/file.txt'
            }
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.REMOVE
        assert request.path == '/old/file.txt'
        
    def test_rmtree_factory_create_request_from_node(self):
        """UnifiedCommandRequestFactory (Rmtree)のテスト"""
        factory = UnifiedCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'rmtree_step',
            {
                'type': 'rmtree',
                'target': '/old/directory'
            }
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.RMTREE
        assert request.path == '/old/directory'
        
    def test_move_factory_create_request_from_node(self):
        """UnifiedCommandRequestFactory (Move)のテスト"""
        factory = UnifiedCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'move_step',
            {
                'type': 'move',
                'cmd': ['/src/file.txt', '/dst/file.txt']
            }
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.MOVE
        assert request.path == '/src/file.txt'
        assert request.dst_path == '/dst/file.txt'
        
    def test_movetree_factory_create_request_from_node(self):
        """UnifiedCommandRequestFactory (Movetree)のテスト"""
        factory = UnifiedCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'movetree_step',
            {
                'type': 'movetree',
                'cmd': ['/src/dir', '/dst/dir']
            }
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.COPYTREE  # Movetree uses COPYTREE
        assert request.path == '/src/dir'
        assert request.dst_path == '/dst/dir'
        
    def test_oj_factory_create_request_from_node_local(self):
        """UnifiedCommandRequestFactory (OJ)のテスト"""
        factory = UnifiedCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'oj_step',
            {
                'type': 'oj',
                'cmd': ['oj', 'download', 'https://example.com'],
                'cwd': '/work',
                'show_output': True,
                'allow_failure': False
            }
        )
        
        request = factory.create_request_from_node(node)
        
        # OJ uses ShellRequest
        assert isinstance(request, ShellRequest)
        assert request.cmd == ['oj', 'download', 'https://example.com']
        assert request.cwd == '/work'
        assert request.show_output is True
        assert request.allow_failure is False
        
    def test_factory_with_nested_config_nodes(self):
        """ネストしたConfigNodeを持つファクトリーのテスト"""
        factory = UnifiedCommandRequestFactory(self.mock_controller)
        
        # cmdフィールドのConfigNodeを作成
        cmd_nodes = [
            self.create_config_node(0, 'echo'),
            self.create_config_node(1, '{message}')
        ]
        cmd_node = self.create_config_node('cmd', ['echo', '{message}'], cmd_nodes)
        
        # cwdフィールドのConfigNode
        cwd_node = self.create_config_node('cwd', '{workspace_path}')
        
        # メインのnode
        node = self.create_config_node(
            'shell_step',
            {
                'type': 'shell',
                'cmd': ['echo', '{message}'],
                'cwd': '{workspace_path}'
            },
            [cmd_node, cwd_node]
        )
        
        # factoryを作成してformat_valueをモック化
        factory = UnifiedCommandRequestFactory(self.mock_controller)
        factory.format_value = MagicMock(side_effect=lambda val, node: f"formatted_{val}")
        
        request = factory.create_request_from_node(node)
        
        # format_valueが適切に呼ばれたことを確認
        assert isinstance(request, ShellRequest)
        # Verify that format_value was called
        assert factory.format_value.call_count >= 3  # Should be called for each cmd arg and cwd
        assert request.cmd == ['formatted_echo', 'formatted_{message}']
        assert request.cwd == 'formatted_{workspace_path}'
        
    def test_factory_invalid_node_value(self):
        """無効なnode valueの場合のエラーテスト"""
        factory = UnifiedCommandRequestFactory(self.mock_controller)
        
        # valueがNoneの場合
        node = self.create_config_node('python_step', None)
        
        with pytest.raises(ValueError, match="Invalid node value"):
            factory.create_request_from_node(node)
            
        # valueがdictでない場合
        node = self.create_config_node('python_step', "invalid")
        
        with pytest.raises(ValueError, match="Invalid node value"):
            factory.create_request_from_node(node)