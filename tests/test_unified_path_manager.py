from pathlib import Path
from src.path_manager.unified_path_manager import UnifiedPathManager
import os

def make_upm(tmp_path):
    # テスト用の一時ディレクトリをproject_rootに
    return UnifiedPathManager(project_root=tmp_path, container_root="/workspace", mounts=[(tmp_path, Path("/workspace"))])

def test_path_service_shortcuts(tmp_path):
    upm = make_upm(tmp_path)
    assert upm.contest_current("main.py").endswith(os.path.join("contest_current", "main.py"))
    assert upm.contest_stocks("abc", "a", "python").endswith(os.path.join("contest_stocks", "abc", "a", "python"))
    assert upm.contest_env("python.Dockerfile").endswith(os.path.join("contest_env", "python.Dockerfile"))
    assert upm.contest_template("python", "main.py").endswith(os.path.join("contest_template", "python", "main.py"))
    assert upm.info_json().endswith(os.path.join("contest_current", "info.json"))
    assert upm.config_json().endswith(os.path.join("contest_current", "config.json"))
    assert upm.test_dir().endswith(os.path.join("contest_current", "test"))
    assert upm.readme_md().endswith(os.path.join("contest_current", "README.md"))

def test_to_container_path_and_back(tmp_path):
    upm = make_upm(tmp_path)
    host_file = Path(tmp_path) / "contest_current" / "main.py"
    cont_file = Path("/workspace/contest_current/main.py")
    # to_container_path
    assert upm.to_container_path(host_file) == cont_file
    # to_host_path
    assert upm.to_host_path(cont_file) == host_file.resolve()
    # 未マウント
    assert upm.to_container_path(Path("/not/mounted/file.txt")) is None
    assert upm.to_host_path(Path("/not/mounted/file.txt")) is None

def test_get_and_add_mount(tmp_path):
    upm = make_upm(tmp_path)
    mounts = upm.get_mounts()
    assert len(mounts) == 1
    new_host = Path("/tmp/other")
    new_cont = Path("/workspace/other")
    upm.add_mount(new_host, new_cont)
    mounts2 = upm.get_mounts()
    assert any(h == new_host.resolve() and c == new_cont for h, c in mounts2)

def test_container_shortcuts(tmp_path):
    upm = make_upm(tmp_path)
    # contest_current_in_container
    assert upm.contest_current_in_container("main.py") == Path("/workspace/contest_current/main.py")
    assert upm.info_json_in_container() == Path("/workspace/contest_current/info.json")
    assert upm.config_json_in_container() == Path("/workspace/contest_current/config.json")
    assert upm.test_dir_in_container() == Path("/workspace/contest_current/test")
    assert upm.readme_md_in_container() == Path("/workspace/contest_current/README.md")

def test_path_validation_and_normalize(tmp_path):
    file_path = tmp_path / "file.txt"
    dir_path = tmp_path / "dir"
    file_path.write_text("abc")
    dir_path.mkdir()
    # is_valid_path
    assert UnifiedPathManager.is_valid_path(file_path, must_exist=True, must_be_file=True)
    assert UnifiedPathManager.is_valid_path(dir_path, must_exist=True, must_be_dir=True)
    assert not UnifiedPathManager.is_valid_path(file_path, must_be_dir=True)
    assert not UnifiedPathManager.is_valid_path(dir_path, must_be_file=True)
    # ensure_exists
    new_file = tmp_path / "new.txt"
    assert not new_file.exists()
    UnifiedPathManager.ensure_exists(new_file, create_if_missing=True)
    assert new_file.exists()
    new_dir = tmp_path / "newdir"
    UnifiedPathManager.ensure_exists(new_dir, create_if_missing=True, is_dir=True)
    assert new_dir.exists() and new_dir.is_dir()
    # normalize_path
    rel = "./foo/bar.txt"
    abs_path = UnifiedPathManager.normalize_path(rel)
    from pathlib import Path
    assert Path(abs_path).is_absolute()
    # resolve_symlink
    target = tmp_path / "target.txt"
    target.write_text("x")
    link = tmp_path / "link.txt"
    link.symlink_to(target)
    resolved = UnifiedPathManager.resolve_symlink(link)
    assert Path(resolved).resolve() == target.resolve() 