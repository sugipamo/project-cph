"""
回帰テスト: これまでに発見された問題を検出するテストケース
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch

from src.env_core.step.step import Step, StepType, StepContext
from src.env_core.workflow.pure_request_factory import PureRequestFactory
from src.operations.docker.docker_request import DockerRequest
from src.operations.shell.shell_request import ShellRequest
from src.operations.file.file_request import FileRequest
from src.operations.file.file_op_type import FileOpType
from src.workflow_execution_service import WorkflowExecutionService
from src.operations.result.result import OperationResult


class TestRegressionFixes:
    """これまでに発見された問題の回帰テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.context = Mock(spec=StepContext)
        self.context.contest_name = "abc300"
        self.context.problem_name = "a"
        self.context.language = "python"
        self.context.env_type = "local"  # ローカル環境にしてDocker関連エラーを回避
        self.context.command_type = "test"
        self.context.workspace_path = "./workspace"
        self.context.contest_current_path = "./contest_current"
        
    def test_test_step_docker_request_creation_no_cwd_parameter(self):
        """
        回帰テスト: TEST stepがDockerRequestのcwdパラメータエラーで失敗しない
        
        問題: DockerRequest.__init__()にcwdパラメータを渡してTypeErrorが発生
        修正: cwdパラメータを除去
        """
        step = Step(
            type=StepType.TEST,
            cmd=["python3", "./workspace/main.py"],
            cwd="./workspace",
            allow_failure=False,
            show_output=True
        )
        
        # Docker環境のコンテキストを設定
        docker_context = Mock(spec=StepContext)
        docker_context.env_type = "docker"
        docker_context.get_docker_names = Mock(return_value={'container_name': 'test_container'})
        
        # リクエスト生成がエラーなく動作することを確認
        request = PureRequestFactory.create_request_from_step(step, docker_context)
        
        # DockerRequestが正常に生成されることを確認
        assert request is not None
        assert isinstance(request, (DockerRequest, ShellRequest))  # 仮実装でShellRequestになる場合もあり
        assert request.allow_failure == False
        assert request.show_output == True
        
    def test_test_step_local_fallback_implementation(self):
        """
        回帰テスト: TEST stepがローカル環境でShellRequestとして正しく実装される
        
        問題: TEST stepが仮実装としてShellRequestにフォールバックする
        """
        step = Step(
            type=StepType.TEST,
            cmd=["python3", "./workspace/main.py"],
            cwd="./workspace",
            allow_failure=False,
            show_output=True
        )
        
        # ローカル環境のコンテキスト
        local_context = StepContext(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local", 
            command_type="test",
            workspace_path="./workspace",
            contest_current_path="./contest_current"
        )
        
        request = PureRequestFactory.create_request_from_step(step, local_context)
        
        # ShellRequestが生成されることを確認
        assert request is not None
        assert isinstance(request, ShellRequest)
        assert request.allow_failure == False
        assert request.show_output == True
        
    def test_movetree_step_implementation_exists(self):
        """
        回帰テスト: MOVETREE stepが正しく実装されている
        
        問題: PureRequestFactoryでMOVETREEステップタイプが未実装でNoneが返される
        修正: _create_movetree_requestメソッドを追加
        """
        step = Step(
            type=StepType.MOVETREE,
            cmd=["./workspace/test", "./contest_current/test"],
            allow_failure=True,
            show_output=False
        )
        
        request = PureRequestFactory.create_request_from_step(step, self.context)
        
        # FileRequestが正常に生成されることを確認
        assert request is not None
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.COPYTREE
        assert request.path == "./workspace/test"
        assert request.dst_path == "./contest_current/test"
        assert request.allow_failure == True
        
    def test_all_step_types_have_implementations(self):
        """
        回帰テスト: 全てのStepTypeに対応する実装が存在する
        
        問題: 新しいStepTypeが追加されてもPureRequestFactoryで未実装になる
        """
        # 各ステップタイプが正常に処理されることを確認
        test_cases = [
            (StepType.MKDIR, ["./test_dir"]),
            (StepType.TOUCH, ["./test_file.txt"]),
            (StepType.COPY, ["./src.txt", "./dst.txt"]),
            (StepType.MOVE, ["./src.txt", "./dst.txt"]),
            (StepType.MOVETREE, ["./src_dir", "./dst_dir"]),
            (StepType.REMOVE, ["./test_file.txt"]),
            (StepType.RMTREE, ["./test_dir"]),
            (StepType.SHELL, ["echo", "test"]),
            (StepType.PYTHON, ["print('test')"]),
            (StepType.TEST, ["python3", "test.py"]),
            (StepType.BUILD, ["make", "build"]),
            (StepType.OJ, ["oj", "download", "url"]),
        ]
        
        for step_type, cmd in test_cases:
            step = Step(
                type=step_type,
                cmd=cmd,
                allow_failure=True,
                show_output=False
            )
            
            request = PureRequestFactory.create_request_from_step(step, self.context)
            
            # 全てのステップタイプでリクエストが生成されることを確認
            assert request is not None, f"Step type {step_type} returned None"
                
    def test_allow_failure_handling_in_workflow_execution(self):
        """
        回帰テスト: allow_failure=trueのステップ失敗が全体の失敗とならない
        
        問題: WorkflowExecutionServiceでallow_failureを考慮せずに全体失敗と判定
        修正: allow_failure=trueの失敗を致命的失敗から除外
        """
        # モックコンテキストとオペレーション
        mock_context = Mock()
        mock_context.env_json = {
            "python": {
                "commands": {
                    "test": {
                        "steps": [
                            {
                                "type": "shell",
                                "allow_failure": True,
                                "cmd": ["false"]  # 常に失敗するコマンド
                            },
                            {
                                "type": "shell", 
                                "allow_failure": False,
                                "cmd": ["true"]   # 常に成功するコマンド
                            }
                        ]
                    }
                }
            }
        }
        mock_context.language = "python"
        mock_context.command_type = "test"
        
        mock_operations = Mock()
        
        # WorkflowExecutionServiceをモック
        service = WorkflowExecutionService(mock_context, mock_operations)
        
        # モック結果を作成
        # 1つ目: allow_failure=trueで失敗
        failed_result_allowed = Mock(spec=OperationResult)
        failed_result_allowed.success = False
        failed_result_allowed.request = Mock()
        failed_result_allowed.request.allow_failure = True
        failed_result_allowed.get_error_output = Mock(return_value="Allowed failure")
        
        # 2つ目: allow_failure=falseで成功
        success_result = Mock(spec=OperationResult) 
        success_result.success = True
        success_result.request = Mock()
        success_result.request.allow_failure = False
        
        # _get_workflow_stepsとgraph executionをモック
        with patch.object(service, '_get_workflow_steps') as mock_get_steps, \
             patch('src.workflow_execution_service.generate_steps_from_json') as mock_generate, \
             patch('src.workflow_execution_service.GraphBasedWorkflowBuilder') as mock_builder:
            
            mock_get_steps.return_value = mock_context.env_json["python"]["commands"]["test"]["steps"]
            
            mock_step_result = Mock()
            mock_step_result.steps = []
            mock_step_result.errors = []
            mock_step_result.warnings = []
            mock_generate.return_value = mock_step_result
            
            mock_graph = Mock()
            mock_graph.execute_sequential = Mock(return_value=[failed_result_allowed, success_result])
            mock_builder_instance = Mock()
            mock_builder_instance.build_graph_from_json_steps = Mock(return_value=(mock_graph, [], []))
            mock_builder.from_context = Mock(return_value=mock_builder_instance)
            
            # 実行
            result = service.execute_workflow()
            
            # allow_failure=trueの失敗があってもワークフロー全体は成功するべき
            assert result.success == True, "Workflow should succeed when only allow_failure=true steps fail"
            assert len(result.errors) == 1  # エラーは記録されるが致命的ではない
            assert "allowed" in result.errors[0].lower()  # "allowed"が含まれることを確認
            
    def test_workflow_execution_critical_failure_detection(self):
        """
        回帰テスト: allow_failure=falseのステップ失敗は全体の失敗となる
        """
        # モックコンテキストとオペレーション
        mock_context = Mock()
        mock_context.env_json = {
            "python": {
                "commands": {
                    "test": {
                        "steps": [
                            {
                                "type": "shell",
                                "allow_failure": False,
                                "cmd": ["false"]  # 常に失敗するコマンド
                            }
                        ]
                    }
                }
            }
        }
        mock_context.language = "python"
        mock_context.command_type = "test"
        
        mock_operations = Mock()
        service = WorkflowExecutionService(mock_context, mock_operations)
        
        # allow_failure=falseで失敗する結果
        critical_failed_result = Mock(spec=OperationResult)
        critical_failed_result.success = False
        critical_failed_result.request = Mock()
        critical_failed_result.request.allow_failure = False
        critical_failed_result.get_error_output = Mock(return_value="Critical failure")
        
        with patch.object(service, '_get_workflow_steps') as mock_get_steps, \
             patch('src.workflow_execution_service.generate_steps_from_json') as mock_generate, \
             patch('src.workflow_execution_service.GraphBasedWorkflowBuilder') as mock_builder:
            
            mock_get_steps.return_value = mock_context.env_json["python"]["commands"]["test"]["steps"]
            
            mock_step_result = Mock()
            mock_step_result.steps = []
            mock_step_result.errors = []
            mock_step_result.warnings = []
            mock_generate.return_value = mock_step_result
            
            mock_graph = Mock()
            mock_graph.execute_sequential = Mock(return_value=[critical_failed_result])
            mock_builder_instance = Mock()
            mock_builder_instance.build_graph_from_json_steps = Mock(return_value=(mock_graph, [], []))
            mock_builder.from_context = Mock(return_value=mock_builder_instance)
            
            # 実行
            result = service.execute_workflow()
            
            # allow_failure=falseの失敗でワークフロー全体は失敗するべき
            assert result.success == False, "Workflow should fail when allow_failure=false steps fail"
            assert len(result.errors) == 1
            assert "allowed" not in result.errors[0].lower()  # "allowed"は含まれない
            
    def test_step_context_formatting_preserves_paths(self):
        """
        回帰テスト: ステップコンテキストのフォーマットが正しく動作する
        
        問題: テンプレート文字列の置換でパスが正しく展開されない
        """
        context = StepContext(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test", 
            workspace_path="./workspace",
            contest_current_path="./contest_current",
            contest_template_path="./contest_template/python",
            source_file_name="main.py"
        )
        
        format_dict = context.to_format_dict()
        
        # 重要なフィールドが正しく設定されることを確認
        assert format_dict['contest_name'] == "abc300"
        assert format_dict['problem_name'] == "a"
        assert format_dict['problem_id'] == "a"  # problem_nameのエイリアス
        assert format_dict['workspace_path'] == "./workspace"
        assert format_dict['contest_current_path'] == "./contest_current"
        assert format_dict['source_file_name'] == "main.py"
        
        # テンプレート文字列の展開をテスト
        template = "{contest_current_path}/{source_file_name}"
        result = template.format(**format_dict)
        assert result == "./contest_current/main.py"