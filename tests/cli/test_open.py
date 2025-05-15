import os
import tempfile
import shutil
from src.cli.open import open_problem

class MockApiClient:
    def get_problem_info(self, contest_name, problem_name):
        return {
            "description": f"Description for {contest_name} {problem_name}",
            "samples": [
                {"input": "1 2\n", "output": "3\n"},
                {"input": "4 5\n", "output": "9\n"}
            ]
        }

class MockFileManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.files = {}
    def make_dir(self, path):
        os.makedirs(path, exist_ok=True)
    def join(self, *args):
        return os.path.join(*args)
    def file_exists(self, path):
        return os.path.exists(path)
    def write_file(self, path, content):
        with open(path, "w") as f:
            f.write(content)
    def read_file(self, path):
        with open(path, "r") as f:
            return f.read()

def test_open_problem_creates_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        api_client = MockApiClient()
        file_manager = MockFileManager(tmpdir)
        result = open_problem(
            contest_name="abc123",
            problem_name="a",
            api_client=api_client,
            file_manager=file_manager,
            dest_dir=tmpdir,
            overwrite=True
        )
        assert result["success"]
        assert os.path.exists(os.path.join(tmpdir, "README.md"))
        assert os.path.exists(os.path.join(tmpdir, "sample_1.in"))
        assert os.path.exists(os.path.join(tmpdir, "sample_1.out"))
        assert os.path.exists(os.path.join(tmpdir, "sample_2.in"))
        assert os.path.exists(os.path.join(tmpdir, "sample_2.out"))
        # 内容も確認
        with open(os.path.join(tmpdir, "README.md")) as f:
            assert f.read() == "Description for abc123 a"
        with open(os.path.join(tmpdir, "sample_1.in")) as f:
            assert f.read() == "1 2\n"
        with open(os.path.join(tmpdir, "sample_1.out")) as f:
            assert f.read() == "3\n" 