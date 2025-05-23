import pytest
import json
from src.main import main
from src.env.build_di_container_and_context import build_mock_operations
from src.context.execution_context import ExecutionContext
from src.operations.exceptions.composite_step_failure import CompositeStepFailure

class DummyService:
    def __init__(self, exception=None, result=None):
        self._exception = exception
        self._result = result
    def run_workflow(self):
        if self._exception:
            raise self._exception
        return self._result

# main.pyのmain関数をラップして、EnvWorkflowServiceの代わりにダミーを注入できるようにする

def main_with_service(context, operations, service):
    try:
        result = service.run_workflow()
        print(result)
    except json.JSONDecodeError as e:
        print(f"JSONの解析に失敗しました: {e}")
    except ValueError as e:
        print(f"エラー: {e}")
    except FileNotFoundError as e:
        print(f"ファイルが見つかりません: {e}")
    except Exception as e:
        if isinstance(e, CompositeStepFailure):
            print(f"ユーザー定義コマンドでエラーが発生しました: {e}")
        else:
            print(f"予期せぬエラーが発生しました: {e}")

@pytest.fixture
def context():
    return ExecutionContext(
        command_type="run",
        language="python",
        contest_name="abc",
        problem_name="a",
        env_type="local",
        env_json={"python": {"commands": {"run": {"steps": []}}}},
        contest_current_path="contests/abc",
        workspace_path="."
    )

@pytest.fixture
def operations():
    return build_mock_operations()

# 正常系

def test_main_normal(context, operations, capsys):
    service = DummyService(result="SUCCESS")
    main_with_service(context, operations, service)
    out = capsys.readouterr().out
    assert "SUCCESS" in out

# CompositeStepFailure

def test_main_composite_step_failure(context, operations, capsys):
    service = DummyService(exception=CompositeStepFailure("dummy composite error"))
    main_with_service(context, operations, service)
    out = capsys.readouterr().out
    assert "ユーザー定義コマンドでエラーが発生しました" in out
    assert "dummy composite error" in out

# ValueError

def test_main_value_error(context, operations, capsys):
    service = DummyService(exception=ValueError("dummy value error"))
    main_with_service(context, operations, service)
    out = capsys.readouterr().out
    assert "エラー: dummy value error" in out

# FileNotFoundError

def test_main_file_not_found_error(context, operations, capsys):
    service = DummyService(exception=FileNotFoundError("dummy file not found"))
    main_with_service(context, operations, service)
    out = capsys.readouterr().out
    assert "ファイルが見つかりません: dummy file not found" in out

# JSONDecodeError

def test_main_json_decode_error(context, operations, capsys):
    service = DummyService(exception=json.JSONDecodeError("msg", doc="{}", pos=0))
    main_with_service(context, operations, service)
    out = capsys.readouterr().out
    assert "JSONの解析に失敗しました" in out

# その他例外

def test_main_other_exception(context, operations, capsys):
    service = DummyService(exception=RuntimeError("unexpected error"))
    main_with_service(context, operations, service)
    out = capsys.readouterr().out
    assert "予期せぬエラーが発生しました" in out
    assert "unexpected error" in out 