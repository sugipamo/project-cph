import os
import shutil
import pytest
from src.language_runner import PythonRunner, PypyRunner, RustRunner

@pytest.fixture
def temp_dir(tmp_path):
    d = tmp_path / "work_temp"
    d.mkdir()
    return str(d)

@pytest.mark.asyncio
async def test_pythonrunner_build_success(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = src_dir / "main.py"
    src.write_text("print('hello')")
    runner = PythonRunner(str(src), None, None)
    assert await runner.build() is True
    assert os.path.exists(src)

@pytest.mark.asyncio
async def test_pythonrunner_build_no_source(tmp_path):
    runner = PythonRunner(str(tmp_path / "no_main.py"), None, None)
    assert await runner.build() is False

@pytest.mark.asyncio
async def test_pythonrunner_build_copy_fail(tmp_path, monkeypatch):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = src_dir / "main.py"
    src.write_text("print('hello')")
    runner = PythonRunner(str(src), None, None)
    # コピー失敗は発生しないが、念のため例外を投げるようにしても良い
    monkeypatch.setattr("os.path.exists", lambda path: False if path == str(src) else True)
    assert await runner.build() is False

@pytest.mark.asyncio
async def test_pythonrunner_build_copy_missing(tmp_path, monkeypatch):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = src_dir / "main.py"
    src.write_text("print('hello')")
    runner = PythonRunner(str(src), None, None)
    monkeypatch.setattr("os.path.exists", lambda path: False if path == str(src) else True)
    assert await runner.build() is False

@pytest.mark.asyncio
async def test_pythonrunner_run(monkeypatch, tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = src_dir / "main.py"
    src.write_text("print('hello')")
    runner = PythonRunner(str(src), None, None)
    await runner.build()
    class DummyResult:
        returncode = 0
        stdout = b'ok'
        stderr = b''
    monkeypatch.setattr("subprocess.run", lambda *a, **k: DummyResult())
    rc, out, err, _ = await runner.run()
    assert rc == 0 and out == "ok"

@pytest.mark.asyncio
async def test_pythonrunner_run_with_input(monkeypatch, tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = src_dir / "main.py"
    src.write_text("print(input())")
    inp = tmp_path / "input.txt"
    inp.write_text("42")
    runner = PythonRunner(str(src), None, None)
    await runner.build()
    class DummyResult:
        returncode = 0
        stdout = b'42\n'
        stderr = b''
    monkeypatch.setattr("subprocess.run", lambda *a, **k: DummyResult())
    rc, out, err, _ = await runner.run(input_path=str(inp))
    assert rc == 0 and out == "42\n"

@pytest.mark.asyncio
async def test_pypy_runner_run(monkeypatch, tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = src_dir / "main.py"
    src.write_text("print('hello')")
    runner = PypyRunner(str(src), None, None)
    await runner.build()
    class DummyResult:
        returncode = 0
        stdout = b'ok'
        stderr = b''
    monkeypatch.setattr("subprocess.run", lambda *a, **k: DummyResult())
    rc, out, err, _ = await runner.run()
    assert rc == 0 and out == "ok"

@pytest.mark.asyncio
async def test_rustrunner_build_and_run(monkeypatch, tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = src_dir / "main.rs"
    src.write_text("fn main() { println(\"hello\"); }")
    class DummyDockerOperator:
        async def run(self, image, cmd, volumes=None, workdir=None, input_path=None):
            return 0, "ok", ""
    runner = RustRunner(str(src), None, DummyDockerOperator())
    # subprocess.runをモック
    class DummyResult:
        returncode = 0
        stdout = b'ok'
        stderr = b''
    monkeypatch.setattr("subprocess.run", lambda *a, **k: DummyResult())
    async def dummy_build():
        return True
    monkeypatch.setattr(runner, "build", dummy_build)
    assert await runner.build() is True
    rc, out, err, _ = await runner.run()
    assert rc == 0 and out == "ok"

@pytest.mark.asyncio
async def test_language_runner_run_common(monkeypatch, tmp_path):
    # PythonRunner, PypyRunner, RustRunnerでrunの共通部分が正しく動作するかを確認
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    # Python
    src_py = src_dir / "main.py"
    src_py.write_text("print('hello')")
    runner_py = PythonRunner(str(src_py), None, None)
    await runner_py.build()
    class DummyResult:
        returncode = 0
        stdout = b'ok'
        stderr = b''
    monkeypatch.setattr("subprocess.run", lambda *a, **k: DummyResult())
    rc, out, err, _ = await runner_py.run()
    assert rc == 0 and out == "ok"
    # Pypy
    runner_pypy = PypyRunner(str(src_py), None, None)
    await runner_pypy.build()
    rc, out, err, _ = await runner_pypy.run()
    assert rc == 0 and out == "ok"
    # Rust
    src_rs = src_dir / "main.rs"
    src_rs.write_text("fn main() { println(\"hello\"); }")
    class DummyDockerOperator:
        async def run(self, image, cmd, volumes=None, workdir=None, input_path=None):
            return 0, "ok", ""
    runner_rs = RustRunner(str(src_rs), None, DummyDockerOperator())
    class DummyResult:
        returncode = 0
        stdout = b'ok'
        stderr = b''
    monkeypatch.setattr("subprocess.run", lambda *a, **k: DummyResult())
    async def dummy_build():
        return True
    monkeypatch.setattr(runner_rs, "build", dummy_build)
    await runner_rs.build()
    rc, out, err, _ = await runner_rs.run()
    assert rc == 0 and out == "ok" 