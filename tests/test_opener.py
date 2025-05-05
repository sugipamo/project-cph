import pytest
from src.commands.opener import Opener

def test_open_editor_and_browser(monkeypatch):
    called = {}
    def fake_popen(cmd, *a, **k):
        called['editor'] = cmd
    def fake_webbrowser_open(url):
        called['browser'] = url
    monkeypatch.setattr("subprocess.Popen", fake_popen)
    monkeypatch.setattr("webbrowser.open", fake_webbrowser_open)
    op = Opener()
    op.open_editor('foo')
    op.open_browser('http://example.com')
    # VSCode/カーソル両方呼ばれるので、最後の呼び出しがcursor
    assert called['editor'][-1] in ['foo/main.py', 'foo/src/main.rs']
    assert called['browser'] == 'http://example.com'

def test_open_editor_rust(monkeypatch):
    called = {}
    def fake_popen(cmd, *a, **k):
        called.setdefault('editors', []).append(cmd)
    monkeypatch.setattr("subprocess.Popen", fake_popen)
    op = Opener()
    op.open_editor('foo', language='rust')
    # rustならmain.rsが開かれる
    assert any('foo/src/main.rs' in c for c in called['editors'])

def test_open_editor_vscode_fail_cursor_success(monkeypatch, capsys):
    calls = []
    def popen_side_effect(cmd, *a, **k):
        if 'code' in cmd[0]:
            raise Exception("fail VSCode")
        calls.append(cmd)
    monkeypatch.setattr("subprocess.Popen", popen_side_effect)
    op = Opener()
    op.open_editor('foo')
    out = capsys.readouterr().out
    assert "VSCode起動失敗" in out
    assert any('cursor' in c[0] for c in calls)

def test_open_editor_both_fail(monkeypatch, capsys):
    def popen_fail(cmd, *a, **k):
        raise Exception("fail")
    monkeypatch.setattr("subprocess.Popen", popen_fail)
    op = Opener()
    op.open_editor('foo')
    out = capsys.readouterr().out
    assert "VSCode起動失敗" in out and "Cursor起動失敗" in out

def test_open_browser_success(monkeypatch):
    called = {}
    def fake_webbrowser_open(url):
        called['url'] = url
    monkeypatch.setattr("webbrowser.open", fake_webbrowser_open)
    op = Opener()
    op.open_browser('http://example.com')
    assert called['url'] == 'http://example.com' 