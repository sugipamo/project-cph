"""
PureRequestFactory回帰テスト: 以前に発見された具体的な問題
"""
import pytest
from unittest.mock import Mock

from src.env_core.step.step import Step, StepType, StepContext
from src.env_core.workflow.pure_request_factory import PureRequestFactory
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.operations.shell.shell_request import ShellRequest
from src.operations.file.file_request import FileRequest
from src.operations.file.file_op_type import FileOpType


class TestPureRequestFactoryRegression:
    """PureRequestFactory回帰テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.docker_context = Mock(spec=StepContext)
        self.docker_context.contest_name = "abc300"
        self.docker_context.problem_name = "a"
        self.docker_context.language = "python"
        self.docker_context.env_type = "docker"
        self.docker_context.command_type = "test"
        self.docker_context.workspace_path = "./workspace"
        self.docker_context.contest_current_path = "./contest_current"
        self.docker_context.get_docker_names = Mock(return_value={
            'container_name': 'test_container',
            'oj_container_name': 'oj_container'
        })
        
        self.local_context = Mock(spec=StepContext)
        self.local_context.contest_name = "abc300"
        self.local_context.problem_name = "a"
        self.local_context.language = "python"
        self.local_context.env_type = "local"
        self.local_context.command_type = "test"
        self.local_context.workspace_path = "./workspace"
        self.local_context.contest_current_path = "./contest_current"
    
    def test_docker_request_creation_without_invalid_cwd_parameter(self):
        """
        回帰テスト: DockerRequestでcwdパラメータを渡さない
        
        以前の問題: DockerRequest(cwd=step.cwd)でTypeError
        修正後: cwdパラメータを除去
        """
        test_step = Step(
            type=StepType.TEST,
            cmd=["python3", "main.py"],
            cwd="./workspace",
            allow_failure=False,
            show_output=True
        )
        
        # TEST stepの場合、仮実装でShellRequestになる
        request = PureRequestFactory._create_test_request(test_step, self.local_context)
        assert isinstance(request, ShellRequest)
        
        build_step = Step(
            type=StepType.BUILD, 
            cmd=["make", "build"],
            cwd="./workspace",
            allow_failure=False,
            show_output=True
        )
        
        # BUILD stepをDocker環境で実行する場合
        # 注意: 現在の実装ではcwdパラメータが除去されているはず
        try:
            request = PureRequestFactory._create_build_request(build_step, self.docker_context)
            # DockerRequestの場合、cwdパラメータがないため例外は発生しないはず
            if isinstance(request, DockerRequest):
                assert request.op == DockerOpType.EXEC
                assert request.container == 'test_container'
                assert request.command == 'make build'
                # cwdプロパティが存在しないか、設定されていないことを確認
                assert not hasattr(request, 'cwd') or getattr(request, 'cwd', None) is None
        except TypeError as e:
            pytest.fail(f"DockerRequest creation should not fail with cwd parameter: {e}")
            
    def test_oj_request_docker_creation(self):
        """
        回帰テスト: OJリクエストのDocker版でcwdパラメータエラーが発生しない
        """
        oj_step = Step(
            type=StepType.OJ,
            cmd=["oj", "download", "https://example.com"],
            cwd="./workspace", 
            allow_failure=True,
            show_output=True
        )
        
        # OJ stepをDocker環境で実行する場合
        try:
            request = PureRequestFactory._create_oj_request(oj_step, self.docker_context)
            if isinstance(request, DockerRequest):
                assert request.op == DockerOpType.EXEC
                assert request.container == 'oj_container'  # OJ専用コンテナ
                assert request.command == 'oj download https://example.com'
                # cwdプロパティが設定されていないことを確認
                assert not hasattr(request, 'cwd') or getattr(request, 'cwd', None) is None
        except TypeError as e:
            pytest.fail(f"OJ DockerRequest creation should not fail with cwd parameter: {e}")
    
    def test_movetree_step_creates_copytree_request(self):
        """
        回帰テスト: MOVETREEステップがCOPYTREE FileRequestを作成する
        
        以前の問題: MOVETREEステップタイプが未実装でNoneが返される
        修正後: _create_movetree_requestメソッドが実装され、COPYTREEとして動作
        """
        movetree_step = Step(
            type=StepType.MOVETREE,
            cmd=["./workspace/test", "./contest_current/test"],
            allow_failure=True,
            show_output=False
        )
        
        request = PureRequestFactory.create_request_from_step(movetree_step, self.local_context)
        
        # FileRequestが生成されることを確認
        assert request is not None
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.COPYTREE
        assert request.path == "./workspace/test"
        assert request.dst_path == "./contest_current/test"
        assert request.allow_failure == True
        
    def test_movetree_step_validation(self):
        """
        回帰テスト: MOVETREEステップの引数検証
        """
        from unittest.mock import Mock
        
        # 引数が不足している場合（Mockを使ってStep検証をバイパス）
        invalid_step = Mock()
        invalid_step.type = StepType.MOVETREE
        invalid_step.cmd = ["./single_path"]  # 2つのパスが必要
        invalid_step.allow_failure = True
        invalid_step.show_output = False
        
        with pytest.raises(ValueError, match="movetree step requires source and destination paths"):
            PureRequestFactory._create_movetree_request(invalid_step, self.local_context)
            
    def test_all_step_types_return_non_none_requests(self):
        """
        回帰テスト: 全てのステップタイプでNoneが返されない
        
        以前の問題: 未実装のステップタイプでNoneが返される
        修正後: 全てのStepTypeに対応する実装が存在
        """
        step_configs = [
            (StepType.MKDIR, ["./test"]),
            (StepType.TOUCH, ["./test.txt"]),
            (StepType.COPY, ["./src", "./dst"]),
            (StepType.MOVE, ["./src", "./dst"]),
            (StepType.MOVETREE, ["./src", "./dst"]),
            (StepType.REMOVE, ["./test"]),
            (StepType.RMTREE, ["./test"]),
            (StepType.SHELL, ["echo", "test"]),
            (StepType.PYTHON, ["print('test')"]),
            (StepType.TEST, ["python3", "test.py"]),
            (StepType.BUILD, ["make"]),
            (StepType.OJ, ["oj", "test"]),
        ]
        
        for step_type, cmd in step_configs:
            step = Step(
                type=step_type,
                cmd=cmd,
                allow_failure=True,
                show_output=False
            )
            
            request = PureRequestFactory.create_request_from_step(step, self.local_context)
            assert request is not None, f"Step type {step_type.value} should not return None"
            
    def test_request_properties_preservation(self):
        """
        回帰テスト: ステップのプロパティがリクエストに正しく伝達される
        
        以前の問題: allow_failureやshow_outputが正しく設定されない場合がある
        """
        step = Step(
            type=StepType.SHELL,
            cmd=["echo", "test"],
            allow_failure=True,
            show_output=False,
            cwd="./test_dir"
        )
        
        request = PureRequestFactory.create_request_from_step(step, self.local_context)
        
        assert isinstance(request, ShellRequest)
        assert request.allow_failure == True
        assert request.show_output == False
        assert request.cwd == "./test_dir"
        
    def test_exception_handling_returns_none(self):
        """
        回帰テスト: 例外が発生した場合にNoneが返される
        
        リクエスト生成で例外が発生してもワークフロー全体がクラッシュしないようにする
        """
        from unittest.mock import Mock
        
        # 不正な引数でステップを作成（Mockを使ってStep検証をバイパス）
        invalid_step = Mock()
        invalid_step.type = StepType.COPY
        invalid_step.cmd = ["single_arg"]  # COPYには2つの引数が必要
        invalid_step.allow_failure = False
        invalid_step.show_output = False
        
        # 例外が発生してもNoneが返されることを確認
        request = PureRequestFactory.create_request_from_step(invalid_step, self.local_context)
        assert request is None
        
    def test_context_dependency_handling(self):
        """
        回帰テスト: コンテキストに依存する処理が正しく動作する
        
        Docker環境とローカル環境でリクエストタイプが変わる場合の処理
        """
        test_step = Step(
            type=StepType.TEST,
            cmd=["python3", "main.py"],
            allow_failure=False,
            show_output=True
        )
        
        # ローカル環境ではShellRequest
        local_request = PureRequestFactory.create_request_from_step(test_step, self.local_context)
        assert isinstance(local_request, ShellRequest)
        
        # Docker環境でも現在は仮実装でShellRequest
        # 将来的にDockerRequestになる可能性もある
        docker_request = PureRequestFactory.create_request_from_step(test_step, self.docker_context)
        assert docker_request is not None
        assert isinstance(docker_request, (ShellRequest, DockerRequest))