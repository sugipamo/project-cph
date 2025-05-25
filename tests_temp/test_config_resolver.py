import pytest
from src.context.config_resolver import ConfigResolver

@pytest.fixture
def sample_config():
    return {
        "python": {
            "env_type": {
                "docker": {"value": 1},
                "aliases": ["container"]
            },
            "local": {"value": 2}
        },
        "java": {
            "env_type": {
                "docker": {"value": 3}
            }
        }
    }

def test_resolve_deepest_match(sample_config):
    resolver = ConfigResolver.from_dict(sample_config)
    # 完全一致
    results = resolver.resolve(["python", "env_type", "docker"])
    assert any(r.node.name == "docker" for r in results)
    # 一部しかpathが存在しない場合
    results = resolver.resolve(["java", "env_type", "docker"])
    assert any(r.node.name == "docker" for r in results)
    # 存在しないpath
    results = resolver.resolve(["ruby", "env_type", "docker"])
    assert results == []
    # aliasでの探索
    results = resolver.resolve(["python", "container", "docker"])
    assert any(r.node.name == "docker" for r in results)

def test_resolve_multiple_aliases():
    config = {
        "lang": {
            "env_type": {
                "docker": {"value": 1, "aliases": ["container", "dkr", "d"]}
            }
        }
    }
    resolver = ConfigResolver.from_dict(config)
    for alias in ["docker", "container", "dkr", "d"]:
        results = resolver.resolve(["lang", "env_type", alias])
        assert any(r.node.name == "docker" for r in results)

def test_resolve_alias_in_middle_of_path():
    config = {
        "lang": {
            "env_type": {
                "docker": {"value": 1, "aliases": ["container"]}
            }
        }
    }
    resolver = ConfigResolver.from_dict(config)
    # パスの途中でaliasを使う場合は一致しない
    results = resolver.resolve(["lang", "container", "docker"])
    assert results == []

def test_resolve_name_and_alias_conflict():
    config = {
        "lang": {
            "env_type": {
                "docker": {"value": 1, "aliases": ["local"]},
                "local": {"value": 2}
            }
        }
    }
    resolver = ConfigResolver.from_dict(config)
    # "local"はノード名とエイリアス両方に存在
    results = resolver.resolve(["lang", "env_type", "local"])
    # どちらも返る（同じ深さ）
    names = set(r.node.name for r in results)
    assert "docker" in names or "local" in names
    assert len(results) >= 1

def test_resolve_multiple_nodes_same_depth():
    config = {
        "lang": {
            "env_type": {
                "docker": {"value": 1},
                "local": {"value": 2}
            }
        }
    }
    resolver = ConfigResolver.from_dict(config)
    # "docker"と"local"両方が同じ深さにある
    results = resolver.resolve(["lang", "env_type", "docker"])
    assert any(r.node.name == "docker" for r in results)
    results = resolver.resolve(["lang", "env_type", "local"])
    assert any(r.node.name == "local" for r in results)

def test_resolve_empty_path():
    config = {"a": 1}
    resolver = ConfigResolver.from_dict(config)
    with pytest.raises(Exception):
        resolver.resolve([])
    with pytest.raises(Exception):
        resolver.resolve(None)

def test_from_dict_with_list():
    config = {"lang": [1, 2, 3]}
    with pytest.raises(Exception):
        ConfigResolver.from_dict(config) 