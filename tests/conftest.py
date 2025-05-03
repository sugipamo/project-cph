import pytest
from src.command_executor import MockEditorOpener

@pytest.fixture(autouse=True)
def patch_editor_opener(monkeypatch):
    monkeypatch.setattr("src.command_executor.EditorOpener", MockEditorOpener) 