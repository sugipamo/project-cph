import pytest
import pytest_asyncio
from src.command_parser import CommandParser
import json
import os
import io
import builtins
from src.file.file_operator import LocalFileOperator
from src.environment.test_environment import DockerTestExecutionEnvironment
import tempfile
import subprocess
from src.commands.command_test import CommandTest, UnifiedPathManager, CONTAINER_WORKSPACE

# 共通のダミーCtlクラス
class BaseDummyCtl:
    def is_container_running(self, name):
        return False
    def start_container(self, name, typ, volumes):
        pass
    def run_container(self, name, image, volumes):
        pass
    def exec_in_container(self, name, cmd):
        return True, "ok", ""
    def remove_container(self, name):
        pass
    def cp_from_container(self, name, src, dst):
        pass
    def copy_from_container(self, name, src, dst):
        return self.cp_from_container(name, src, dst)

def test_parse_prints_args():
    parser = CommandParser()
    parser.parse(["abc300", "open", "a", "python"])
    assert parser.parsed == {
        "contest_name": "abc300",
        "command": "open",
        "problem_name": "a",
        "language_name": "python",
        "exec_mode": None
    }

def test_parse_with_aliases():
    parser = CommandParser()
    parser.parse(["arc100", "o", "b", "rs"])
    assert parser.parsed == {
        "contest_name": "arc100",
        "command": "open",
        "problem_name": "b",
        "language_name": "rust",
        "exec_mode": None
    }

def test_parse_order_independence():
    parser = CommandParser()
    parser.parse(["t", "python", "agc001", "c"])
    assert parser.parsed == {
        "contest_name": "agc001",
        "command": "test",
        "problem_name": "c",
        "language_name": "python",
        "exec_mode": None
    }

def test_parse_missing_elements_warns():
    parser = CommandParser()
    parser.parse(["abc300", "a"])  # command, language_name不足
    assert parser.parsed["contest_name"] == "abc300"
    assert parser.parsed["problem_name"] == "a"
    assert parser.parsed["command"] is None
    assert parser.parsed["language_name"] is None

def test_parse_with_pypy_alias():
    parser = CommandParser()
    parser.parse(["ahc100", "submit", "ex", "py"])
    assert parser.parsed == {
        "contest_name": "ahc100",
        "command": "submit",
        "problem_name": "ex",
        "language_name": "pypy",
        "exec_mode": None
    }

def test_get_effective_args_with_infojson(tmp_path):
    # info.jsonを用意
    info = {"contest_name": "abc300", "problem_name": "a", "language_name": "python"}
    info_path = tmp_path / "info.json"
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(info, f)
    parser = CommandParser()
    parser.parse(["open", "python", "a"])
    args = parser.get_effective_args(str(info_path))
    assert args["contest_name"] == "abc300"
    assert args["problem_name"] == "a"
    assert args["language_name"] == "python"
    assert args["command"] == "open"

def test_command_test(monkeypatch, tmp_path):
    from src.commands.command_test import CommandTest
    # file_manager, file_operator, InfoJsonManager, ContainerClient, HANDLERS, ResultFormatter, os, printを全てmock
    class DummyFileManager:
        def __init__(self):
            self.file_operator = DummyFileOperator()
    class DummyFileOperator:
        def exists(self, path):
            return True
        def rmtree(self, path):
            self.rmtree_called = True
        def makedirs(self, path, exist_ok=False):
            self.makedirs_called = True
        def copy(self, src, dst):
            self.copy_called = (src, dst)
        def copytree(self, src, dst):
            self.copytree_called = (src, dst)
        def glob(self, pat):
            return ["test1.in", "test2.in"]
        def open(self, path, mode="r", encoding=None):
            import io
            return io.StringIO("")
    class DummyInfoJsonManager:
        def __init__(self, path):
            self.data = {"contest_name": "abc", "problem_name": "a", "containers": [{"name": "test1", "type": "test"}]}
        def get_containers(self, type=None):
            if type == "test":
                return [{"name": "test1", "type": "test"}]
            return []
        def save(self):
            self.saved = True
    class DummyCtl(BaseDummyCtl):
        pass
    class DummyHandler:
        def build(self, ctl, container, source_path):
            return (True, "buildok", "")
        def run(self, ctl, container, in_file, src):
            return (0, "out", "")
    # HANDLERS, ResultFormatter, InfoJsonManager, ContainerClient
    monkeypatch.setitem(__import__("src.environment.test_language_handler", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setitem(__import__("src.commands.command_test", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setattr("src.commands.command_test.ResultFormatter", lambda r: type("F", (), {"format": lambda self: "F"})())
    monkeypatch.setattr("src.commands.command_test.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.file.info_json_manager.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.commands.command_test.ContainerClient", DummyCtl)
    # os, print
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    monkeypatch.setattr(os, "makedirs", lambda *a, **k: None)
    monkeypatch.setattr("builtins.print", lambda *a, **k: None)
    # open, existsのモック
    import builtins
    orig_open = builtins.open
    orig_exists = os.path.exists
    def fake_open(path, mode="r", encoding=None):
        if path.endswith(".out"):
            from io import StringIO
            return StringIO("expected\n")
        return orig_open(path, mode, encoding=encoding) if orig_open else None
    def fake_exists(path):
        if path.endswith(".out"):
            return True
        return orig_exists(path)
    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(os.path, "exists", fake_exists)
    # テスト用Dockerfileを作成し、dockerfile_mapを注入
    with tempfile.NamedTemporaryFile("w+b", delete=False) as f:
        f.write(b"FROM python:3.8\n")
        f.flush()
        dockerfile_path = f.name
    dockerfile_map = {"python": dockerfile_path}
    # DockerPoolにDI
    from src.execution_client.container.pool import ContainerPool
    fm = DummyFileManager()
    cmd = CommandTest(fm, DummyEnv(fm.file_operator))
    cmd.env.pool = ContainerPool(dockerfile_map=dockerfile_map)
    # subprocess.runをモック（docker build等が失敗しないように）
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: type("Dummy", (), {"stdout": "", "returncode": 0})())
    # prepare_test_environment, collect_test_cases
    temp_source_path, temp_test_dir = cmd.prepare_test_environment("abc", "a", "python")
    temp_in_files, out_files = cmd.collect_test_cases(temp_test_dir, fm.file_operator)
    assert len(temp_in_files) == 2
    # get_test_containers_from_info
    assert cmd.get_test_containers_from_info() == ["test1"]
    # run_test_cases
    import asyncio
    results = asyncio.run(cmd.run_test_cases("src", ["test1.in"], "python"))
    assert results[0]["result"][0] in (0, 1)
    # print_test_results
    cmd.print_test_results([(True, "out", "")])
    # run_test_return_results
    res = asyncio.run(cmd.run_test_return_results("abc", "a", "python"))
    os.remove(dockerfile_path)
    assert isinstance(res, list)
    for r in res:
        assert "result" in r
        assert r["result"][0] in (0, 1)
    # テスト終了後にopen, existsを元に戻す
    monkeypatch.setattr(builtins, "open", orig_open)
    monkeypatch.setattr(os.path, "exists", orig_exists)
    # is_all_ac
    assert cmd.is_all_ac([{"result": (0, "foo", ""), "expected": "foo"}]) is True
    assert cmd.is_all_ac([{"result": (1, "foo", ""), "expected": "foo"}]) is False
    assert cmd.is_all_ac([{"result": (0, "bar", ""), "expected": "foo"}]) is False

def test_command_executor_execute(monkeypatch):
    from src.command_executor import CommandExecutor
    class DummyHandler:
        def __init__(self):
            self.called = False
        async def login(self):
            self.called = True
            return "login"
        async def open(self, c, p, l):
            self.called = (c, p, l)
            return "open"
        async def submit(self, c, p, l):
            self.called = (c, p, l)
            return "submit"
        async def run_test(self, c, p, l):
            self.called = (c, p, l)
            return "test"
    # 各ハンドラをダミーに差し替え
    ce = CommandExecutor()
    dummy_login = DummyHandler()
    dummy_open = DummyHandler()
    dummy_submit = DummyHandler()
    dummy_test = DummyHandler()
    ce.login_handler = dummy_login
    ce.open_handler = dummy_open
    ce.submit_handler = dummy_submit
    ce.test_handler = dummy_test
    import asyncio
    # login
    assert asyncio.run(ce.execute("login")) == "login"
    # open
    assert asyncio.run(ce.execute("open", "c", "p", "l")) == "open"
    # submit
    assert asyncio.run(ce.execute("submit", "c", "p", "l")) == "submit"
    # test
    assert asyncio.run(ce.execute("test", "c", "p", "l")) == "test"
    # 未対応コマンド
    import pytest
    with pytest.raises(ValueError):
        asyncio.run(ce.execute("unknown")) 

def test_command_login_not_implemented():
    from src.commands.command_login import CommandLogin
    import pytest
    import asyncio
    with pytest.raises(NotImplementedError):
        asyncio.run(CommandLogin().login()) 

def test_main_help(monkeypatch, capsys):
    import sys
    monkeypatch.setattr(sys, "argv", ["main.py", "--help"])
    from src import main as mainmod
    mainmod.main()
    out = capsys.readouterr().out
    assert "使い方" in out

def test_main_missing_args(monkeypatch, capsys):
    import sys
    # コマンド名が入らないようにする
    monkeypatch.setattr(sys, "argv", ["main.py", "abc300", "a", "python"])
    from src import main as mainmod
    mainmod.main()
    out = capsys.readouterr().out
    assert "エラー" in out and "不足" in out

def test_main_unknown_command(monkeypatch, capsys):
    import sys
    # コマンド名は明示的にunknown
    monkeypatch.setattr(sys, "argv", ["main.py", "abc300", "unknown", "a", "python"])
    from src import main as mainmod
    mainmod.main()
    out = capsys.readouterr().out
    # 未知コマンドは不足エラーになる
    assert "エラー" in out and "不足" in out

def test_main_command_branches(monkeypatch):
    import sys
    from src import main as mainmod
    # 各コマンド分岐をダミーexecutorで副作用なくテスト
    class DummyExecutor:
        def __init__(self, *a, **k): pass
        async def open(self, c, p, l):
            DummyExecutor.called = ("open", c, p, l)
        async def execute(self, *a, **k):
            DummyExecutor.called = ("login",)
        async def submit(self, c, p, l):
            DummyExecutor.called = ("submit", c, p, l)
        async def run_test(self, c, p, l):
            DummyExecutor.called = ("test", c, p, l)
    monkeypatch.setattr(mainmod, "CommandExecutor", lambda *a, **k: DummyExecutor())
    # open
    monkeypatch.setattr(sys, "argv", ["main.py", "abc300", "open", "a", "python"])
    DummyExecutor.called = None
    mainmod.main()
    assert DummyExecutor.called == ("open", "abc300", "a", "python")
    # login
    monkeypatch.setattr(sys, "argv", ["main.py", "login"])
    DummyExecutor.called = None
    mainmod.main()
    assert DummyExecutor.called == ("login",)
    # submit
    monkeypatch.setattr(sys, "argv", ["main.py", "abc300", "submit", "a", "python"])
    DummyExecutor.called = None
    mainmod.main()
    assert DummyExecutor.called == ("submit", "abc300", "a", "python")
    # test
    monkeypatch.setattr(sys, "argv", ["main.py", "abc300", "test", "a", "python"])
    DummyExecutor.called = None
    mainmod.main()
    assert DummyExecutor.called == ("test", "abc300", "a", "python") 

def test_command_test_build_fail(monkeypatch):
    from src.commands.command_test import CommandTest
    class DummyFileManager:
        def __init__(self):
            self.file_operator = None
    class DummyInfoJsonManager:
        def __init__(self, path):
            self.data = {"contest_name": "abc", "problem_name": "a", "containers": [{"name": "test1", "type": "test"}]}
        def get_containers(self, type=None):
            if type == "test":
                return [{"name": "test1", "type": "test"}]
            return []
        def save(self):
            self.saved = True
    class DummyCtl(BaseDummyCtl):
        pass
    class DummyHandler:
        def build(self, ctl, container, source_path):
            return (False, "", "build error!")
        def run(self, ctl, container, in_file, src):
            return (0, "", "exec error!")
    monkeypatch.setitem(__import__("src.environment.test_language_handler", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setitem(__import__("src.commands.command_test", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setattr("src.commands.command_test.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.file.info_json_manager.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.commands.command_test.ContainerClient", DummyCtl)
    fm = DummyFileManager()
    cmd = CommandTest(fm, DummyEnv())
    import asyncio
    results = asyncio.run(cmd.run_test_cases("src", ["test1.in"], "python"))
    assert results == []

def test_command_test_run_fail_and_retry(monkeypatch):
    from src.commands.command_test import CommandTest
    class DummyFileManager:
        def __init__(self):
            self.file_operator = None
    class DummyInfoJsonManager:
        def __init__(self, path):
            self.data = {"contest_name": "abc", "problem_name": "a", "containers": [{"name": "test1", "type": "test"}]}
        def get_containers(self, type=None):
            if type == "test":
                return [{"name": "test1", "type": "test"}]
            return []
        def save(self):
            self.saved = True
    class DummyCtl(BaseDummyCtl):
        pass
    class DummyHandler:
        def __init__(self):
            self.calls = 0
        def build(self, ctl, container, source_path):
            return (True, "", "")
        def run(self, ctl, container, in_file, src):
            self.calls += 1
            return (1, "out", "")
    handler = DummyHandler()
    monkeypatch.setitem(__import__("src.environment.test_language_handler", fromlist=["HANDLERS"]).HANDLERS, "python", handler)
    monkeypatch.setitem(__import__("src.commands.command_test", fromlist=["HANDLERS"]).HANDLERS, "python", handler)
    monkeypatch.setattr("src.commands.command_test.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.file.info_json_manager.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.commands.command_test.ContainerClient", DummyCtl)
    fm = DummyFileManager()
    cmd = CommandTest(fm, DummyEnv())
    import asyncio
    results = asyncio.run(cmd.run_test_cases("src", ["test1.in"], "python"))
    assert results[0]["result"][0] == 1
    assert results[0]["attempt"] == 1

def test_command_test_multiple_cases_and_containers(monkeypatch):
    from src.commands.command_test import CommandTest
    class DummyFileManager:
        def __init__(self):
            self.file_operator = None
    class DummyInfoJsonManager:
        def __init__(self, path):
            self.data = {"contest_name": "abc", "problem_name": "a", "containers": [
                {"name": "test1", "type": "test"},
                {"name": "test2", "type": "test"}
            ]}
        def get_containers(self, type=None):
            if type == "test":
                return [
                    {"name": "test1", "type": "test"},
                    {"name": "test2", "type": "test"}
                ]
            return []
        def save(self):
            self.saved = True
    class DummyCtl(BaseDummyCtl):
        pass
    class DummyHandler:
        def build(self, ctl, container, src):
            return (True, "", "")
        def run(self, ctl, container, in_file, src):
            return (True, f"out-{container}", "")
    monkeypatch.setitem(__import__("src.environment.test_language_handler", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setitem(__import__("src.commands.command_test", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setattr("src.commands.command_test.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.file.info_json_manager.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.commands.command_test.ContainerClient", DummyCtl)
    # open, existsのモック
    import builtins, os
    orig_open = builtins.open
    orig_exists = os.path.exists
    def fake_open(path, mode="r", encoding=None):
        if path.endswith(".out"):
            from io import StringIO
            return StringIO(f"expected-{os.path.basename(path).replace('.out','')}")
        return orig_open(path, mode, encoding=encoding) if orig_open else None
    def fake_exists(path):
        if path.endswith(".out"):
            return True
        return orig_exists(path)
    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(os.path, "exists", fake_exists)
    fm = DummyFileManager()
    cmd = CommandTest(fm, DummyEnv())
    import asyncio
    # 2ケース・2コンテナ
    results = asyncio.run(cmd.run_test_cases("src", ["test1.in", "test2.in"], "python"))
    assert len(results) == 2
    assert results[0]["container"] == "test1"
    assert results[1]["container"] == "test2"
    # テスト終了後にopen, existsを元に戻す
    monkeypatch.setattr(builtins, "open", orig_open)
    monkeypatch.setattr(os.path, "exists", orig_exists)

def test_command_test_is_all_ac(monkeypatch):
    from src.commands.command_test import CommandTest
    fm = type("FM", (), {})()
    cmd = CommandTest(fm, DummyEnv())
    # AC
    results = [
        {"result": (0, "foo", ""), "expected": "foo"},
        {"result": (0, "bar", ""), "expected": "bar"}
    ]
    assert cmd.is_all_ac(results) is True
    # WA
    results_wa = [
        {"result": (0, "foo", ""), "expected": "foo"},
        {"result": (0, "baz", ""), "expected": "bar"}
    ]
    assert cmd.is_all_ac(results_wa) is False
    # RE
    results_re = [
        {"result": (1, "foo", "err"), "expected": "foo"}
    ]
    assert cmd.is_all_ac(results_re) is False

def test_command_test_outfile_not_exists(monkeypatch):
    from src.commands.command_test import CommandTest
    class DummyFileManager:
        def __init__(self):
            self.file_operator = None
    class DummyInfoJsonManager:
        def __init__(self, path):
            self.data = {"contest_name": "abc", "problem_name": "a", "containers": [{"name": "test1", "type": "test"}]}
        def get_containers(self, type=None):
            if type == "test":
                return [{"name": "test1", "type": "test"}]
            return []
        def save(self):
            self.saved = True
    class DummyCtl(BaseDummyCtl):
        pass
    class DummyHandler:
        def build(self, ctl, container, src):
            return (True, "", "")
        def run(self, ctl, container, in_file, src):
            return (0, "", "exec error!")
    monkeypatch.setitem(__import__("src.environment.test_language_handler", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setitem(__import__("src.commands.command_test", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setattr("src.commands.command_test.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.file.info_json_manager.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.commands.command_test.ContainerClient", DummyCtl)
    # open, existsのモック
    import builtins, os
    orig_open = builtins.open
    orig_exists = os.path.exists
    def fake_exists(path):
        if path.endswith(".out"):
            return False
        return orig_exists(path)
    monkeypatch.setattr(os.path, "exists", fake_exists)
    fm = DummyFileManager()
    cmd = CommandTest(fm, DummyEnv())
    import asyncio
    results = asyncio.run(cmd.run_test_cases("src", ["test1.in"], "python"))
    # expectedが空文字列であることを確認
    assert results[0]["expected"] == ""
    # テスト終了後にexistsを元に戻す
    monkeypatch.setattr(os.path, "exists", orig_exists)

def test_run_test_cases_infile_not_exist(monkeypatch):
    from src.commands.command_test import CommandTest
    class DummyHandler:
        def build(self, ctl, container, src):
            return (True, "", "")
        def run(self, ctl, container, in_file, src):
            return (False, "", "No such file")
    class DummyFileManager:
        def __init__(self):
            self.file_operator = None
    class DummyInfoJsonManager:
        def __init__(self, path):
            self.data = {"contest_name": "abc", "problem_name": "a", "containers": [{"name": "test1", "type": "test"}]}
        def get_containers(self, type=None):
            if type == "test":
                return [{"name": "test1", "type": "test"}]
            return []
        def save(self):
            self.saved = True
    class DummyCtl(BaseDummyCtl):
        pass
    monkeypatch.setitem(__import__("src.environment.test_language_handler", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setitem(__import__("src.commands.command_test", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setattr("src.commands.command_test.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.file.info_json_manager.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.commands.command_test.ContainerClient", DummyCtl)
    fm = DummyFileManager()
    cmd = CommandTest(fm, DummyEnv())
    import asyncio
    results = asyncio.run(cmd.run_test_cases("src", ["notfound.in"], "python"))
    assert results[0]["result"][0] == 1 or results[0]["stderr"] == "No such file"

def test_to_container_path():
    from src.commands.command_test import HOST_PROJECT_ROOT, CONTAINER_WORKSPACE
    cmd = DummyCommandTestNoEnv(None)
    host_path = f"{HOST_PROJECT_ROOT}/.temp/test/sample-1.in"
    cont_path = cmd.to_container_path(host_path)
    assert cont_path.startswith(CONTAINER_WORKSPACE)
    assert cont_path.endswith(".temp/test/sample-1.in")

def test_build_in_container():
    class DummyHandler:
        def build(self, ctl, container, source_path):
            return (True, "buildok", "")
    cmd = DummyCommandTestNoEnv(None)
    ctl = object()
    handler = DummyHandler()
    ok, stdout, stderr = cmd.build_in_container(ctl, handler, "container1", "src.py")
    assert ok is True
    assert stdout == "buildok"

def test_select_container_for_case():
    cmd = DummyCommandTestNoEnv(None)
    containers = ["c1", "c2"]
    assert cmd.select_container_for_case(containers, 0) == "c1"
    assert cmd.select_container_for_case(containers, 1) == "c2"
    assert cmd.select_container_for_case(containers, 2) == "c2"

def test_ensure_container_running():
    class DummyCtl(BaseDummyCtl):
        def __init__(self):
            self.started = []
        def is_container_running(self, name):
            return name == "running"
        def start_container(self, name, image, volumes):
            self.started.append((name, image, volumes))
        def run_container(self, name, image, volumes):
            self.started.append((name, image, volumes))
    cmd = DummyCommandTestNoEnv(None)
    ctl = DummyCtl()
    # already running
    cmd.ensure_container_running(ctl, "running", "img")
    assert ctl.started == []
    # not running
    cmd.ensure_container_running(ctl, "notrunning", "img")
    assert ctl.started[-1][0] == "notrunning"

def test_run_single_test_case():
    class DummyCtl(BaseDummyCtl):
        def remove_container(self, name):
            self.removed = name
        def start_container(self, name, image, volumes):
            self.started = (name, image, volumes)
    class DummyHandler:
        def __init__(self):
            self.calls = 0
        def run(self, ctl, container, in_file, source_path):
            self.calls += 1
            if self.calls == 1:
                return False, "", "err"
            return True, "ok", ""
    cmd = DummyCommandTestNoEnv(None)
    ctl = DummyCtl()
    handler = DummyHandler()
    # 1回目失敗、2回目成功
    ok, stdout, stderr, attempt = cmd.run_single_test_case(ctl, handler, "cont", "in", "src", "img", retry=2)
    assert ok is True
    assert stdout == "ok"
    assert attempt == 2 

def test_run_single_test_case_retry_integration():
    class DummyCtl(BaseDummyCtl):
        def __init__(self):
            self.calls = []
        def remove_container(self, name):
            self.calls.append(f"remove:{name}")
        def start_container(self, name, image, volumes):
            self.calls.append(f"start:{name}:{image}")
    class DummyHandler:
        def __init__(self):
            self.calls = 0
        def run(self, ctl, container, in_file, source_path):
            self.calls += 1
            if self.calls == 1:
                return False, "", "err"
            return True, "ok", ""
    cmd = DummyCommandTestNoEnv(None)
    ctl = DummyCtl()
    handler = DummyHandler()
    ok, stdout, stderr, attempt = cmd.run_single_test_case(ctl, handler, "cont", "in", "src", "img")
    assert ok is True
    assert stdout == "ok"
    assert attempt == 2
    # 1回目失敗時にremove/startが呼ばれていること
    assert ctl.calls[0].startswith("remove:")
    assert ctl.calls[1].startswith("start:") 

def test_run_test_cases_integration():
    from src.commands.command_test import CommandTest
    from src.environment.test_language_handler import PythonTestHandler, HANDLERS
    class DummyCtl(BaseDummyCtl):
        def __init__(self):
            self.running = set()
            self.started = []
            self.removed = []
        def is_container_running(self, name):
            return name in self.running
        def start_container(self, name, image, volumes):
            self.running.add(name)
            self.started.append((name, image))
        def remove_container(self, name):
            self.running.discard(name)
            self.removed.append(name)
    class DummyHandler:
        def __init__(self):
            self.build_called = False
            self.run_calls = []
        def build(self, ctl, container, source_path):
            self.build_called = True
            return True, "buildok", ""
        def run(self, ctl, container, in_file, source_path):
            self.run_calls.append((container, in_file, source_path))
            return True, "output", ""
    class DummyFileManager:
        def __init__(self):
            self.file_operator = None
    class DummyInfoJsonManager:
        def __init__(self, path):
            self.data = {"contest_name": "abc", "problem_name": "a", "containers": [
                {"name": "cont1", "type": "test"},
                {"name": "cont2", "type": "test"}
            ]}
        def get_containers(self, type=None):
            return self.data["containers"]
        def save(self):
            pass
    import builtins
    import types
    # patch HANDLERS, InfoJsonManager, ContainerClient
    from src.commands import command_test
    orig_handler = HANDLERS["python"]
    handler = DummyHandler()
    command_test.HANDLERS["python"] = handler
    command_test.InfoJsonManager = DummyInfoJsonManager
    command_test.ContainerClient = DummyCtl
    fm = DummyFileManager()
    # DummyEnvのrun_test_caseをhandler.runを呼ぶように差し替え
    class IntegrationEnv(DummyEnv):
        def run_test_case(self, language_name, container, cont_in_file, cont_temp_source_path, retry=3):
            return handler.run(None, container, cont_in_file, cont_temp_source_path) + (1,)
    cmd = CommandTest(fm, IntegrationEnv())
    # テストケース2件
    temp_source_path = "src/main.py"
    temp_in_files = ["test1.in", "test2.in"]
    try:
        results = builtins.__import__("asyncio").run(cmd.run_test_cases(temp_source_path, temp_in_files, "python"))
        # build, run, container起動、パス変換、結果収集がすべて呼ばれていること
        assert handler.build_called is True
        assert len(handler.run_calls) == 2
        assert results[0]["result"][1] == "output"
        assert results[1]["result"][1] == "output"
    finally:
        HANDLERS["python"] = orig_handler

def test_run_test_cases_build_fail():
    from src.commands.command_test import CommandTest
    from src.environment.test_language_handler import HANDLERS
    class DummyCtl(BaseDummyCtl):
        pass
    class DummyHandler:
        def build(self, ctl, container, source_path):
            return False, "", "build error!"
        def run(self, ctl, container, in_file, source_path):
            raise AssertionError("run should not be called if build fails")
    class DummyFileManager:
        def __init__(self):
            self.file_operator = None
    class DummyInfoJsonManager:
        def __init__(self, path):
            self.data = {"contest_name": "abc", "problem_name": "a", "containers": [
                {"name": "cont1", "type": "test"}
            ]}
        def get_containers(self, type=None):
            return self.data["containers"]
        def save(self):
            pass
    import builtins
    from src.commands import command_test
    orig_handler = HANDLERS["python"]
    command_test.HANDLERS["python"] = DummyHandler()
    command_test.InfoJsonManager = DummyInfoJsonManager
    command_test.ContainerClient = DummyCtl
    fm = DummyFileManager()
    cmd = CommandTest(fm, DummyEnv())
    temp_source_path = "src/main.py"
    temp_in_files = ["test1.in"]
    try:
        results = builtins.__import__("asyncio").run(cmd.run_test_cases(temp_source_path, temp_in_files, "python"))
        assert results == []
    finally:
        HANDLERS["python"] = orig_handler

def test_run_test_cases_run_all_fail():
    from src.commands.command_test import CommandTest
    from src.environment.test_language_handler import HANDLERS
    class DummyCtl(BaseDummyCtl):
        pass
    class DummyHandler:
        def build(self, ctl, container, source_path):
            return True, "buildok", ""
        def run(self, ctl, container, in_file, source_path):
            return 1, "", "exec error!"
    class DummyFileManager:
        def __init__(self):
            self.file_operator = None
    class DummyInfoJsonManager:
        def __init__(self, path):
            self.data = {"contest_name": "abc", "problem_name": "a", "containers": [
                {"name": "cont1", "type": "test"}
            ]}
        def get_containers(self, type=None):
            return self.data["containers"]
        def save(self):
            pass
    import builtins
    from src.commands import command_test
    orig_handler = HANDLERS["python"]
    command_test.HANDLERS["python"] = DummyHandler()
    command_test.InfoJsonManager = DummyInfoJsonManager
    command_test.ContainerClient = DummyCtl
    fm = DummyFileManager()
    cmd = CommandTest(fm, DummyEnv(fm.file_operator))
    temp_source_path = "src/main.py"
    temp_in_files = ["test1.in"]
    try:
        results = builtins.__import__("asyncio").run(cmd.run_test_cases(temp_source_path, temp_in_files, "python"))
        # run_test_caseの返り値に合わせてassertを修正
        assert results[0]["result"][0] == 1
        assert "exec error!" in results[0]["result"][2]
    finally:
        HANDLERS["python"] = orig_handler

def test_run_test_cases_empty():
    from src.commands.command_test import CommandTest
    from src.environment.test_language_handler import HANDLERS
    class DummyCtl(BaseDummyCtl):
        pass
    class DummyHandler:
        def build(self, ctl, container, source_path):
            return True, "buildok", ""
        def run(self, ctl, container, source_path):
            raise AssertionError("run should not be called if no test cases")
    class DummyFileManager:
        def __init__(self):
            self.file_operator = None
    class DummyInfoJsonManager:
        def __init__(self, path):
            self.data = {"contest_name": "abc", "problem_name": "a", "containers": [
                {"name": "cont1", "type": "test"}
            ]}
        def get_containers(self, type=None):
            return self.data["containers"]
        def save(self):
            pass
    import builtins
    from src.commands import command_test
    orig_handler = HANDLERS["python"]
    command_test.HANDLERS["python"] = DummyHandler()
    command_test.InfoJsonManager = DummyInfoJsonManager
    command_test.ContainerClient = DummyCtl
    fm = DummyFileManager()
    cmd = CommandTest(fm, DummyEnv())
    temp_source_path = "src/main.py"
    temp_in_files = []
    try:
        results = builtins.__import__("asyncio").run(cmd.run_test_cases(temp_source_path, temp_in_files, "python"))
        assert results == []
    finally:
        HANDLERS["python"] = orig_handler 

# CommandTestのユーティリティ系テスト用に、test_envを使わないダミーサブクラスを用意
class DummyEnv:
    def __init__(self, file_operator=None):
        self.file_operator = file_operator
    def to_container_path(self, host_path):
        import os
        idx = host_path.find(".temp/")
        subpath = host_path[idx:] if idx >= 0 else os.path.basename(host_path)
        return f"{CONTAINER_WORKSPACE}/{subpath}"
    def prepare_source_code(self, contest_name, problem_name, language_name):
        return f"/tmp/{contest_name}_{problem_name}_{language_name}.py"
    def prepare_test_cases(self, contest_name, problem_name):
        # .tempディレクトリ作成を模倣
        if self.file_operator:
            self.file_operator.makedirs(".temp", exist_ok=True)
            self.file_operator.makedirs(".temp/test", exist_ok=True)
        else:
            from src.file.file_operator import LocalFileOperator
            op = LocalFileOperator()
            op.makedirs(".temp", exist_ok=True)
            op.makedirs(".temp/test", exist_ok=True)
        return f"/tmp/{contest_name}_{problem_name}_testcases"
    def run_test_case(self, language_name, container, cont_in_file, cont_temp_source_path, retry=3):
        # テスト用ダミー: 4要素タプルで返す（stderrも適宜）
        if 'notfound' in str(cont_in_file):
            return 0, '', 'No such file', 1
        # 失敗時は常に0（False）
        return 0, '', 'exec error!', 1
    def adjust_containers(self, requirements, contest_name, problem_name, language_name):
        return requirements

class DummyCommandTestNoEnv(CommandTest):
    def __init__(self, file_manager, test_env=None):
        self.file_manager = file_manager
        self.env = test_env if test_env is not None else DummyEnv()
        self.upm = UnifiedPathManager() 

class DummyTestEnv:
    def adjust_containers(self, requirements, contest_name=None, problem_name=None, language_name=None):
        return requirements
    def download_testcases(self, url, test_dir_host):
        # テスト用: 何もしない
        pass
    def submit_via_ojtools(self, args, volumes, workdir):
        # テスト用: ojtoolsがいない場合はRuntimeErrorを投げる
        # テストでojtoolsがいない場合の分岐を再現
        if hasattr(self, 'no_ojtools') and self.no_ojtools:
            raise RuntimeError("ojtools用コンテナがsystem_info.jsonにありません")
        if any("no_ojtools" in str(a) for a in args):
            raise RuntimeError("ojtools用コンテナがsystem_info.jsonにありません")
        return True, "ok", "" 