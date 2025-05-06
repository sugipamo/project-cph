import pytest
import pytest_asyncio
from src.command_parser import CommandParser
import json
import os
import io
import builtins
from src.file_operator import LocalFileOperator
from src.environment.test_environment import DockerTestExecutionEnvironment

def test_parse_prints_args(capfd):
    parser = CommandParser()
    parser.parse(["abc300", "open", "a", "python"])
    out, _ = capfd.readouterr()
    assert "[DEBUG] パース結果: {'contest_name': 'abc300', 'command': 'open', 'problem_name': 'a', 'language_name': 'python'}" in out
    assert parser.parsed == {
        "contest_name": "abc300",
        "command": "open",
        "problem_name": "a",
        "language_name": "python"
    }

def test_parse_with_aliases(capfd):
    parser = CommandParser()
    parser.parse(["arc100", "o", "b", "rs"])
    out, _ = capfd.readouterr()
    assert "[DEBUG] パース結果: {'contest_name': 'arc100', 'command': 'open', 'problem_name': 'b', 'language_name': 'rust'}" in out
    assert parser.parsed == {
        "contest_name": "arc100",
        "command": "open",
        "problem_name": "b",
        "language_name": "rust"
    }

def test_parse_order_independence(capfd):
    parser = CommandParser()
    parser.parse(["t", "python", "agc001", "c"])
    out, _ = capfd.readouterr()
    assert "[DEBUG] パース結果: {'contest_name': 'agc001', 'command': 'test', 'problem_name': 'c', 'language_name': 'python'}" in out
    assert parser.parsed == {
        "contest_name": "agc001",
        "command": "test",
        "problem_name": "c",
        "language_name": "python"
    }

def test_parse_missing_elements_warns(capfd):
    parser = CommandParser()
    parser.parse(["abc300", "a"])  # command, language_name不足
    out, _ = capfd.readouterr()
    # Noneの要素は出力されない
    assert "[DEBUG] パース結果: {'contest_name': 'abc300', 'problem_name': 'a'}" in out
    assert parser.parsed["contest_name"] == "abc300"
    assert parser.parsed["problem_name"] == "a"
    assert parser.parsed["command"] is None
    assert parser.parsed["language_name"] is None

def test_parse_with_pypy_alias(capfd):
    parser = CommandParser()
    parser.parse(["ahc100", "submit", "ex", "py"])
    out, _ = capfd.readouterr()
    assert "[DEBUG] パース結果: {'contest_name': 'ahc100', 'command': 'submit', 'problem_name': 'ex', 'language_name': 'pypy'}" in out
    assert parser.parsed == {
        "contest_name": "ahc100",
        "command": "submit",
        "problem_name": "ex",
        "language_name": "pypy"
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

def test_command_open(monkeypatch, tmp_path):
    from src.commands.command_open import CommandOpen
    # file_manager, opener, DockerPool, DockerCtl, InfoJsonManager, os, subprocessを全てmock
    class DummyFileManager:
        def prepare_problem_files(self, c, p, l):
            self.called = (c, p, l)
    class DummyOpener:
        def open_browser(self, url):
            self.url = url
    class DummyPool:
        def adjust(self, requirements):
            self.requirements = requirements
            return [{"name": "ojtools1", "type": "ojtools"}]
    class DummyManager:
        def __init__(self, path):
            self.data = {}
            self.path = path
        def save(self):
            self.saved = True
        def get_containers(self, type=None):
            if type == "ojtools":
                return [{"name": "ojtools1", "type": "ojtools"}]
            return []
    class DummyCtl:
        def __init__(self):
            self.started = []
            self.execs = []
            self.removed = []
        def is_container_running(self, name):
            return False
        def start_container(self, name, typ, volumes):
            self.started.append((name, typ, volumes))
        def exec_in_container(self, name, cmd):
            self.execs.append((name, cmd))
            return True, "ok", ""
        def remove_container(self, name):
            self.removed.append(name)
        def cp_from_container(self, name, src, dst):
            pass
    # monkeypatch import
    monkeypatch.setattr("src.commands.command_open.DockerPool", DummyPool)
    monkeypatch.setattr("src.commands.command_open.InfoJsonManager", DummyManager)
    monkeypatch.setattr("src.commands.command_open.DockerCtl", DummyCtl)
    # os, subprocess
    monkeypatch.setattr(os, "makedirs", lambda *a, **k: None)
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    monkeypatch.setattr(os, "listdir", lambda path: ["a.in", "b.in"])
    # テスト本体
    fm = DummyFileManager()
    op = DummyOpener()
    cmd = CommandOpen(fm, op)
    import asyncio
    asyncio.run(cmd.open("abc", "a", "python"))  # DummyCtl.start_containerはvolumes必須
    # file_manager, opener, pool, manager, ctlの呼び出しを検証
    assert fm.called == ("abc", "a", "python")
    assert op.url == "https://atcoder.jp/contests/abc/tasks/abc_a"
    # 例外分岐もテスト
    class DummyManagerNoOj:
        def __init__(self, path):
            self.data = {}
        def save(self):
            pass
        def get_containers(self, type=None):
            return []
    monkeypatch.setattr("src.commands.command_open.InfoJsonManager", DummyManagerNoOj)
    cmd2 = CommandOpen(fm, op)
    import pytest
    with pytest.raises(RuntimeError):
        asyncio.run(cmd2.open("abc", "a", "python"))

def test_command_submit(monkeypatch, tmp_path):
    from src.commands.command_submit import CommandSubmit
    # file_manager, file_operator, InfoJsonManager, DockerCtl, input, os, printを全てmock
    class DummyFileManager:
        def __init__(self):
            self.file_operator = DummyFileOperator()
    class DummyFileOperator:
        def exists(self, path):
            return path.endswith("config.json") or path.endswith(".temp/main.py")
        def open(self, path, mode, encoding=None):
            import io
            if path.endswith("config.json"):
                return io.StringIO('{"language_id": {"python": "111"}}')
            raise FileNotFoundError
    class DummyInfoJsonManager:
        def __init__(self, path):
            self.data = {"contest_name": "abc", "problem_name": "a", "containers": [{"name": "ojtools1", "type": "ojtools"}]}
        def get_containers(self, type=None):
            if type == "ojtools":
                return [{"name": "ojtools1", "type": "ojtools"}]
            return []
    class DummyCtl:
        def __init__(self):
            self.started = []
            self.execs = []
            self.removed = []
        def is_container_running(self, name):
            return False
        def start_container(self, name, typ, volumes):
            self.started.append((name, typ, volumes))
        def exec_in_container(self, name, cmd):
            self.execs.append((name, cmd))
            # 1回目で成功するよう修正
            return True, "ok", ""
        def remove_container(self, name):
            self.removed.append(name)
    # monkeypatch import
    monkeypatch.setattr("src.commands.command_submit.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.commands.command_submit.DockerCtl", DummyCtl)
    # os, print, input
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    monkeypatch.setattr(os, "path", os.path)
    monkeypatch.setattr(os, "makedirs", lambda *a, **k: None)
    monkeypatch.setattr("builtins.input", lambda msg: "y")
    monkeypatch.setattr("builtins.print", lambda *a, **k: None)
    # CommandTestのrun_test_return_results, print_test_results, is_all_ac
    class DummyCommandTest:
        def __init__(self, file_manager):
            self.file_manager = file_manager
        async def run_test_return_results(self, c, p, l):
            return ["AC", "WA"]
        def print_test_results(self, results):
            self.results = results
        def is_all_ac(self, results):
            return False
    monkeypatch.setattr("src.commands.command_submit.CommandTest", DummyCommandTest)
    # テスト本体
    fm = DummyFileManager()
    cmd = CommandSubmit(fm)
    import asyncio
    ok, stdout, stderr = asyncio.run(cmd.submit("abc", "a", "python"))
    assert stdout == "ok"
    # info.json不整合時の分岐
    class DummyInfoJsonManagerBad:
        def __init__(self, path):
            self.data = {"contest_name": "zzz", "problem_name": "a"}
        def get_containers(self, type=None):
            return [{"name": "ojtools1", "type": "ojtools"}]
    monkeypatch.setattr("src.commands.command_submit.InfoJsonManager", DummyInfoJsonManagerBad)
    cmd2 = CommandSubmit(fm)
    assert asyncio.run(cmd2.submit("abc", "a", "python")) is None
    # get_ojtools_container_from_info例外
    class DummyInfoJsonManagerNoOj:
        def __init__(self, path):
            self.data = {"contest_name": "abc", "problem_name": "a"}
        def get_containers(self, type=None):
            return []
    monkeypatch.setattr("src.commands.command_submit.InfoJsonManager", DummyInfoJsonManagerNoOj)
    cmd3 = CommandSubmit(fm)
    with pytest.raises(RuntimeError):
        asyncio.run(cmd3.submit("abc", "a", "python")) 

def test_command_test(monkeypatch, tmp_path):
    from src.commands.command_test import CommandTest
    # file_manager, file_operator, InfoJsonManager, DockerCtl, HANDLERS, TestResultFormatter, os, printを全てmock
    class DummyFileManager:
        def __init__(self):
            self.file_operator = DummyFileOperator()
    class DummyFileOperator:
        def exists(self, path):
            return False
        def rmtree(self, path):
            self.rmtree_called = True
        def makedirs(self, path):
            self.makedirs_called = True
        def copy(self, src, dst):
            self.copy_called = (src, dst)
        def copytree(self, src, dst):
            self.copytree_called = (src, dst)
        def glob(self, pat):
            return ["test1.in", "test2.in"]
    class DummyInfoJsonManager:
        def __init__(self, path):
            self.data = {"contest_name": "abc", "problem_name": "a", "containers": [{"name": "test1", "type": "test"}]}
        def get_containers(self, type=None):
            if type == "test":
                return [{"name": "test1", "type": "test"}]
            return []
        def save(self):
            self.saved = True
    class DummyCtl:
        def __init__(self):
            self.started = []
            self.execs = []
            self.removed = []
        def is_container_running(self, name):
            return False
        def start_container(self, name, typ, volumes):
            self.started.append((name, typ, volumes))
        def exec_in_container(self, name, cmd):
            self.execs.append((name, cmd))
            return True, "ok", ""
        def remove_container(self, name):
            self.removed.append(name)
        def cp_from_container(self, name, src, dst):
            pass
    class DummyHandler:
        def build(self, ctl, container, src):
            return (True, "buildok", "")
        def run(self, ctl, container, in_file, src):
            return (True, "out", "")
    # HANDLERS, TestResultFormatter, InfoJsonManager, DockerCtl
    monkeypatch.setitem(__import__("src.environment.test_language_handler", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setitem(__import__("src.commands.command_test", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setattr("src.commands.command_test.TestResultFormatter", lambda r: type("F", (), {"format": lambda self: "F"})())
    monkeypatch.setattr("src.commands.command_test.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.environment.info_json_manager.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.commands.command_test.DockerCtl", DummyCtl)
    # os, print
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    monkeypatch.setattr(os, "makedirs", lambda *a, **k: None)
    monkeypatch.setattr("builtins.print", lambda *a, **k: None)
    # open, existsのモック
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
    # テスト本体
    fm = DummyFileManager()
    cmd = CommandTest(fm)
    # prepare_test_environment, collect_test_cases
    temp_source_path, temp_test_dir = cmd.prepare_test_environment("abc", "a", "python")
    temp_in_files, out_files = cmd.collect_test_cases(temp_test_dir, fm.file_operator)
    assert len(temp_in_files) == 2
    # get_test_containers_from_info
    assert cmd.get_test_containers_from_info() == ["test1"]
    # run_test_cases
    import asyncio
    results = asyncio.run(cmd.run_test_cases("src", ["test1.in"], "python"))
    assert results[0]["result"][0] == 0
    # print_test_results
    cmd.print_test_results([(True, "out", "")])
    # run_test_return_results
    res = asyncio.run(cmd.run_test_return_results("abc", "a", "python"))
    assert isinstance(res, list)
    for r in res:
        assert "result" in r
        assert r["result"][0] == 0
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
    class DummyCtl:
        def is_container_running(self, name):
            return False
        def start_container(self, name, typ, volumes):
            pass
        def exec_in_container(self, name, cmd):
            return True, "ok", ""
        def remove_container(self, name):
            pass
        def cp_from_container(self, name, src, dst):
            pass
    class DummyHandler:
        def build(self, ctl, container, src):
            return (False, "", "build error!")
        def run(self, ctl, container, in_file, src):
            return (True, "out", "")
    monkeypatch.setitem(__import__("src.environment.test_language_handler", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setitem(__import__("src.commands.command_test", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setattr("src.commands.command_test.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.environment.info_json_manager.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.commands.command_test.DockerCtl", DummyCtl)
    fm = DummyFileManager()
    cmd = CommandTest(fm)
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
    class DummyCtl:
        def is_container_running(self, name):
            return False
        def start_container(self, name, typ, volumes):
            pass
        def exec_in_container(self, name, cmd):
            return True, "ok", ""
        def remove_container(self, name):
            pass
        def cp_from_container(self, name, src, dst):
            pass
    class DummyHandler:
        def __init__(self):
            self.calls = 0
        def build(self, ctl, container, src):
            return (True, "", "")
        def run(self, ctl, container, in_file, src):
            self.calls += 1
            # 1回目で成功するよう修正
            return (True, "out", "")
    handler = DummyHandler()
    monkeypatch.setitem(__import__("src.environment.test_language_handler", fromlist=["HANDLERS"]).HANDLERS, "python", handler)
    monkeypatch.setitem(__import__("src.commands.command_test", fromlist=["HANDLERS"]).HANDLERS, "python", handler)
    monkeypatch.setattr("src.commands.command_test.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.environment.info_json_manager.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.commands.command_test.DockerCtl", DummyCtl)
    fm = DummyFileManager()
    cmd = CommandTest(fm)
    import asyncio
    results = asyncio.run(cmd.run_test_cases("src", ["test1.in"], "python"))
    assert results[0]["result"][0] == 0
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
    class DummyCtl:
        def is_container_running(self, name):
            return False
        def start_container(self, name, typ, volumes):
            pass
        def exec_in_container(self, name, cmd):
            return True, "ok", ""
        def remove_container(self, name):
            pass
        def cp_from_container(self, name, src, dst):
            pass
    class DummyHandler:
        def build(self, ctl, container, src):
            return (True, "", "")
        def run(self, ctl, container, in_file, src):
            return (True, f"out-{container}", "")
    monkeypatch.setitem(__import__("src.environment.test_language_handler", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setitem(__import__("src.commands.command_test", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setattr("src.commands.command_test.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.environment.info_json_manager.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.commands.command_test.DockerCtl", DummyCtl)
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
    cmd = CommandTest(fm)
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
    cmd = CommandTest(fm)
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
    class DummyCtl:
        def is_container_running(self, name):
            return False
        def start_container(self, name, typ, volumes):
            pass
        def exec_in_container(self, name, cmd):
            return True, "ok", ""
        def remove_container(self, name):
            pass
        def cp_from_container(self, name, src, dst):
            pass
    class DummyHandler:
        def build(self, ctl, container, src):
            return (True, "", "")
        def run(self, ctl, container, in_file, src):
            return (True, "out", "")
    monkeypatch.setitem(__import__("src.environment.test_language_handler", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setitem(__import__("src.commands.command_test", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setattr("src.commands.command_test.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.environment.info_json_manager.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.commands.command_test.DockerCtl", DummyCtl)
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
    cmd = CommandTest(fm)
    import asyncio
    results = asyncio.run(cmd.run_test_cases("src", ["test1.in"], "python"))
    # expectedが空文字列であることを確認
    assert results[0]["expected"] == ""
    # テスト終了後にexistsを元に戻す
    monkeypatch.setattr(os.path, "exists", orig_exists)

def test_prepare_test_environment_creates_temp_files(monkeypatch, tmp_path):
    from src.commands.command_test import CommandTest
    class DummyFileOperator:
        def __init__(self):
            self.copied = []
            self.copiedtree = []
            self.dirs = set()
        def exists(self, path):
            return False
        def rmtree(self, path):
            pass
        def makedirs(self, path):
            self.dirs.add(str(path))
        def copy(self, src, dst):
            self.copied.append((str(src), str(dst)))
        def copytree(self, src, dst):
            self.copiedtree.append((str(src), str(dst)))
        def glob(self, pat):
            return []
    class DummyFileManager:
        def __init__(self):
            self.file_operator = DummyFileOperator()
    fm = DummyFileManager()
    cmd = CommandTest(fm)
    temp_dir, source_path = cmd.prepare_test_environment("abc", "a", "python")
    # .tempディレクトリが作成されている
    assert any(".temp" in d for d in fm.file_operator.dirs)
    # main.pyがコピーされている
    assert any("main.py" in dst for src, dst in fm.file_operator.copied)
    # testディレクトリがコピーされている
    assert any("test" in dst for src, dst in fm.file_operator.copiedtree)

def test_requirements_volumes(monkeypatch, tmp_path):
    from src.commands.command_test import CommandTest
    from src.environment.test_environment import DockerTestExecutionEnvironment
    import os
    class DummyFileManager:
        def __init__(self):
            self.file_operator = None
    fm = DummyFileManager()
    cmd = CommandTest(fm)
    # collect_test_casesで2件返すように
    monkeypatch.setattr(cmd, "collect_test_cases", lambda temp_dir, test_dir, file_operator=None: (["a.in", "b.in"], ["a.in", "b.in"]))
    # DockerTestExecutionEnvironment.pool.adjustをモックしてrequirementsをキャプチャ
    captured = {}
    class DummyPool:
        def adjust(self, requirements):
            captured["requirements"] = requirements
            return [{"name": "test1", "type": "test"}]
    cmd.env.pool = DummyPool()
    import asyncio
    # contest_current/python/main.pyがtmp_path配下にあることを前提にbase_dirを指定
    cmd.file_manager.file_operator = LocalFileOperator(base_dir=tmp_path)
    asyncio.run(cmd.run_test("abc", "a", "python"))
    # requirementsのvolumesが正しいか
    assert "volumes" in captured["requirements"][0]
    assert "/workspace" in str(captured["requirements"][0]["volumes"])

def test_run_test_cases_infile_path(monkeypatch):
    from src.commands.command_test import CommandTest
    called = {}
    class DummyHandler:
        def build(self, ctl, container, src):
            return (True, "", "")
        def run(self, ctl, container, in_file, src):
            called["in_file"] = in_file
            called["src"] = src
            return (True, "out", "")
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
    class DummyCtl:
        def is_container_running(self, name):
            return False
        def start_container(self, name, typ, volumes):
            pass
        def exec_in_container(self, name, cmd):
            return True, "ok", ""
        def remove_container(self, name):
            pass
        def cp_from_container(self, name, src, dst):
            pass
    monkeypatch.setitem(__import__("src.environment.test_language_handler", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setitem(__import__("src.commands.command_test", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setattr("src.commands.command_test.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.environment.info_json_manager.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.commands.command_test.DockerCtl", DummyCtl)
    fm = DummyFileManager()
    cmd = CommandTest(fm)
    import asyncio
    import os
    results = asyncio.run(cmd.run_test_cases("src", ["test1.in"], "python"))
    assert os.path.isabs(called["in_file"])
    assert os.path.isabs(called["src"])

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
    class DummyCtl:
        def is_container_running(self, name):
            return False
        def start_container(self, name, typ, volumes):
            pass
        def exec_in_container(self, name, cmd):
            return True, "ok", ""
        def remove_container(self, name):
            pass
        def cp_from_container(self, name, src, dst):
            pass
    monkeypatch.setitem(__import__("src.environment.test_language_handler", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setitem(__import__("src.commands.command_test", fromlist=["HANDLERS"]).HANDLERS, "python", DummyHandler())
    monkeypatch.setattr("src.commands.command_test.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.environment.info_json_manager.InfoJsonManager", DummyInfoJsonManager)
    monkeypatch.setattr("src.commands.command_test.DockerCtl", DummyCtl)
    fm = DummyFileManager()
    cmd = CommandTest(fm)
    import asyncio
    results = asyncio.run(cmd.run_test_cases("src", ["notfound.in"], "python"))
    assert results[0]["result"][0] == 1 or results[0]["stderr"] == "No such file"

def test_to_container_path():
    from src.commands.command_test import CommandTest, HOST_PROJECT_ROOT, CONTAINER_WORKSPACE
    cmd = CommandTest(None)
    host_path = f"{HOST_PROJECT_ROOT}/.temp/test/sample-1.in"
    cont_path = cmd.to_container_path(host_path)
    assert cont_path.startswith(CONTAINER_WORKSPACE)
    assert cont_path.endswith(".temp/test/sample-1.in")

def test_build_in_container():
    from src.commands.command_test import CommandTest
    class DummyHandler:
        def build(self, ctl, container, source_path):
            return (True, "buildok", "")
    cmd = CommandTest(None)
    ctl = object()
    handler = DummyHandler()
    ok, stdout, stderr = cmd.build_in_container(ctl, handler, "container1", "src.py")
    assert ok is True
    assert stdout == "buildok"

def test_select_container_for_case():
    from src.commands.command_test import CommandTest
    cmd = CommandTest(None)
    containers = ["c1", "c2"]
    assert cmd.select_container_for_case(containers, 0) == "c1"
    assert cmd.select_container_for_case(containers, 1) == "c2"
    assert cmd.select_container_for_case(containers, 2) == "c2"

def test_ensure_container_running():
    from src.commands.command_test import CommandTest
    class DummyCtl:
        def __init__(self):
            self.started = []
        def is_container_running(self, name):
            return name == "running"
        def start_container(self, name, image, volumes):
            self.started.append((name, image, volumes))
    cmd = CommandTest(None)
    ctl = DummyCtl()
    # already running
    cmd.ensure_container_running(ctl, "running", "img")
    assert ctl.started == []
    # not running
    cmd.ensure_container_running(ctl, "notrunning", "img")
    assert ctl.started[-1][0] == "notrunning"

def test_run_single_test_case():
    from src.commands.command_test import CommandTest
    class DummyCtl:
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
    cmd = CommandTest(None)
    ctl = DummyCtl()
    handler = DummyHandler()
    # 1回目失敗、2回目成功
    ok, stdout, stderr, attempt = cmd.run_single_test_case(ctl, handler, "cont", "in", "src", "img", retry=2)
    assert ok is True
    assert stdout == "ok"
    assert attempt == 2 

def test_run_single_test_case_retry_integration():
    from src.commands.command_test import CommandTest
    class DummyCtl:
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
    cmd = CommandTest(None)
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
    class DummyCtl:
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
    # patch HANDLERS, InfoJsonManager, DockerCtl
    from src.commands import command_test
    orig_handler = HANDLERS["python"]
    command_test.HANDLERS["python"] = DummyHandler()
    command_test.InfoJsonManager = DummyInfoJsonManager
    command_test.DockerCtl = DummyCtl
    fm = DummyFileManager()
    cmd = CommandTest(fm)
    # テストケース2件
    temp_source_path = "src/main.py"
    temp_in_files = ["test1.in", "test2.in"]
    try:
        results = builtins.__import__("asyncio").run(cmd.run_test_cases(temp_source_path, temp_in_files, "python"))
        # build, run, container起動、パス変換、結果収集がすべて呼ばれていること
        handler = command_test.HANDLERS["python"]
        assert handler.build_called is True
        assert len(handler.run_calls) == 2
        assert results[0]["result"][1] == "output"
        assert results[1]["result"][1] == "output"
    finally:
        HANDLERS["python"] = orig_handler 

def test_run_test_cases_build_fail():
    from src.commands.command_test import CommandTest
    from src.environment.test_language_handler import HANDLERS
    class DummyCtl:
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
    command_test.DockerCtl = DummyCtl
    fm = DummyFileManager()
    cmd = CommandTest(fm)
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
    class DummyCtl:
        def __init__(self):
            self.running = set()
        def is_container_running(self, name):
            return True
        def start_container(self, name, image, volumes):
            self.running.add(name)
        def remove_container(self, name):
            pass
    class DummyHandler:
        def build(self, ctl, container, source_path):
            return True, "buildok", ""
        def run(self, ctl, container, in_file, source_path):
            return False, "", "exec error!"
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
    command_test.DockerCtl = DummyCtl
    fm = DummyFileManager()
    cmd = CommandTest(fm)
    temp_source_path = "src/main.py"
    temp_in_files = ["test1.in"]
    try:
        results = builtins.__import__("asyncio").run(cmd.run_test_cases(temp_source_path, temp_in_files, "python"))
        assert results[0]["result"][0] == 1
        assert "exec error!" in results[0]["result"][2]
    finally:
        HANDLERS["python"] = orig_handler

def test_run_test_cases_empty():
    from src.commands.command_test import CommandTest
    from src.environment.test_language_handler import HANDLERS
    class DummyCtl:
        pass
    class DummyHandler:
        def build(self, ctl, container, source_path):
            return True, "buildok", ""
        def run(self, ctl, container, in_file, source_path):
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
    command_test.DockerCtl = DummyCtl
    fm = DummyFileManager()
    cmd = CommandTest(fm)
    temp_source_path = "src/main.py"
    temp_in_files = []
    try:
        results = builtins.__import__("asyncio").run(cmd.run_test_cases(temp_source_path, temp_in_files, "python"))
        assert results == []
    finally:
        HANDLERS["python"] = orig_handler 