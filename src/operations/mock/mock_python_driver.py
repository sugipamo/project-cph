class MockPythonDriver:
    """
    Mock driver for Python operations to prevent actual code execution
    """
    def __init__(self):
        self.calls = []
        self.call_count = 0
        self.expected_results = {}
        self.default_result = None

    def set_expected_result(self, code_pattern, stdout="", stderr="", returncode=0):
        """Set expected result for specific code pattern"""
        self.expected_results[code_pattern] = {
            'stdout': stdout,
            'stderr': stderr,
            'returncode': returncode
        }

    def set_default_result(self, stdout="mock_python_output", stderr="", returncode=0):
        """Set default result"""
        self.default_result = {
            'stdout': stdout,
            'stderr': stderr,
            'returncode': returncode
        }

    def reset(self):
        """Reset all state"""
        self.calls.clear()
        self.call_count = 0
        self.expected_results.clear()
        self.default_result = None

    def assert_called_with(self, expected_code, times=None):
        """Assert that specific code was executed"""
        matching_calls = [call for call in self.calls if call['code'] == expected_code]
        if times is None:
            assert len(matching_calls) > 0, f"Code {expected_code} was not executed"
        else:
            assert len(matching_calls) == times, f"Code {expected_code} was executed {len(matching_calls)} times, expected {times}"

    def run_code_string(self, code, cwd=None):
        """Mock implementation of PythonUtils.run_code_string"""
        self.call_count += 1
        call_info = {
            'code': code,
            'cwd': cwd,
            'type': 'code_string'
        }
        self.calls.append(call_info)

        # Search for expected result
        result_data = None
        for code_pattern, expected in self.expected_results.items():
            if code_pattern in str(code):
                result_data = expected
                break
        
        if result_data is None:
            result_data = self.default_result or {
                'stdout': 'mock_python_output',
                'stderr': '',
                'returncode': 0
            }

        return result_data['stdout'], result_data['stderr'], result_data['returncode']

    def run_script_file(self, filename, cwd=None):
        """Mock implementation of PythonUtils.run_script_file"""
        self.call_count += 1
        call_info = {
            'filename': filename,
            'cwd': cwd,
            'type': 'script_file'
        }
        self.calls.append(call_info)

        # Search for expected result based on filename
        result_data = None
        for code_pattern, expected in self.expected_results.items():
            if code_pattern in str(filename):
                result_data = expected
                break
        
        if result_data is None:
            result_data = self.default_result or {
                'stdout': 'mock_script_output',
                'stderr': '',
                'returncode': 0
            }

        return result_data['stdout'], result_data['stderr'], result_data['returncode']

    def is_script_file(self, code_or_file):
        """Mock implementation of PythonUtils.is_script_file"""
        # Simple mock logic - if it's a single item ending with .py, it's a script file
        if isinstance(code_or_file, (list, tuple)) and len(code_or_file) == 1:
            return str(code_or_file[0]).endswith('.py')
        return False