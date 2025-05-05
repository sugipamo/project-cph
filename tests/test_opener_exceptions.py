import pytest
from src.commands.opener import Opener

def test_open_editor_exceptions(monkeypatch, capsys):
    def raise_exc(cmd, *a, **k):
        raise Exception("fail")
    monkeypatch.setattr("subprocess.Popen", raise_exc)
    op = Opener()
    op.open_editor('foo')
    out = capsys.readouterr().out
    assert "VSCode起動失敗" in out or "Cursor起動失敗" in out

def test_open_browser_exception(monkeypatch, capsys):
    def raise_exc(url, *a, **k):
        raise Exception("fail")
    monkeypatch.setattr("webbrowser.open", raise_exc)
    op = Opener()
    op.open_browser('http://example.com')
    out = capsys.readouterr().out
    assert "ブラウザでページを開けませんでした" in out 