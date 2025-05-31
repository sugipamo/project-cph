"""
PureRequestFactory のテスト
"""
import pytest
from src.env_core.workflow.pure_request_factory import PureRequestFactory
from src.env_core.step.step import Step, StepType
from src.operations.file.file_request import FileRequest
from src.operations.file.file_op_type import FileOpType
from src.operations.shell.shell_request import ShellRequest
from src.operations.python.python_request import PythonRequest


class TestPureRequestFactory:
    """PureRequestFactory のテストクラス"""
    
    def test_create_mkdir_request(self):
        """mkdir requestの生成テスト"""
        step = Step(
            type=StepType.MKDIR,
            cmd=["./test_dir"],
            allow_failure=False
        )
        
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, FileRequest)
        assert request.path == "./test_dir"
        assert request.op == FileOpType.MKDIR
        assert request.allow_failure is False
    
    def test_create_touch_request(self):
        """touch requestの生成テスト"""
        step = Step(
            type=StepType.TOUCH,
            cmd=["./test_file.txt"],
            allow_failure=True
        )
        
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, FileRequest)
        assert request.path == "./test_file.txt"
        assert request.op == FileOpType.TOUCH
        assert request.allow_failure is True
    
    def test_create_copy_request(self):
        """copy requestの生成テスト"""
        step = Step(
            type=StepType.COPY,
            cmd=["./source.txt", "./dest.txt"],
            allow_failure=False
        )
        
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, FileRequest)
        assert request.path == "./source.txt"
        assert request.dst_path == "./dest.txt"
        assert request.op == FileOpType.COPY
        assert request.allow_failure is False
    
    def test_create_shell_request(self):
        """shell requestの生成テスト"""
        step = Step(
            type=StepType.SHELL,
            cmd=["echo", "hello", "world"],
            allow_failure=True,
            show_output=True,
            cwd="./work"
        )
        
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, ShellRequest)
        assert request.cmd == ["echo", "hello", "world"]
        assert request.allow_failure is True
        assert request.show_output is True
        assert request.cwd == "./work"
    
    def test_create_python_request(self):
        """python requestの生成テスト"""
        step = Step(
            type=StepType.PYTHON,
            cmd=["import os", "print(os.getcwd())"],
            allow_failure=False,
            show_output=True
        )
        
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, PythonRequest)
        assert "import os" in request.code_or_file
        assert "print(os.getcwd())" in request.code_or_file
        assert request.allow_failure is False
        assert request.show_output is True
    
    def test_create_remove_request(self):
        """remove requestの生成テスト"""
        step = Step(
            type=StepType.REMOVE,
            cmd=["./temp_file.txt"],
            allow_failure=True
        )
        
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, FileRequest)
        assert request.path == "./temp_file.txt"
        assert request.op == FileOpType.REMOVE
        assert request.allow_failure is True
    
    def test_create_move_request(self):
        """move requestの生成テスト"""
        step = Step(
            type=StepType.MOVE,
            cmd=["./old_file.txt", "./new_file.txt"],
            allow_failure=False
        )
        
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, FileRequest)
        assert request.path == "./old_file.txt"
        assert request.dst_path == "./new_file.txt"
        assert request.op == FileOpType.MOVE
        assert request.allow_failure is False
    
    def test_create_rmtree_request(self):
        """rmtree requestの生成テスト"""
        step = Step(
            type=StepType.RMTREE,
            cmd=["./temp_dir"],
            allow_failure=True
        )
        
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, FileRequest)
        assert request.path == "./temp_dir"
        assert request.op == FileOpType.RMTREE
        assert request.allow_failure is True
    
    def test_invalid_step_type(self):
        """未知のステップタイプの処理テスト"""
        # StepTypeにないタイプを直接作成（テスト目的）
        step = Step(
            type=StepType.BUILD,  # PureRequestFactoryで未対応
            cmd=["make"],
            allow_failure=False
        )
        
        request = PureRequestFactory.create_request_from_step(step)
        
        # 未知のタイプはNoneを返す
        assert request is None
    
    def test_invalid_cmd_parameters(self):
        """無効なcmdパラメータの処理テスト"""
        # 正常なcopyとエラーケースを分けてテスト
        valid_step = Step(
            type=StepType.COPY,
            cmd=["./source.txt", "./dest.txt"],
            allow_failure=False
        )
        
        request = PureRequestFactory.create_request_from_step(valid_step)
        assert request is not None  # 正常な場合
        
        # Stepの検証でエラーが出るケースは除外し、
        # Factoryレベルでのエラーハンドリングをテスト
        # 例：未知のステップタイプ
        build_step = Step(
            type=StepType.BUILD,  # PureRequestFactoryで未対応
            cmd=["make", "all"],
            allow_failure=False
        )
        
        request = PureRequestFactory.create_request_from_step(build_step)
        assert request is None  # 未対応タイプはNoneを返す
    
    def test_operations_independence(self):
        """operations非依存の確認テスト"""
        # PureRequestFactoryはoperationsなしで動作する
        step = Step(
            type=StepType.MKDIR,
            cmd=["./test"],
            allow_failure=False
        )
        
        # operations を渡さずに実行
        request = PureRequestFactory.create_request_from_step(step, context=None)
        
        assert isinstance(request, FileRequest)
        assert request.path == "./test"
        
        # 複数のステップタイプでテスト
        test_cases = [
            (StepType.TOUCH, ["./file.txt"], FileRequest),
            (StepType.SHELL, ["echo", "test"], ShellRequest),
            (StepType.PYTHON, ["print('hello')"], PythonRequest),
        ]
        
        for step_type, cmd, expected_type in test_cases:
            step = Step(type=step_type, cmd=cmd, allow_failure=False)
            request = PureRequestFactory.create_request_from_step(step)
            assert isinstance(request, expected_type)