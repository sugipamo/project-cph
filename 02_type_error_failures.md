# TypeError関連のテスト失敗

## 失敗したテスト一覧

### Python Request関連
- `tests/python/test_python_request.py::test_python_request_repr - TypeError`
- `tests/python/test_python_request.py::test_python_request_code_string`
- `tests/python/test_python_request.py::test_python_request_script_file`
- `tests/python/test_python_request.py::test_python_request_with_cwd - TypeError`
- `tests/python/test_python_request.py::test_python_request_execute_exception`
- `tests/python/test_python_request.py::test_python_request_code_string_with_patch`
- `tests/python/test_python_request.py::test_python_request_script_file_with_patch`
- `tests/python/test_python_request.py::test_python_request_with_cwd_with_patch`
- `tests/python/test_python_request.py::test_python_request_execute_exception_with_patch`

### Python Utils関連
- `tests/python/test_python_utils.py::test_run_script_file - TypeError`
- `tests/python/test_python_utils.py::test_run_code_string_success - TypeError`
- `tests/python/test_python_utils.py::test_run_code_string_exception - TypeError`

### Shell Utils関連（遅いテスト）
- `tests_slow/test_shell_utils.py::test_run_subprocess_echo - TypeError`
- `tests_slow/test_shell_utils.py::test_run_subprocess_input - TypeError`
- `tests_slow/test_shell_utils.py::test_run_subprocess_timeout - TypeError`
- `tests_slow/test_shell_utils.py::test_start_interactive_and_enqueue_output_and_drain_queue`
- `tests_slow/test_shell_utils.py::test_enforce_timeout - TypeError`

### Test Fixtures関連
- `tests/test_conftest_fixtures.py::test_mock_infrastructure_fixture - TypeError`
- `tests/test_conftest_fixtures.py::test_mock_drivers_fixture - TypeError`
- `tests/test_conftest_fixtures.py::test_clean_mock_state_fixture - TypeError`

## 問題の分析

この分類のテストは主に型エラーが原因で失敗しています。以下の領域で問題が発生：

1. **Python Request/Utils**: Python実行関連の機能で型の不整合が発生
2. **Shell Utils**: シェルコマンド実行ユーティリティで型エラー
3. **Test Fixtures**: テストフィクスチャの設定で型の問題

これらのエラーは、メソッドの引数の型や戻り値の型が期待と異なっているか、デフォルト値の禁止ルールに関連した問題の可能性があります。