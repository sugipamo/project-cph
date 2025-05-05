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