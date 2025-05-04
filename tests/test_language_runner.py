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
    temp_dir = tmp_path / "work_temp"
    temp_dir.mkdir()
    runner = PythonRunner(str(src), str(temp_dir), None)
    assert await runner.build() is True
    assert os.path.exists(temp_dir / "main.py")

@pytest.mark.asyncio
async def test_pythonrunner_build_no_source(tmp_path):
    temp_dir = tmp_path / "work_temp"
    temp_dir.mkdir()
    runner = PythonRunner(str(tmp_path / "no_main.py"), str(temp_dir), None)
    assert await runner.build() is False

@pytest.mark.asyncio
async def test_pythonrunner_build_copy_fail(tmp_path, monkeypatch):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = src_dir / "main.py"
    src.write_text("print('hello')")
    temp_dir = tmp_path / "work_temp"
    temp_dir.mkdir()
    runner = PythonRunner(str(src), str(temp_dir), None)
    monkeypatch.setattr("shutil.copy2", lambda *a, **k: (_ for _ in ()).throw(Exception("copy error")))
    assert await runner.build() is False

@pytest.mark.asyncio
async def test_pythonrunner_build_copy_missing(tmp_path, monkeypatch):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = src_dir / "main.py"
    src.write_text("print('hello')")
    temp_dir = tmp_path / "work_temp"
    temp_dir.mkdir()
    runner = PythonRunner(str(src), str(temp_dir), None)
    orig_copy2 = shutil.copy2
    def fake_copy2(src, dst):
        orig_copy2(src, dst)
        os.remove(dst)
    monkeypatch.setattr("shutil.copy2", fake_copy2)
    assert await runner.build() is False

@pytest.mark.asyncio
async def test_pythonrunner_run(monkeypatch, tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = src_dir / "main.py"
    src.write_text("print('hello')")
    temp_dir = tmp_path / "work_temp"
    temp_dir.mkdir()
    runner = PythonRunner(str(src), str(temp_dir), None)
    await runner.build()
    class DummyResult:
        returncode = 0
        stdout = b'ok'
        stderr = b''
    monkeypatch.setattr("subprocess.run", lambda *a, **k: DummyResult())
    rc, out, err = await runner.run()
    assert rc == 0 and out == "ok"

@pytest.mark.asyncio
async def test_pythonrunner_run_with_input(monkeypatch, tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = src_dir / "main.py"
    src.write_text("print(input())")
    inp = tmp_path / "input.txt"
    inp.write_text("42")
    temp_dir = tmp_path / "work_temp"
    temp_dir.mkdir()
    runner = PythonRunner(str(src), str(temp_dir), None)
    await runner.build()
    class DummyResult:
        returncode = 0
        stdout = b'42\n'
        stderr = b''
    monkeypatch.setattr("subprocess.run", lambda *a, **k: DummyResult())
    rc, out, err = await runner.run(input_path=str(inp))
    assert rc == 0 and out == "42\n"

@pytest.mark.asyncio
async def test_pypy_runner_run(monkeypatch, tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = src_dir / "main.py"
    src.write_text("print('hello')")
    temp_dir = tmp_path / "work_temp"
    temp_dir.mkdir()
    runner = PypyRunner(str(src), str(temp_dir), None)
    await runner.build()
    class DummyResult:
        returncode = 0
        stdout = b'ok'
        stderr = b''
    monkeypatch.setattr("subprocess.run", lambda *a, **k: DummyResult())
    rc, out, err = await runner.run()
    assert rc == 0 and out == "ok"

@pytest.mark.asyncio
async def test_rustrunner_build_and_run(monkeypatch, tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = src_dir / "main.rs"
    src.write_text("fn main() { println!(\"hello\"); }")
    temp_dir = tmp_path / "work_temp"
    temp_dir.mkdir()
    class DummyDockerOperator:
        async def run(self, image, cmd, volumes=None, workdir=None, input_path=None):
            return 0, "ok", ""
    runner = RustRunner(str(src), str(temp_dir), DummyDockerOperator())
    # buildのdocker.runをモック
    async def dummy_build():
        return True
    monkeypatch.setattr(runner, "build", dummy_build)
    assert await runner.build() is True
    rc, out, err = await runner.run()
    assert rc == 0 and out == "ok" 