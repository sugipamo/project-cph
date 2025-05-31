"""
統合ファクトリ+ビルダーパターンによる効率的な実装
現在の14個のファクトリクラスを統合する設計例
"""

from enum import Enum, auto
from abc import ABC, abstractmethod
from typing import Dict, Type, Any, List, Optional

# 現在のインポート（実装時に必要）
# from src.env_factories.base.factory import BaseCommandRequestFactory
# from src.operations.shell.shell_request import ShellRequest
# from src.operations.docker.docker_request import DockerRequest, DockerOpType
# from src.operations.file.file_request import FileRequest
from src.operations.file.file_op_type import FileOpType
# from src.operations.python.python_request import PythonRequest


class CommandType(Enum):
    """コマンド種別定義"""
    # コマンド実行系
    SHELL = auto()
    DOCKER = auto()
    BUILD = auto()
    PYTHON = auto()
    OJ = auto()
    
    # ファイル操作系
    COPY = auto()
    MKDIR = auto()
    TOUCH = auto()
    REMOVE = auto()
    RMTREE = auto()
    MOVE = auto()
    MOVETREE = auto()


class ConfigNodeProcessor:
    """ConfigNode処理の共通ロジック"""
    
    @staticmethod
    def find_child_node(node, key: str):
        """指定されたキーの子ノードを検索"""
        for child in node.next_nodes:
            if child.key == key:
                return child
        return None
    
    @staticmethod
    def format_command_array(factory, node, cmd: List[str]) -> List[str]:
        """コマンド配列のフォーマット処理（重複削除）"""
        cmd_node = ConfigNodeProcessor.find_child_node(node, 'cmd')
        formatted_cmd = []
        
        if cmd_node and cmd_node.next_nodes:
            # cmd配列の各要素のnodeを使ってフォーマット
            for i, arg in enumerate(cmd):
                arg_node = None
                for child in cmd_node.next_nodes:
                    if child.key == i:
                        arg_node = child
                        break
                if arg_node:
                    formatted_cmd.append(factory.format_value(arg, arg_node))
                else:
                    formatted_cmd.append(factory.format_value(arg, node))
        else:
            # nodeが見つからない場合は親nodeを使用
            formatted_cmd = [factory.format_value(arg, node) for arg in cmd]
        
        return formatted_cmd
    
    @staticmethod
    def format_single_field(factory, node, field_name: str, value: Any) -> Any:
        """単一フィールドのフォーマット処理（重複削除）"""
        field_node = ConfigNodeProcessor.find_child_node(node, field_name)
        return factory.format_value(value, field_node if field_node else node)


class CommandRequestBuilder(ABC):
    """コマンドリクエストビルダーの基底クラス"""
    
    def __init__(self, factory):
        self.factory = factory
        self.reset()
    
    def reset(self):
        """ビルダーの状態をリセット"""
        self._cmd = []
        self._cwd = None
        self._show_output = True
        self._allow_failure = False
        self._target = None
        self._source = None
        self._dst_path = None
        return self
    
    def set_command(self, cmd: List[str]):
        """コマンドを設定"""
        self._cmd = cmd
        return self
    
    def set_working_directory(self, cwd: str):
        """作業ディレクトリを設定"""
        self._cwd = cwd
        return self
    
    def set_output_options(self, show_output: bool = True, allow_failure: bool = False):
        """出力オプションを設定"""
        self._show_output = show_output
        self._allow_failure = allow_failure
        return self
    
    def set_file_paths(self, target: str = None, source: str = None, dst_path: str = None):
        """ファイルパスを設定"""
        self._target = target
        self._source = source
        self._dst_path = dst_path
        return self
    
    @abstractmethod
    def build_from_run_step(self, run_step):
        """RunStepからリクエストを構築"""
        pass
    
    @abstractmethod
    def build_from_node(self, node):
        """ConfigNodeからリクエストを構築"""
        pass
    
    def _validate_and_format_common_fields(self, node_or_step, is_node: bool = True):
        """共通フィールドの検証とフォーマット"""
        if is_node:
            # ConfigNodeの場合
            if not node_or_step.value or not isinstance(node_or_step.value, dict):
                raise ValueError(f"Invalid node value for {self.__class__.__name__}")
        else:
            # RunStepの場合  
            expected_type = self._get_expected_run_step_type()
            if expected_type and not isinstance(node_or_step, expected_type):
                raise TypeError(f"{self.__class__.__name__} expects {expected_type.__name__}, got {type(node_or_step).__name__}")
    
    def _get_expected_run_step_type(self):
        """期待するRunStepタイプを返す（サブクラスで実装）"""
        return None


class ShellRequestBuilder(CommandRequestBuilder):
    """ShellRequestビルダー"""
    
    def build_from_run_step(self, run_step):
        """ShellRunStepからShellRequestを構築"""
        self._validate_and_format_common_fields(run_step, is_node=False)
        
        cmd = [self.factory.format_string(arg) for arg in run_step.cmd]
        cwd = self.factory.format_string(run_step.cwd) if getattr(run_step, 'cwd', None) else None
        
        # ShellRequest作成（実装時にimport必要）
        # request = ShellRequest(cmd, cwd=cwd, show_output=getattr(run_step, 'show_output', True))
        # return self.factory.set_request_attributes(request, run_step)
        
        # デモ用の疑似コード
        return f"ShellRequest(cmd={cmd}, cwd={cwd})"
    
    def build_from_node(self, node):
        """ConfigNodeからShellRequestを構築"""
        self._validate_and_format_common_fields(node, is_node=True)
        
        cmd = node.value.get('cmd', [])
        cwd = node.value.get('cwd')
        
        # 共通処理を使用してフォーマット
        formatted_cmd = ConfigNodeProcessor.format_command_array(self.factory, node, cmd)
        formatted_cwd = ConfigNodeProcessor.format_single_field(self.factory, node, 'cwd', cwd) if cwd else None
        
        # ShellRequest作成（実装時にimport必要）
        # request = ShellRequest(formatted_cmd, cwd=formatted_cwd, 
        #                       show_output=node.value.get('show_output', True))
        # return self.factory.set_request_attributes(request, node)
        
        # デモ用の疑似コード
        return f"ShellRequest(cmd={formatted_cmd}, cwd={formatted_cwd})"


class FileRequestBuilder(CommandRequestBuilder):
    """FileRequestビルダー（複数のファイル操作を統合）"""
    
    def __init__(self, factory, file_op_type):
        super().__init__(factory)
        self.file_op_type = file_op_type  # FileOpType.COPY, MKDIR, etc.
    
    def build_from_run_step(self, run_step):
        """RunStepからFileRequestを構築"""
        self._validate_and_format_common_fields(run_step, is_node=False)
        
        if self.file_op_type.name in ['COPY', 'MOVE', 'MOVETREE']:
            # 2つのパラメータが必要
            if len(run_step.cmd) < 2:
                raise ValueError(f"{self.file_op_type.name}: cmdにはsrcとdstの2つが必要です")
            src = self.factory.format_string(run_step.cmd[0])
            dst = self.factory.format_string(run_step.cmd[1])
            # request = FileRequest(self.file_op_type, src, dst_path=dst)
            return f"FileRequest({self.file_op_type.name}, src={src}, dst={dst})"
        else:
            # 1つのパラメータが必要（target）
            target = self.factory.format_string(getattr(run_step, 'target', run_step.cmd[0] if run_step.cmd else None))
            if not target:
                raise ValueError(f"target is required for {self.file_op_type.name} operation")
            # request = FileRequest(self.file_op_type, target)
            return f"FileRequest({self.file_op_type.name}, target={target})"
    
    def build_from_node(self, node):
        """ConfigNodeからFileRequestを構築"""
        self._validate_and_format_common_fields(node, is_node=True)
        
        if self.file_op_type.name in ['COPY', 'MOVE', 'MOVETREE']:
            # 2つのパラメータが必要
            cmd = node.value.get('cmd', [])
            if len(cmd) < 2:
                raise ValueError(f"{self.file_op_type.name}: cmdにはsrcとdstの2つが必要です")
            
            src = ConfigNodeProcessor.format_single_field(self.factory, node, 'cmd[0]', cmd[0])
            dst = ConfigNodeProcessor.format_single_field(self.factory, node, 'cmd[1]', cmd[1])
            return f"FileRequest({self.file_op_type.name}, src={src}, dst={dst})"
        else:
            # 1つのパラメータが必要
            target = node.value.get('target')
            if not target:
                raise ValueError(f"target is required for {self.file_op_type.name} operation")
            
            formatted_target = ConfigNodeProcessor.format_single_field(self.factory, node, 'target', target)
            return f"FileRequest({self.file_op_type.name}, target={formatted_target})"


class DockerRequestBuilder(CommandRequestBuilder):
    """DockerRequestビルダー"""
    
    def build_from_run_step(self, run_step):
        """ShellRunStepからDockerRequestを構築"""
        self._validate_and_format_common_fields(run_step, is_node=False)
        
        cmd = [self.factory.format_string(arg) for arg in run_step.cmd]
        # dockerfile_text = getattr(self.factory.controller.env_context, 'dockerfile', None)
        # container_name = get_container_name(self.factory.controller.env_context.language, dockerfile_text)
        
        cwd = self.factory.format_string(run_step.cwd) if getattr(run_step, 'cwd', None) else None
        options = {}
        if cwd:
            options["workdir"] = cwd
        
        # return DockerRequest(DockerOpType.EXEC, container=container_name, 
        #                     command=" ".join(cmd), options=options, 
        #                     show_output=getattr(run_step, 'show_output', True))
        
        return f"DockerRequest(EXEC, cmd={' '.join(cmd)}, options={options})"
    
    def build_from_node(self, node):
        """ConfigNodeからDockerRequestを構築"""
        self._validate_and_format_common_fields(node, is_node=True)
        
        cmd = node.value.get('cmd', [])
        cwd = node.value.get('cwd')
        
        # 共通処理を使用
        formatted_cmd = ConfigNodeProcessor.format_command_array(self.factory, node, cmd)
        formatted_cwd = ConfigNodeProcessor.format_single_field(self.factory, node, 'cwd', cwd) if cwd else None
        
        options = {}
        if formatted_cwd:
            options["workdir"] = formatted_cwd
        
        return f"DockerRequest(EXEC, cmd={' '.join(formatted_cmd)}, options={options})"


class PythonRequestBuilder(CommandRequestBuilder):
    """PythonRequestビルダー"""
    
    def build_from_run_step(self, run_step):
        """PythonRunStepからPythonRequestを構築"""
        self._validate_and_format_common_fields(run_step, is_node=False)
        
        code_or_file = [self.factory.format_string(str(arg)) for arg in run_step.cmd]
        cwd = self.factory.format_string(run_step.cwd) if getattr(run_step, 'cwd', None) else None
        
        # return PythonRequest(code_or_file, cwd=cwd, 
        #                     show_output=getattr(run_step, 'show_output', True))
        
        return f"PythonRequest(code_or_file={code_or_file}, cwd={cwd})"
    
    def build_from_node(self, node):
        """ConfigNodeからPythonRequestを構築"""
        self._validate_and_format_common_fields(node, is_node=True)
        
        cmd = node.value.get('cmd', [])
        cwd = node.value.get('cwd')
        
        formatted_cmd = ConfigNodeProcessor.format_command_array(self.factory, node, cmd)
        formatted_cwd = ConfigNodeProcessor.format_single_field(self.factory, node, 'cwd', cwd) if cwd else None
        
        return f"PythonRequest(code_or_file={formatted_cmd}, cwd={formatted_cwd})"


class UnifiedCommandRequestFactory:
    """統合コマンドリクエストファクトリ"""
    
    def __init__(self, controller):
        self.controller = controller
        self._builders = self._initialize_builders()
    
    def _initialize_builders(self) -> Dict[CommandType, CommandRequestBuilder]:
        """ビルダーを初期化"""
        # FileOpTypeの疑似実装（実装時には実際のenumを使用）
        class FileOpType(Enum):
            COPY = auto()
            MKDIR = auto()
            TOUCH = auto()
            REMOVE = auto()
            RMTREE = auto()
            MOVE = auto()
            MOVETREE = auto()
        
        return {
            # コマンド実行系
            CommandType.SHELL: ShellRequestBuilder(self),
            CommandType.DOCKER: DockerRequestBuilder(self),
            CommandType.BUILD: ShellRequestBuilder(self),  # BuildはShellRequestを使用
            CommandType.PYTHON: PythonRequestBuilder(self),
            CommandType.OJ: DockerRequestBuilder(self),  # 条件によりShell/Dockerを選択（実装時に詳細化）
            
            # ファイル操作系（FileOpTypeに対応）
            CommandType.COPY: FileRequestBuilder(self, FileOpType.COPY),
            CommandType.MKDIR: FileRequestBuilder(self, FileOpType.MKDIR),
            CommandType.TOUCH: FileRequestBuilder(self, FileOpType.TOUCH),
            CommandType.REMOVE: FileRequestBuilder(self, FileOpType.REMOVE),
            CommandType.RMTREE: FileRequestBuilder(self, FileOpType.RMTREE),
            CommandType.MOVE: FileRequestBuilder(self, FileOpType.MOVE),
            CommandType.MOVETREE: FileRequestBuilder(self, FileOpType.MOVETREE),
        }
    
    def create_request(self, run_step):
        """RunStepからリクエストを生成"""
        command_type = self._determine_command_type(run_step)
        builder = self._get_builder(command_type)
        return builder.build_from_run_step(run_step)
    
    def create_request_from_node(self, node):
        """ConfigNodeからリクエストを生成"""
        command_type = self._determine_command_type_from_node(node)
        builder = self._get_builder(command_type)
        return builder.build_from_node(node)
    
    def _determine_command_type(self, run_step) -> CommandType:
        """RunStepからコマンドタイプを決定"""
        # 実装時にrun_stepの型に基づいて判定
        class_name = type(run_step).__name__
        if 'Shell' in class_name:
            return CommandType.SHELL
        elif 'Docker' in class_name:
            return CommandType.DOCKER
        elif 'Build' in class_name:
            return CommandType.BUILD
        elif 'Python' in class_name:
            return CommandType.PYTHON
        elif 'Copy' in class_name:
            return CommandType.COPY
        elif 'Mkdir' in class_name:
            return CommandType.MKDIR
        # ... 他のタイプも同様に判定
        else:
            raise ValueError(f"Unknown run_step type: {class_name}")
    
    def _determine_command_type_from_node(self, node) -> CommandType:
        """ConfigNodeからコマンドタイプを決定"""
        # nodeのメタデータまたは構造から判定
        # 実装時にnode.value内の'type'フィールドなどを確認
        if hasattr(node, 'command_type'):
            return CommandType[node.command_type.upper()]
        else:
            # デフォルトまたは推論ロジック
            raise ValueError("Cannot determine command type from node")
    
    def _get_builder(self, command_type: CommandType) -> CommandRequestBuilder:
        """コマンドタイプに対応するビルダーを取得"""
        builder = self._builders.get(command_type)
        if not builder:
            raise ValueError(f"No builder found for command type: {command_type}")
        return builder.reset()  # 状態をリセットして返す
    
    # BaseCommandRequestFactoryの互換メソッド
    def format_string(self, value):
        """文字列値をフォーマットする（BaseCommandRequestFactoryとの互換性）"""
        if not isinstance(value, str):
            return value
        
        # 既存のformat_stringロジックをここに実装
        initial_values = {
            "contest_name": self.controller.env_context.contest_name,
            "problem_id": self.controller.env_context.problem_name,
            "problem_name": self.controller.env_context.problem_name,
            "language": self.controller.env_context.language,
            "language_name": self.controller.env_context.language,
            "env_type": self.controller.env_context.env_type,
            "command_type": self.controller.env_context.command_type
        }
        
        result = value
        for key, val in initial_values.items():
            result = result.replace(f"{{{key}}}", str(val))
        
        return result
    
    def format_value(self, value, node):
        """値をフォーマットする（BaseCommandRequestFactoryとの互換性）"""
        if not isinstance(value, str):
            return value
        
        # 既存のformat_valueロジックをここに実装
        # resolve_format_stringを使用する部分
        return self.format_string(value)  # 簡略版
    
    def set_request_attributes(self, request, run_step_or_node):
        """requestにallow_failureとshow_outputを設定する共通メソッド"""
        if hasattr(run_step_or_node, 'allow_failure'):
            # RunStepの場合
            request.allow_failure = getattr(run_step_or_node, 'allow_failure', False)
            request.show_output = getattr(run_step_or_node, 'show_output', False)
        elif hasattr(run_step_or_node, 'value') and isinstance(run_step_or_node.value, dict):
            # ConfigNodeの場合
            request.allow_failure = run_step_or_node.value.get('allow_failure', False)
            request.show_output = run_step_or_node.value.get('show_output', False)
        
        return request


# 使用例とデモ
def demonstrate_unified_factory():
    """統合ファクトリの使用例"""
    
    # 疑似的なcontrollerとコンテキスト
    class MockController:
        class MockContext:
            contest_name = "abc300"
            problem_name = "a"
            language = "python"
            env_type = "docker"
            command_type = "shell"
        env_context = MockContext()
    
    # 疑似的なrun_step
    class MockShellRunStep:
        cmd = ["python", "main.py"]
        cwd = "/workspace"
        show_output = True
        allow_failure = False
    
    # 疑似的なnode
    class MockNode:
        value = {
            'cmd': ["python", "main.py"],
            'cwd': "/workspace",
            'show_output': True
        }
        next_nodes = []
        key = 'shell'
        command_type = 'shell'
    
    # 統合ファクトリの使用
    controller = MockController()
    factory = UnifiedCommandRequestFactory(controller)
    
    # RunStepからリクエスト生成
    run_step = MockShellRunStep()
    request1 = factory.create_request(run_step)
    print(f"RunStepから生成: {request1}")
    
    # ConfigNodeからリクエスト生成
    node = MockNode()
    request2 = factory.create_request_from_node(node)
    print(f"ConfigNodeから生成: {request2}")


if __name__ == "__main__":
    demonstrate_unified_factory()