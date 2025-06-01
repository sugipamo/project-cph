"""
純粋なRequest生成Factory

operationsに依存しない、ユーザー入力からRequestを生成する純粋関数的Factory
"""
from typing import Optional, Any
from src.env_core.step.step import Step, StepType
from src.operations.file.file_request import FileRequest
from src.operations.file.file_op_type import FileOpType
from src.operations.shell.shell_request import ShellRequest
from src.operations.python.python_request import PythonRequest
from src.operations.docker.docker_request import DockerRequest, DockerOpType


class PureRequestFactory:
    """
    純粋なRequest生成Factory
    
    operationsに依存せず、Step情報からRequestを直接生成
    """
    
    @staticmethod
    def create_request_from_step(step: Step, context=None) -> Optional[Any]:
        """
        StepからRequestを純粋に生成
        
        Args:
            step: 変換するStep
            context: フォーマット用のコンテキスト（オプション）
            
        Returns:
            生成されたRequest、または None
        """
        try:
            if step.type == StepType.MKDIR:
                return PureRequestFactory._create_mkdir_request(step, context)
            elif step.type == StepType.TOUCH:
                return PureRequestFactory._create_touch_request(step, context)
            elif step.type == StepType.COPY:
                return PureRequestFactory._create_copy_request(step, context)
            elif step.type == StepType.MOVE:
                return PureRequestFactory._create_move_request(step, context)
            elif step.type == StepType.MOVETREE:
                return PureRequestFactory._create_movetree_request(step, context)
            elif step.type == StepType.REMOVE:
                return PureRequestFactory._create_remove_request(step, context)
            elif step.type == StepType.RMTREE:
                return PureRequestFactory._create_rmtree_request(step, context)
            elif step.type == StepType.SHELL:
                return PureRequestFactory._create_shell_request(step, context)
            elif step.type == StepType.PYTHON:
                return PureRequestFactory._create_python_request(step, context)
            elif step.type == StepType.DOCKER_EXEC:
                return PureRequestFactory._create_docker_exec_request(step, context)
            elif step.type == StepType.DOCKER_CP:
                return PureRequestFactory._create_docker_cp_request(step, context)
            elif step.type == StepType.DOCKER_RUN:
                return PureRequestFactory._create_docker_run_request(step, context)
            elif step.type == StepType.TEST:
                return PureRequestFactory._create_test_request(step, context)
            elif step.type == StepType.BUILD:
                return PureRequestFactory._create_build_request(step, context)
            elif step.type == StepType.OJ:
                return PureRequestFactory._create_oj_request(step, context)
            else:
                # 未知のステップタイプ
                return None
        except Exception:
            # 生成エラーの場合はNoneを返す
            return None
    
    @staticmethod
    def _create_mkdir_request(step: Step, context) -> FileRequest:
        """mkdir requestを生成"""
        if not step.cmd:
            raise ValueError("mkdir step requires target path in cmd")
        target_path = step.cmd[0]
        request = FileRequest(op=FileOpType.MKDIR, path=target_path)
        request.allow_failure = step.allow_failure
        return request
    
    @staticmethod
    def _create_touch_request(step: Step, context) -> FileRequest:
        """touch requestを生成"""
        if not step.cmd:
            raise ValueError("touch step requires target path in cmd")
        target_path = step.cmd[0]
        request = FileRequest(op=FileOpType.TOUCH, path=target_path)
        request.allow_failure = step.allow_failure
        return request
    
    @staticmethod
    def _create_copy_request(step: Step, context) -> FileRequest:
        """copy requestを生成"""
        if len(step.cmd) < 2:
            raise ValueError("copy step requires source and destination paths")
        source_path = step.cmd[0]
        dest_path = step.cmd[1]
        request = FileRequest(op=FileOpType.COPY, path=source_path, dst_path=dest_path)
        request.allow_failure = step.allow_failure
        return request
    
    @staticmethod
    def _create_move_request(step: Step, context) -> FileRequest:
        """move requestを生成"""
        if len(step.cmd) < 2:
            raise ValueError("move step requires source and destination paths")
        source_path = step.cmd[0]
        dest_path = step.cmd[1]
        request = FileRequest(op=FileOpType.MOVE, path=source_path, dst_path=dest_path)
        request.allow_failure = step.allow_failure
        return request
    
    @staticmethod
    def _create_movetree_request(step: Step, context) -> FileRequest:
        """movetree requestを生成（実際にはcopytreeとして実装）"""
        if len(step.cmd) < 2:
            raise ValueError("movetree step requires source and destination paths")
        source_path = step.cmd[0]
        dest_path = step.cmd[1]
        request = FileRequest(op=FileOpType.COPYTREE, path=source_path, dst_path=dest_path)
        request.allow_failure = step.allow_failure
        return request
    
    @staticmethod
    def _create_remove_request(step: Step, context) -> FileRequest:
        """remove requestを生成"""
        if not step.cmd:
            raise ValueError("remove step requires target path in cmd")
        target_path = step.cmd[0]
        request = FileRequest(op=FileOpType.REMOVE, path=target_path)
        request.allow_failure = step.allow_failure
        return request
    
    @staticmethod
    def _create_rmtree_request(step: Step, context) -> FileRequest:
        """rmtree requestを生成"""
        if not step.cmd:
            raise ValueError("rmtree step requires target path in cmd")
        target_path = step.cmd[0]
        request = FileRequest(op=FileOpType.RMTREE, path=target_path)
        request.allow_failure = step.allow_failure
        return request
    
    @staticmethod
    def _create_shell_request(step: Step, context) -> ShellRequest:
        """shell requestを生成"""
        if not step.cmd:
            raise ValueError("shell step requires command")
        request = ShellRequest(cmd=step.cmd, cwd=step.cwd, show_output=step.show_output)
        request.allow_failure = step.allow_failure
        return request
    
    @staticmethod
    def _create_python_request(step: Step, context) -> PythonRequest:
        """python requestを生成"""
        if not step.cmd:
            raise ValueError("python step requires code")
        
        # PythonRequestはcode_or_fileとしてリストを受け取る
        request = PythonRequest(code_or_file=step.cmd, cwd=step.cwd, show_output=step.show_output)
        request.allow_failure = step.allow_failure
        return request
    
    @staticmethod
    def _create_docker_exec_request(step: Step, context) -> DockerRequest:
        """docker exec requestを生成"""
        if len(step.cmd) < 2:
            raise ValueError("docker_exec step requires container and command")
        
        container_name = step.cmd[0]
        command = ' '.join(step.cmd[1:])  # Join remaining arguments as command
        
        request = DockerRequest(
            op=DockerOpType.EXEC,
            container=container_name,
            command=command
        )
        request.allow_failure = step.allow_failure
        request.show_output = step.show_output
        return request
    
    @staticmethod
    def _create_docker_cp_request(step: Step, context) -> DockerRequest:
        """docker cp requestを生成"""
        if len(step.cmd) < 2:
            raise ValueError("docker_cp step requires source and destination")
        
        # Docker cp can be either:
        # - local_path container:remote_path (to container)
        # - container:remote_path local_path (from container)
        src = step.cmd[0]
        dst = step.cmd[1]
        
        # Determine direction and extract container name
        if ':' in src:
            # Copy FROM container
            container_name = src.split(':')[0]
            remote_path = src.split(':', 1)[1]
            local_path = dst
            to_container = False
        elif ':' in dst:
            # Copy TO container
            container_name = dst.split(':')[0]
            remote_path = dst.split(':', 1)[1]
            local_path = src
            to_container = True
        else:
            raise ValueError("docker_cp step requires container:path format in src or dst")
        
        # Use options to pass cp-specific parameters
        options = {
            'local_path': local_path,
            'remote_path': remote_path,
            'to_container': to_container
        }
        
        request = DockerRequest(
            op=DockerOpType.CP,
            container=container_name,
            options=options
        )
        request.allow_failure = step.allow_failure
        request.show_output = step.show_output
        return request
    
    @staticmethod
    def _create_docker_run_request(step: Step, context) -> DockerRequest:
        """docker run requestを生成"""
        if not step.cmd:
            raise ValueError("docker_run step requires image name")
        
        image_name = step.cmd[0]
        
        # Additional options from step.cmd[1:]
        options = {}
        if len(step.cmd) > 1:
            # Parse additional run options
            for i in range(1, len(step.cmd), 2):
                if i + 1 < len(step.cmd):
                    key = step.cmd[i].lstrip('-')  # Remove leading dashes
                    value = step.cmd[i + 1]
                    options[key] = value
        
        # Get container name from context if available
        container_name = None
        if context and hasattr(context, 'get_docker_names'):
            docker_names = context.get_docker_names()
            if 'ojtools' in image_name.lower():
                container_name = docker_names.get('oj_container_name')
            else:
                container_name = docker_names.get('container_name')
        
        request = DockerRequest(
            op=DockerOpType.RUN,
            image=image_name,
            container=container_name,
            options=options
        )
        request.allow_failure = step.allow_failure
        request.show_output = step.show_output
        return request
    @staticmethod
    def _create_test_request(step: Step, context) -> Any:
        """test requestを生成（テストケースファイルを使った実行）"""
        if not step.cmd:
            raise ValueError("test step requires command")
        
        # テストケース実行のためのコンポジットリクエストを作成
        from src.operations.composite.composite_request import CompositeRequest
        
        # テストケースディレクトリパスを構築
        if hasattr(context, 'contest_current_path'):
            test_dir = f"{context.contest_current_path}/test"
            workspace_path = getattr(context, 'workspace_path', './workspace')
        else:
            test_dir = "./contest_current/test"
            workspace_path = "./workspace"
        
        # テストケースファイルを探すためのシェルコマンドを構築
        # 各sample-*.inファイルに対してテストを実行
        test_commands = []
        
        # ベースディレクトリを取得
        base_dir = "/home/cphelper/project-cph"
        
        # sample-*.inファイルを探して、それぞれに対してテストを実行
        find_and_test_cmd = [
            "bash", "-c", 
            f'''
            cd "{base_dir}"
            test_dir="{test_dir}"
            workspace_file="{workspace_path}/main.py"
            
            if [[ ! -d "$test_dir" ]]; then
                echo "テストディレクトリが見つかりません: $test_dir"
                exit 1
            fi
            
            if [[ ! -f "$workspace_file" ]]; then
                echo "実行ファイルが見つかりません: $workspace_file"
                exit 1
            fi
            
            test_passed=0
            test_total=0
            
            for input_file in "$test_dir"/sample-*.in; do
                if [[ -f "$input_file" ]]; then
                    test_total=$((test_total + 1))
                    test_name=$(basename "$input_file" .in)
                    expected_file="${{input_file%.in}}.out"
                    
                    echo "=== テストケース: $test_name ==="
                    echo "入力:"
                    cat "$input_file"
                    echo "期待する出力:"
                    if [[ -f "$expected_file" ]]; then
                        cat "$expected_file"
                    else
                        echo "(期待する出力ファイルが見つかりません)"
                    fi
                    echo "実際の出力:"
                    
                    # プログラムを実行
                    if {" ".join(step.cmd)} < "$input_file" > temp_output.txt 2>&1; then
                        cat temp_output.txt
                        if [[ -f "$expected_file" ]] && diff -q "$expected_file" temp_output.txt > /dev/null; then
                            echo "✓ PASS"
                            test_passed=$((test_passed + 1))
                        else
                            echo "✗ FAIL"
                            if [[ -f "$expected_file" ]]; then
                                echo "差分:"
                                diff "$expected_file" temp_output.txt || true
                            fi
                        fi
                    else
                        echo "✗ RUNTIME ERROR"
                        cat temp_output.txt
                    fi
                    echo
                    rm -f temp_output.txt
                fi
            done
            
            if [[ $test_total -eq 0 ]]; then
                echo "テストケースが見つかりませんでした"
                exit 1
            fi
            
            echo "=== テスト結果 ==="
            echo "合格: $test_passed / $test_total"
            
            if [[ $test_passed -eq $test_total ]]; then
                echo "すべてのテストが合格しました！"
                exit 0
            else
                echo "いくつかのテストが失敗しました"
                exit 1
            fi
            '''
        ]
        
        request = ShellRequest(cmd=find_and_test_cmd, cwd=step.cwd, show_output=step.show_output)
        request.allow_failure = step.allow_failure
        request.show_output = step.show_output
        return request
    
    @staticmethod
    def _create_build_request(step: Step, context) -> Any:
        """build requestを生成（Docker環境ではdocker exec、ローカルではshell）"""
        if not step.cmd:
            raise ValueError("build step requires command")
        
        # env_typeがdockerの場合はDockerRequestを生成
        if hasattr(context, 'env_type') and context.env_type == 'docker':
            # Docker名を取得
            docker_names = context.get_docker_names()
            container_name = docker_names.get('container_name', 'build_container')
            
            # コマンドを文字列に結合
            command = ' '.join(step.cmd)
            
            request = DockerRequest(
                op=DockerOpType.EXEC,
                container=container_name,
                command=command
            )
        else:
            # ローカル環境の場合はShellRequestにフォールバック
            request = ShellRequest(cmd=step.cmd, cwd=step.cwd, show_output=step.show_output)
        
        request.allow_failure = step.allow_failure
        request.show_output = step.show_output
        return request
    
    @staticmethod
    def _create_oj_request(step: Step, context) -> Any:
        """oj requestを生成（Docker環境ではdocker exec、ローカルではshell）"""
        if not step.cmd:
            raise ValueError("oj step requires command")
        
        # env_typeがdockerの場合はDockerRequestを生成
        if hasattr(context, 'env_type') and context.env_type == 'docker':
            # OJ専用コンテナ名を取得
            docker_names = context.get_docker_names()
            container_name = docker_names.get('oj_container_name', 'oj_container')
            
            # コマンドを文字列に結合
            command = ' '.join(step.cmd)
            
            request = DockerRequest(
                op=DockerOpType.EXEC,
                container=container_name,
                command=command
            )
        else:
            # ローカル環境の場合はShellRequestにフォールバック
            request = ShellRequest(cmd=step.cmd, cwd=step.cwd, show_output=step.show_output)
        
        request.allow_failure = step.allow_failure
        request.show_output = step.show_output
        return request
