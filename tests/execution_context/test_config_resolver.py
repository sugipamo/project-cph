import pytest
from src.context.config_resolver import ConfigResolver, ConfigNode

@pytest.fixture
def sample_config():
    return {
        "python": {
            "env_type": {
                "docker": {
                    "aliases": ["container"],
                    "value": 1
                },
            },
            "local": {"value": 2}
        },
        "java": {
            "env_type": {
                "docker": {"value": 3}
            }
        }
    }

def test_resolve_python_match(sample_config):
    resolver = ConfigResolver.from_dict(sample_config)
    # 完全一致
    results = resolver.resolve(["python", "env_type", "docker"])
    assert [r.value for r in results] == [{"value": 1}, {"value": 3}]

def test_resolve_java_docker(sample_config):
    resolver = ConfigResolver.from_dict(sample_config)
    results = resolver.resolve(["java", "env_type", "docker"])
    assert [r.value for r in results] == [{"value": 3}, {"value": 1}]

def test_resolve_local(sample_config):
    resolver = ConfigResolver.from_dict(sample_config)
    results = resolver.resolve(["python", "local"])
    assert [r.value for r in results] == [{"value": 2}]

def test_resolve_alias(sample_config):
    resolver = ConfigResolver.from_dict(sample_config)
    # "container" は "docker" のエイリアス
    results = resolver.resolve(["python", "env_type", "container"])
    assert [r.value for r in results] == [{"value": 1}]

def test_resolve_not_found(sample_config):
    resolver = ConfigResolver.from_dict(sample_config)
    # 存在しないパス
    results = resolver.resolve(["python", "env_type", "nonexistent"])
    assert [r.value for r in results] == []

def test_resolve_neighbor_match(sample_config):
    resolver = ConfigResolver.from_dict(sample_config)
    # 存在しないパスであっても、最もよく一致するノードを返す
    results = resolver.resolve(["rust", "env_type", "container"])
    assert [r.value for r in results] == [{"value": 1}]

def test_resolve_multiple_matches(sample_config):
    resolver = ConfigResolver.from_dict(sample_config)
    # 同じパスで複数のノードが一致する場合、最もよく一致するノードを返す
    results = resolver.resolve(["python", "env_type"])
    assert [r.value for r in results] == [{'docker': {'value': 1}}]

def test_resolve_multiple_matches_with_alias(sample_config):
    resolver = ConfigResolver.from_dict(sample_config)
    # 同じパスで複数のノードが一致する場合、最もよく一致するノードを返す
    results = resolver.resolve(["env_type", "container"])
    assert [r.value for r in results] == [{"value": 1}]

def test_resolve_empty_path(sample_config):
    resolver = ConfigResolver.from_dict(sample_config)
    results = resolver.resolve([])
    assert results == []

def test_resolve_multiple_aliases():
    config = {
        "python": {
            "env_type": {
                "docker": {
                    "aliases": ["container", "box"],
                    "value": 1
                }
            }
        }
    }
    resolver = ConfigResolver.from_dict(config)
    results = resolver.resolve(["python", "env_type", "box"])
    assert [r.value for r in results] == [{"value": 1}]

def test_resolve_list_node():
    config = {
        "python": [1, 2, 3]
    }
    resolver = ConfigResolver.from_dict(config)
    results = resolver.resolve(["python", 1])  # インデックスでアクセス
    assert [r.value for r in results] == [2]

def test_resolve_parent_alias():
    config = {
        "docker": {
            "aliases": ["container"],
            "value": 1
        }
    }
    resolver = ConfigResolver.from_dict(config)
    results = resolver.resolve(["container"])
    assert [r.value for r in results] == [{"value": 1}]

def test_resolve_circular_reference():
    # 手動で循環参照を作る
    node_a = ConfigNode("a", {"value": 1})
    node_b = ConfigNode("b", {"value": 2})
    node_a.add_edge(node_b)
    node_b.add_edge(node_a)  # 循環
    resolver = ConfigResolver(node_a)
    # 無限ループしないこと
    results = resolver.resolve(["b"])
    assert any(r.name == "b" for r in results)

def test_resolve_aliases_and_other_keys():
    config = {
        "docker": {
            "aliases": ["container"],
            "value": 1,
            "desc": "test"
        }
    }
    resolver = ConfigResolver.from_dict(config)
    results = resolver.resolve(["container"])
    # descが消えていないこと
    assert any("desc" in r.value for r in results)
    assert [r.value["value"] for r in results] == [1]

def test_resolve_values():
    config = {
        "python": {
            "env_type": {
                "docker": {"value": 1}
            }
        }
    }
    resolver = ConfigResolver.from_dict(config)
    values = resolver.resolve_values(["python", "env_type", "docker"])
    assert values == [{"value": 1}]

def test_resolve_deep_nested_path():
    config = {
        "python": {
            "env_type": {
                "docker": {
                    "value": 1
                }
            }
        }
    }
    resolver = ConfigResolver.from_dict(config)
    # 存在しない深いパス
    results = resolver.resolve(["python", "env_type", "docker", "extra"])
    assert results == []

def test_resolve_with_special_keys():
    config = {
        "python": {
            None: {"value": 99},
            123: {"value": 42}
        }
    }
    resolver = ConfigResolver.from_dict(config)
    results_none = resolver.resolve(["python", None])
    results_num = resolver.resolve(["python", 123])
    assert [r.value for r in results_none] == [{"value": 99}]
    assert [r.value for r in results_num] == [{"value": 42}]

def test_resolve_empty_aliases():
    config = {
        "docker": {
            "aliases": [],
            "value": 1
        }
    }
    resolver = ConfigResolver.from_dict(config)
    results = resolver.resolve(["docker"])
    assert [r.value for r in results] == [{"value": 1}]
    # 空aliasesでも通常のキーで一致すること
    results_alias = resolver.resolve([""])
    assert results_alias == []

def test_resolve_same_name_multi_level():
    config = {
        "a": {
            "b": {
                "c": 1
            }
        },
        "b": {
            "c": 2
        }
    }
    resolver = ConfigResolver.from_dict(config)
    results = resolver.resolve(["b", "c"])
    # どちらのb/cも返る可能性があるが、最もよく一致するノードが先頭
    values = [r.value for r in results]
    assert 2 in values and 1 in values

def test_resolve_tuple_path():
    config = {
        "python": {
            "env_type": {
                "docker": {"value": 1}
            }
        }
    }
    resolver = ConfigResolver.from_dict(config)
    results = resolver.resolve(("python", "env_type", "docker"))
    assert [r.value for r in results] == [{"value": 1}]

def test_confignode_properties_and_repr():
    node = ConfigNode("test", {"aliases": ["t1", "t2"], "value": 5})
    assert node.name == "test"
    assert "t1" in node.matches and "t2" in node.matches
    assert node.value["value"] == 5
    assert node.parent is None
    assert isinstance(node.next_nodes, list)
    r = repr(node)
    assert "ConfigNode" in r and "test" in r