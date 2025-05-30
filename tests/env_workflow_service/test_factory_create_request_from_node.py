import pytest
from unittest.mock import Mock, MagicMock
from src.env.factory.python_command_request_factory import PythonCommandRequestFactory
from src.env.factory.shell_command_request_factory import ShellCommandRequestFactory
from src.env.factory.copy_command_request_factory import CopyCommandRequestFactory
from src.env.factory.build_command_request_factory import BuildCommandRequestFactory
from src.env.factory.mkdir_command_request_factory import MkdirCommandRequestFactory
from src.env.factory.touch_command_request_factory import TouchCommandRequestFactory
from src.env.factory.remove_command_request_factory import RemoveCommandRequestFactory
from src.env.factory.rmtree_command_request_factory import RmtreeCommandRequestFactory
from src.env.factory.move_command_request_factory import MoveCommandRequestFactory
from src.env.factory.movetree_command_request_factory import MoveTreeCommandRequestFactory
from src.env.factory.oj_command_request_factory import OjCommandRequestFactory
from src.context.resolver.config_node import ConfigNode
from src.operations.file.file_request import FileRequest
from src.operations.shell.shell_request import ShellRequest
from src.operations.python.python_request import PythonRequest
from src.operations.constants.operation_type import FileOpType


class TestFactoryCreateRequestFromNode:
    """各ファクトリーのcreate_request_from_nodeメソッドのテスト"""
    
    def setup_method(self):
        """テスト前の共通セットアップ"""
        self.mock_controller = Mock()
        self.mock_controller.env_context = Mock()
        self.mock_controller.env_context.env_type = "local"
        self.mock_controller.format_string = lambda x: x  # パススルー
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
        """PythonCommandRequestFactoryのテスト"""
        factory = PythonCommandRequestFactory(self.mock_controller)
        
        # コードを含むnode
        node = self.create_config_node(
            'python_step',
            {
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
        """ShellCommandRequestFactoryのテスト"""
        factory = ShellCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'shell_step',
            {
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
        """CopyCommandRequestFactoryのテスト"""
        factory = CopyCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'copy_step',
            {
                'cmd': ['/src/file.txt', '/dst/file.txt'],
                'allow_failure': True,
                'show_output': False
            }
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, FileRequest)
        assert request.op_type == FileOpType.COPY
        assert request.path == '/src/file.txt'
        assert request.dst_path == '/dst/file.txt'
        assert request.allow_failure is True
        assert request.show_output is False
        
    def test_build_factory_create_request_from_node(self):
        """BuildCommandRequestFactoryのテスト"""
        factory = BuildCommandRequestFactory(self.mock_controller)
        
        # カスタムビルドコマンド
        node = self.create_config_node(
            'build_step',
            {'cmd': ['cargo', 'build', '--release']}
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, ShellRequest)
        assert request.cmd == ['cargo', 'build', '--release']
        
        # デフォルトのmakeコマンド
        node_default = self.create_config_node('build_step', {})
        request_default = factory.create_request_from_node(node_default)
        
        assert request_default.cmd == ['make']
        
    def test_mkdir_factory_create_request_from_node(self):
        """MkdirCommandRequestFactoryのテスト"""
        factory = MkdirCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'mkdir_step',
            {'target': '/new/directory'}
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, FileRequest)
        assert request.op_type == FileOpType.MKDIR
        assert request.path == '/new/directory'
        
    def test_mkdir_factory_missing_target(self):
        """MkdirCommandRequestFactoryでtargetが欠けている場合"""
        factory = MkdirCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node('mkdir_step', {})
        
        with pytest.raises(ValueError, match="target is required for mkdir operation"):
            factory.create_request_from_node(node)
            
    def test_touch_factory_create_request_from_node(self):
        """TouchCommandRequestFactoryのテスト"""
        factory = TouchCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'touch_step',
            {'target': '/new/file.txt'}
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, FileRequest)
        assert request.op_type == FileOpType.TOUCH
        assert request.path == '/new/file.txt'
        
    def test_remove_factory_create_request_from_node(self):
        """RemoveCommandRequestFactoryのテスト"""
        factory = RemoveCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'remove_step',
            {'target': '/old/file.txt'}
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, FileRequest)
        assert request.op_type == FileOpType.REMOVE
        assert request.path == '/old/file.txt'
        
    def test_rmtree_factory_create_request_from_node(self):
        """RmtreeCommandRequestFactoryのテスト"""
        factory = RmtreeCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'rmtree_step',
            {'target': '/old/directory'}
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, FileRequest)
        assert request.op_type == FileOpType.RMTREE
        assert request.path == '/old/directory'
        
    def test_move_factory_create_request_from_node(self):
        """MoveCommandRequestFactoryのテスト"""
        factory = MoveCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'move_step',
            {'cmd': ['/src/file.txt', '/dst/file.txt']}
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, FileRequest)
        assert request.op_type == FileOpType.MOVE
        assert request.path == '/src/file.txt'
        assert request.dst_path == '/dst/file.txt'
        
    def test_movetree_factory_create_request_from_node(self):
        """MoveTreeCommandRequestFactoryのテスト"""
        factory = MoveTreeCommandRequestFactory(self.mock_controller)
        
        node = self.create_config_node(
            'movetree_step',
            {
                'cmd': ['/src/dir', '/dst/dir'],
                'allow_failure': True,
                'show_output': True
            }
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, FileRequest)
        assert request.op_type == FileOpType.MOVE
        assert request.path == '/src/dir'
        assert request.dst_path == '/dst/dir'
        assert request.allow_failure is True
        assert request.show_output is True
        
    def test_oj_factory_create_request_from_node_local(self):
        """OjCommandRequestFactory (local環境)のテスト"""
        factory = OjCommandRequestFactory(self.mock_controller, self.mock_operations)
        
        node = self.create_config_node(
            'oj_step',
            {
                'cmd': ['oj', 'download', 'https://example.com'],
                'cwd': '/work',
                'show_output': True,
                'allow_failure': False
            }
        )
        
        request = factory.create_request_from_node(node)
        
        assert isinstance(request, ShellRequest)
        assert request.cmd == ['oj', 'download', 'https://example.com']
        assert request.cwd == '/work'
        assert request.show_output is True
        assert request.allow_failure is False
        
    def test_factory_with_nested_config_nodes(self):
        """ネストしたConfigNodeを持つファクトリーのテスト"""
        factory = ShellCommandRequestFactory(self.mock_controller)
        
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
                'cmd': ['echo', '{message}'],
                'cwd': '{workspace_path}'
            },
            [cmd_node, cwd_node]
        )
        
        # format_valueをモック化
        factory.format_value = MagicMock(side_effect=lambda val, node: f"formatted_{val}")
        
        request = factory.create_request_from_node(node)
        
        # format_valueが適切なnodeで呼ばれたことを確認
        assert factory.format_value.call_count == 3  # echo, {message}, {workspace_path}
        assert request.cmd == ['formatted_echo', 'formatted_{message}']
        assert request.cwd == 'formatted_{workspace_path}'
        
    def test_factory_invalid_node_value(self):
        """無効なnode valueの場合のエラーテスト"""
        factory = PythonCommandRequestFactory(self.mock_controller)
        
        # valueがNoneの場合
        node = self.create_config_node('python_step', None)
        
        with pytest.raises(ValueError, match="Invalid node value"):
            factory.create_request_from_node(node)
            
        # valueがdictでない場合
        node = self.create_config_node('python_step', "invalid")
        
        with pytest.raises(ValueError, match="Invalid node value"):
            factory.create_request_from_node(node)