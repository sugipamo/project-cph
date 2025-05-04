import pytest
from src.command_executor import CommandExecutor
from src.docker_operator import MockDockerOperator
from src.contest_file_manager import ContestFileManager
from src.file_operator import MockFileOperator
import asyncio
from command_executor import MockEditorOpener
from docker_operator import LocalDockerOperator
import os
import json

@pytest.mark.skip(reason="対話が必要なため自動テストから除外")
@pytest.mark.asyncio
async def test_login():
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        await executor.login()

@pytest.mark.asyncio
async def test_open(tmp_path):
    # テンプレート作成
    template_dir = tmp_path / "contest_template" / "python"
    template_dir.mkdir(parents=True, exist_ok=True)
    (template_dir / "main.py").write_text("print('hello')\n")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        mock_docker = MockDockerOperator()
        mock_file_operator = MockFileOperator(base_dir=tmp_path)
        mock_file_manager = ContestFileManager(mock_file_operator)
        executor = CommandExecutor(docker_operator=mock_docker, file_manager=mock_file_manager)
        await executor.open("abc300", "a", "python")
        assert mock_docker.calls[0][0] == "run_oj_download"
    finally:
        os.chdir(old_cwd)

@pytest.mark.asyncio
async def test_submit(tmp_path):
    from src.docker_operator import MockDockerOperator
    # 一時ディレクトリにcontest_current/info.jsonを作成
    contest_current = tmp_path / "contest_current"
    contest_current.mkdir()
    # main.pyも作成
    (contest_current / "python").mkdir()
    (contest_current / "python" / "main.py").write_text("print('hello')\n", encoding="utf-8")
    info = {"contest_name": "abc300", "problem_name": "a", "language_name": "python"}
    (contest_current / "info.json").write_text(json.dumps(info), encoding="utf-8")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        executor = CommandExecutor(docker_operator=MockDockerOperator())
        result = await executor.submit("abc300", "a", "python")
        assert result == (0, 'mock-stdout', 'mock-stderr')
    finally:
        os.chdir(old_cwd)

# @pytest.mark.asyncio
# async def test_test():
#     executor = CommandExecutor()
#     with pytest.raises(NotImplementedError):
#         await executor.test("abc300", "a", "python")

@pytest.mark.skip(reason="対話が必要なため自動テストから除外")
@pytest.mark.asyncio
async def test_execute_login():
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        await executor.execute("login")

@pytest.mark.asyncio
async def test_execute_open(tmp_path):
    # テンプレート作成
    template_dir = tmp_path / "contest_template" / "python"
    template_dir.mkdir(parents=True, exist_ok=True)
    (template_dir / "main.py").write_text("print('hello')\n")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        mock_docker = MockDockerOperator()
        mock_file_operator = MockFileOperator(base_dir=tmp_path)
        mock_file_manager = ContestFileManager(mock_file_operator)
        executor = CommandExecutor(docker_operator=mock_docker, file_manager=mock_file_manager)
        await executor.execute("open", "abc300", "a", "python")
        assert mock_docker.calls[0][0] == "run_oj_download"
    finally:
        os.chdir(old_cwd)

@pytest.mark.asyncio
async def test_execute_submit(tmp_path):
    from src.docker_operator import MockDockerOperator
    # 一時ディレクトリにcontest_current/info.jsonを作成
    contest_current = tmp_path / "contest_current"
    contest_current.mkdir()
    # main.pyも作成
    (contest_current / "python").mkdir()
    (contest_current / "python" / "main.py").write_text("print('hello')\n", encoding="utf-8")
    info = {"contest_name": "abc300", "problem_name": "a", "language_name": "python"}
    (contest_current / "info.json").write_text(json.dumps(info), encoding="utf-8")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        executor = CommandExecutor(docker_operator=MockDockerOperator())
        result = await executor.execute("submit", "abc300", "a", "python")
        assert result == (0, 'mock-stdout', 'mock-stderr')
    finally:
        os.chdir(old_cwd)

# @pytest.mark.asyncio
# async def test_execute_test():
#     executor = CommandExecutor()
#     with pytest.raises(NotImplementedError):
#         await executor.execute("test", "abc300", "a", "python")

@pytest.mark.asyncio
async def test_execute_invalid():
    executor = CommandExecutor()
    with pytest.raises(ValueError):
        await executor.execute("invalid_command")

def test_open_calls_editor_and_file_manager(tmp_path):
    # テンプレート作成
    template_dir = tmp_path / "contest_template" / "python"
    template_dir.mkdir(parents=True, exist_ok=True)
    (template_dir / "main.py").write_text("print('hello')\n")
    mock_editor = MockEditorOpener()
    mock_file_operator = MockFileOperator(base_dir=tmp_path)
    file_manager = ContestFileManager(mock_file_operator)
    mock_docker = LocalDockerOperator()
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        executor = CommandExecutor(
            docker_operator=mock_docker,
            file_manager=file_manager,
            editor_opener=mock_editor
        )
        asyncio.run(executor.open("abc300", "a", "python"))
        assert mock_editor.opened_paths == ["contest_current/python/main.py"]
    finally:
        os.chdir(old_cwd)

@pytest.mark.asyncio
async def test_open_with_none_dependencies(tmp_path):
    # テンプレート作成
    template_dir = tmp_path / "contest_template" / "python"
    template_dir.mkdir(parents=True, exist_ok=True)
    (template_dir / "main.py").write_text("print('hello')\n")
    # file_manager=None, editor_opener=None でも例外が発生しないか
    executor = CommandExecutor(docker_operator=MockDockerOperator(), file_manager=None, editor_opener=None)
    # 問題ディレクトリが存在しない場合でも例外が発生しないことを確認
    await executor.open("abc999", "z", "python")
    # editor_openerがNoneでもエラーにならない（デフォルトが使われる）
    executor2 = CommandExecutor(
        docker_operator=MockDockerOperator(),
        file_manager=ContestFileManager(MockFileOperator(base_dir=tmp_path)),
        editor_opener=None
    )
    await executor2.open("abc300", "a", "python")
    # file_managerがNoneでもエラーにならない（何も起きない）
    executor3 = CommandExecutor(docker_operator=MockDockerOperator(), file_manager=None, editor_opener=MockEditorOpener())
    await executor3.open("abc300", "a", "python")

def test_submit_contest_name_mismatch(tmp_path, capfd):
    # info.jsonをcontest_currentに作成
    contest_current = tmp_path / "contest_current"
    contest_current.mkdir()
    # main.pyも作成
    (contest_current / "python").mkdir()
    (contest_current / "python" / "main.py").write_text("print('hello')\n", encoding="utf-8")
    info = {"contest_name": "abc999", "problem_name": "a", "language_name": "python"}
    (contest_current / "info.json").write_text(json.dumps(info), encoding="utf-8")
    # カレントディレクトリを一時ディレクトリに
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        executor = CommandExecutor()
        result = asyncio.run(executor.submit("abc300", "a", "python"))
        out, _ = capfd.readouterr()
        assert "contest_current/info.jsonのcontest_name（abc999）と指定されたcontest_name（abc300）が異なります。提出を中止します。" in out
        assert result is None
    finally:
        os.chdir(old_cwd)

def test_submit_problem_name_mismatch(tmp_path, capfd):
    # info.jsonをcontest_currentに作成
    contest_current = tmp_path / "contest_current"
    contest_current.mkdir()
    # main.pyも作成
    (contest_current / "python").mkdir()
    (contest_current / "python" / "main.py").write_text("print('hello')\n", encoding="utf-8")
    info = {"contest_name": "abc300", "problem_name": "b", "language_name": "python"}
    (contest_current / "info.json").write_text(json.dumps(info), encoding="utf-8")
    # カレントディレクトリを一時ディレクトリに
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        executor = CommandExecutor()
        result = asyncio.run(executor.submit("abc300", "a", "python"))
        out, _ = capfd.readouterr()
        assert "contest_current/info.jsonのproblem_name（b）と指定されたproblem_name（a）が異なります。提出を中止します。" in out
        assert result is None
    finally:
        os.chdir(old_cwd)

def test_testresultformatter_basic():
    from src.command_executor import TestResultFormatter
    # サンプルデータ
    result = {
        "name": "sample-1.in",
        "result": (0, "2\n", ""),
        "time": 0.123,
        "expected": "2\n",
        "in_file": None,
    }
    formatter = TestResultFormatter(result)
    output = formatter.format()
    assert "sample-1.in" in output
    assert "AC" in output
    assert "0.123" in output
    assert "Expected | Output" in output
    assert "2        | 2" in output

def test_testresultformatter_with_input_and_error(tmp_path):
    from src.command_executor import TestResultFormatter
    # テスト用入力ファイル作成
    in_file = tmp_path / "sample-2.in"
    in_file.write_text("1 2 3\n4 5 6\n")
    result = {
        "name": "sample-2.in",
        "result": (1, "1\n2\n", "error occurred"),
        "time": 0.456,
        "expected": "1\n2\n",
        "in_file": str(in_file),
    }
    formatter = TestResultFormatter(result)
    output = formatter.format()
    assert "sample-2.in" in output
    assert "RE" in output
    assert "0.456" in output
    assert "1 2 3" in output and "4 5 6" in output  # input内容
    assert "error occurred" in output
    # 区切り線の位置（=は出力されなくなったので不要）
    # assert output.count("=") >= 1  # header下のみ
    assert output.count("-") >= 1  # error下 