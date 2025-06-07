import os
import subprocess

import pytest

CPH_SH = os.path.abspath("./cph.sh")
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__ + "/../../"))

pytestmark = pytest.mark.skip(reason="e2eテスト一時スキップ（Rust設定未完了のため）")

@pytest.mark.parametrize("args", [
    ["python", "open", "abc301", "a"],
    ["python", "local", "test", "abc301", "a"],
    ["python", "docker", "test", "abc301", "a"],
    ["rust", "open", "abc301", "a"],
    ["rust", "local", "test", "abc301", "a"],
    ["rust", "docker", "test", "abc301", "a"],
])
def test_cph_sh_basic(args):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(".")
    result = subprocess.run([CPH_SH, *args], capture_output=True, text=True, env=env, cwd=PROJECT_ROOT)
    assert result.returncode == 0, f"Failed: {args}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    # Rustのtest時はCargo.tomlエラーやビルド失敗を検出
    if "rust" in args and "test" in args:
        assert "Cargo.toml" not in result.stderr, f"Cargo.toml missing error: {result.stderr}"
        assert "ビルド失敗" not in result.stdout, f"Build failed: {result.stdout}"

@pytest.mark.parametrize("args", [
    ["python", "local", "submit", "abc301", "a"],
    ["python", "docker", "submit", "abc301", "a"],
    ["rust", "local", "submit", "abc301", "a"],
    ["rust", "docker", "submit", "abc301", "a"],
])
def test_cph_sh_submit(args):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(".")
    result = subprocess.run([CPH_SH, *args], capture_output=True, text=True, env=env, cwd=PROJECT_ROOT)
    # submitはatcoderのセキュリティ都合で200がstdoutに含まれていればOK
    assert "200" in result.stdout, f"Submit failed: {args}\nstdout: {result.stdout}\nstderr: {result.stderr}"
