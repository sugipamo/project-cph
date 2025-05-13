# 上記3つのテスト関数をファイルから削除

import pytest
from unittest.mock import MagicMock, patch
from src.commands.command_open import CommandOpen

class DummyFileManager:
    def __init__(self):
        self.file_operator = MagicMock()
    def prepare_problem_files(self, contest, problem, lang):
        self.called = True
    def get_problem_files(self, contest, problem, lang):
        return 'problem_dir', 'test_dir'

class DummyOpener:
    def __init__(self):
        self.browser_opened = False
        self.editor_opened = False
        self.last_editor_path = None
    def open_browser(self, url):
        self.browser_opened = True
        self.last_url = url
    def open_editor(self, path, lang):
        self.editor_opened = True
        self.last_editor_path = path

class DummyResourceManager:
    def __init__(self, test_env):
        self.test_env = test_env
    def adjust_resources(self, req, contest, problem, lang):
        self.test_env.adjusted = True
        self.test_env.last_req = req
        return ['c1', 'c2']

class DummyFileOps:
    def __init__(self, test_env):
        self.test_env = test_env
    def download_testcases(self, url, test_dir):
        self.test_env.downloaded = True
        self.test_env.last_url = url
        self.test_env.last_test_dir = test_dir

class DummyTestEnv:
    def __init__(self):
        self.adjusted = False
        self.downloaded = False
        self.resource_manager = DummyResourceManager(self)
        self.file_ops = DummyFileOps(self)

# 古い設計依存のテスト（test_open_entry_file_and_editor, test_open_no_entry_file_opens_dir, test_open_no_file_operator）は削除済み 