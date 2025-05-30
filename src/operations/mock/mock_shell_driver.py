from src.operations.shell.shell_driver import ShellDriver

class MockShellDriver(ShellDriver):
    """
    振る舞い検証用のモックシェルドライバー
    - 呼び出し履歴の記録
    - 期待値の設定と検証
    """
    def __init__(self):
        self.calls = []
        self.call_count = 0
        self.expected_results = {}
        self.default_result = None

    def set_expected_result(self, cmd_pattern, stdout="", stderr="", returncode=0):
        """特定のコマンドパターンに対する期待結果を設定"""
        self.expected_results[cmd_pattern] = {
            'stdout': stdout,
            'stderr': stderr,
            'returncode': returncode
        }

    def set_default_result(self, stdout="mock_stdout", stderr="", returncode=0):
        """デフォルトの結果を設定"""
        self.default_result = {
            'stdout': stdout,
            'stderr': stderr,
            'returncode': returncode
        }

    def assert_called_with(self, expected_cmd, times=None):
        """指定されたコマンドで呼ばれたことを検証"""
        matching_calls = [call for call in self.calls if call['cmd'] == expected_cmd]
        if times is None:
            assert len(matching_calls) > 0, f"Command {expected_cmd} was not called"
        else:
            assert len(matching_calls) == times, f"Command {expected_cmd} was called {len(matching_calls)} times, expected {times}"

    def run(self, cmd, cwd=None, env=None, inputdata=None, timeout=None):
        self.call_count += 1
        call_info = {
            'cmd': cmd,
            'cwd': cwd,
            'env': env,
            'inputdata': inputdata,
            'timeout': timeout
        }
        self.calls.append(call_info)

        # 期待結果の検索
        result_data = None
        for cmd_pattern, expected in self.expected_results.items():
            if cmd_pattern in str(cmd):
                result_data = expected
                break
        
        if result_data is None:
            result_data = self.default_result or {
                'stdout': 'mock_stdout',
                'stderr': '',
                'returncode': 0
            }

        class MockResult:
            def __init__(self, stdout, stderr, returncode):
                self.stdout = stdout
                self.stderr = stderr
                self.returncode = returncode

        return MockResult(
            result_data['stdout'],
            result_data['stderr'],
            result_data['returncode']
        ) 