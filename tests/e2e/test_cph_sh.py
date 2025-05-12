import subprocess
import pytest
import os

CPH_SH = os.path.abspath("./cph.sh")
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__ + "/../../"))

pytestmark = pytest.mark.skip(reason="e2eテスト一時スキップ（リファクタ対応中）")

@pytest.mark.parametrize("args", [
    ["open", "abc301", "a", "python"],
    ["test", "abc301", "a", "python", "local"],
    ["test", "abc301", "a", "python", "docker"],
    ["open", "abc301", "a", "rust"],
    ["test", "abc301", "a", "rust", "local"],
    ["test", "abc301", "a", "rust", "docker"],
])
def test_cph_sh_basic(args):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(".")
    result = subprocess.run([CPH_SH] + args, capture_output=True, text=True, env=env, cwd=PROJECT_ROOT)
    assert result.returncode == 0, f"Failed: {args}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    # Rustのtest時はCargo.tomlエラーやビルド失敗を検出
    if "rust" in args and "test" in args:
        assert "Cargo.toml" not in result.stderr, f"Cargo.toml missing error: {result.stderr}"
        assert "ビルド失敗" not in result.stdout, f"Build failed: {result.stdout}"

@pytest.mark.parametrize("args", [
    ["submit", "abc301", "a", "python", "local"],
    ["submit", "abc301", "a", "python", "docker"],
    ["submit", "abc301", "a", "rust", "local"],
    ["submit", "abc301", "a", "rust", "docker"],
])
def test_cph_sh_submit(args):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(".")
    result = subprocess.run([CPH_SH] + args, capture_output=True, text=True, env=env, cwd=PROJECT_ROOT)
    # submitはatcoderのセキュリティ都合で200がstdoutに含まれていればOK
    assert "200" in result.stdout, f"Submit failed: {args}\nstdout: {result.stdout}\nstderr: {result.stderr}" 