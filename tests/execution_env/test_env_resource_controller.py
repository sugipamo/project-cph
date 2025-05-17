import pytest
from src.execution_env.env_resource_controller import EnvResourceController, EnvType, EnvConfig, list_languages, list_language_envs, load_env_json, BASE_DIR
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.docker.docker_file_request import DockerFileRequest
import os
import tempfile
import json
import shutil

class DummyFileHandler:
    def read(self, path):
        return f"read:{path}"
    def write(self, path, content):
        return f"write:{path}:{content}"
    def exists(self, path):
        return path == "exists.txt"
    def remove(self, path):
        return f"remove:{path}"
    def move(self, src, dst):
        return f"move:{src}->{dst}"
    def copytree(self, src, dst):
        return f"copytree:{src}->{dst}"
    def rmtree(self, path):
        return f"rmtree:{path}"
    def copy(self, src, dst):
        return f"copy:{src}->{dst}"

class DummyRunHandler:
    def create_process_options(self, cmd, driver=None):
        return f"run:{cmd}:{driver}"

class DummyConstHandler:
    pass

def test_dependency_injection():
    controller = EnvResourceController(
        language_name="dummy",
        env_type="local",
        file_handler=DummyFileHandler(),
        run_handler=DummyRunHandler(),
        const_handler=DummyConstHandler(),
    )
    assert controller.read_file("foo.txt") == "read:foo.txt"
    assert controller.write_file("bar.txt", "abc") == "write:bar.txt:abc"
    assert controller.file_exists("exists.txt") is True
    assert controller.file_exists("notfound.txt") is False
    assert controller.remove_file("baz.txt") == "remove:baz.txt"
    assert controller.move_file("a.txt", "b.txt") == "move:a.txt->b.txt"
    assert controller.copytree("src", "dst") == "copytree:src->dst"
    assert controller.rmtree("dir") == "rmtree:dir"
    assert controller.copy_file("a", "b") == "copy:a->b"
    assert controller.create_process_options(["ls"], driver="drv") == "run:['ls']:drv"

def test_envconfig_validation():
    # env_typeなし
    with pytest.raises(ValueError):
        EnvConfig({"contest_current_path": "a", "source_file": "b"})
    # 不正なenv_type
    with pytest.raises(ValueError):
        EnvConfig({"env_type": "invalid", "contest_current_path": "a", "source_file": "b"})
    # contest_current_pathなし
    with pytest.raises(ValueError):
        EnvConfig({"env_type": "local", "source_file": "b"})
    # source_fileなし
    with pytest.raises(ValueError):
        EnvConfig({"env_type": "local", "contest_current_path": "a"})

# local/dockerの正常系は既存のtest_env_resource_controller.pyでカバーされているため、
# ここでは依存注入・異常系を中心にテストしています。 

def make_env_json(dir_path, lang, env_type="local"):
    lang_dir = os.path.join(dir_path, lang)
    os.makedirs(lang_dir, exist_ok=True)
    env_json_path = os.path.join(lang_dir, "env.json")
    data = {
        "env_type": env_type,
        "contest_current_path": "abc",
        "source_file": "main.cpp",
        "contest_env_path": "env",
        "contest_template_path": "template",
        "contest_temp_path": "temp",
    }
    with open(env_json_path, "w") as f:
        json.dump(data, f)
    return env_json_path

def test_list_languages_and_load_env_json(tmp_path, monkeypatch):
    # 一時ディレクトリをBASE_DIRに
    base_dir = tmp_path / "contest_env"
    base_dir.mkdir()
    monkeypatch.setattr("src.execution_env.env_resource_controller.BASE_DIR", str(base_dir))
    # 言語A, Bを作成
    make_env_json(str(base_dir), "A")
    make_env_json(str(base_dir), "B")
    langs = list_languages()
    assert set(langs) == {"A", "B"}
    # load_env_jsonでEnvConfigが返る
    cfg = load_env_json("A", "local")
    assert isinstance(cfg, EnvConfig)
    assert cfg.env_type.name == "LOCAL"
    # 存在しない言語
    with pytest.raises(ValueError):
        load_env_json("C", "local")

def test_list_language_envs(tmp_path, monkeypatch):
    base_dir = tmp_path / "contest_env"
    base_dir.mkdir()
    monkeypatch.setattr("src.execution_env.env_resource_controller.BASE_DIR", str(base_dir))
    # env.jsonのトップレベルキーが言語名の形式
    lang_dir = base_dir / "python"
    lang_dir.mkdir()
    env_json_path = lang_dir / "env.json"
    data = {
        "python": {
            "handlers": {
                "local": {},
                "docker": {}
            }
        }
    }
    with open(env_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    result = list_language_envs()
    assert ("python", "local") in result
    assert ("python", "docker") in result
    # handlersが空の場合
    data2 = {"python": {"handlers": {}}}
    with open(env_json_path, "w", encoding="utf-8") as f:
        json.dump(data2, f)
    result2 = list_language_envs()
    assert ("python", "local") not in result2 and ("python", "docker") not in result2 