import subprocess
import sys
import os
import json
import tempfile
import shutil
import pytest

def run_main_with_args(args):
    cmd = [sys.executable, "-m", "src.main"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

def test_main_value_error():
    # CommandRunner.runがValueErrorを投げるようにする
    import importlib
    import src.executor.command_runner as cr
    orig_run = cr.CommandRunner.run
    cr.CommandRunner.run = staticmethod(lambda args: (_ for _ in ()).throw(ValueError("valerr")))
    result = run_main_with_args(["dummy"])
    cr.CommandRunner.run = orig_run
    assert "エラー: valerr" in result.stdout
    assert result.returncode == 1

def test_main_file_not_found_error():
    import importlib
    import src.executor.command_runner as cr
    orig_run = cr.CommandRunner.run
    cr.CommandRunner.run = staticmethod(lambda args: (_ for _ in ()).throw(FileNotFoundError("nofile")))
    result = run_main_with_args(["dummy"])
    cr.CommandRunner.run = orig_run
    assert "ファイルが見つかりません" in result.stdout
    assert result.returncode == 1

def test_main_json_decode_error():
    import importlib
    import src.executor.command_runner as cr
    orig_run = cr.CommandRunner.run
    cr.CommandRunner.run = staticmethod(lambda args: (_ for _ in ()).throw(json.JSONDecodeError("msg", "doc", 1)))
    result = run_main_with_args(["dummy"])
    cr.CommandRunner.run = orig_run
    assert "JSONの解析に失敗しました" in result.stdout
    assert result.returncode == 1

def test_main_composite_step_failure():
    import importlib
    import src.executor.command_runner as cr
    from src.operations.exceptions.composite_step_failure import CompositeStepFailure
    orig_run = cr.CommandRunner.run
    cr.CommandRunner.run = staticmethod(lambda args: (_ for _ in ()).throw(CompositeStepFailure("failstep")))
    result = run_main_with_args(["dummy"])
    cr.CommandRunner.run = orig_run
    assert "ユーザー定義コマンドでエラーが発生しました" in result.stdout
    assert result.returncode == 1

def test_main_unexpected_exception():
    import importlib
    import src.executor.command_runner as cr
    orig_run = cr.CommandRunner.run
    cr.CommandRunner.run = staticmethod(lambda args: (_ for _ in ()).throw(RuntimeError("unexpected")))
    result = run_main_with_args(["dummy"])
    cr.CommandRunner.run = orig_run
    assert "予期せぬエラーが発生しました" in result.stdout
    assert result.returncode == 1

def test_main_import():
    import src.main

def test_main_callable():
    from src import main
    if hasattr(main, "main"):
        main.main() 