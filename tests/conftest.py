import pytest
from src.command_executor import MockOpener

@pytest.fixture(autouse=True)
def patch_opener(monkeypatch):
    monkeypatch.setattr("src.command_executor.Opener", MockOpener) 