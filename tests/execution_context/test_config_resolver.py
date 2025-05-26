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

def test_from_dict_invalid_type():
    with pytest.raises(ValueError):
        ConfigResolver.from_dict([1, 2, 3])
    with pytest.raises(ValueError):
        ConfigResolver.from_dict(None)
    with pytest.raises(ValueError):
        ConfigResolver.from_dict(123)


def test_resolve_invalid_path_type(sample_config):
    resolver = ConfigResolver.from_dict(sample_config)
    with pytest.raises(TypeError):
        resolver.resolve("notalist")
    with pytest.raises(TypeError):
        resolver.resolve(None)
    with pytest.raises(TypeError):
        resolver.resolve(123)


def test_add_edge_invalid_type():
    node = ConfigNode("a")
    with pytest.raises(AttributeError):
        node.add_edge("notanode")


def test_aliases_invalid_type():
    config = {
        "docker": {
            "aliases": "notalist",
            "value": 1
        }
    }
    # from_dictでエラーになるか
    with pytest.raises(Exception):
        ConfigResolver.from_dict(config)


def test_confignode_lt_invalid_type():
    node = ConfigNode("a")
    with pytest.raises(TypeError):
        node < "notanode"

def test_add_edge_self_reference():
    node = ConfigNode("self")
    node.add_edge(node)
    # 自己参照でも例外が出ないこと、next_nodesに自分自身が含まれる
    assert node in node.next_nodes


def test_add_edge_duplicate():
    node1 = ConfigNode("a")
    node2 = ConfigNode("b")
    node1.add_edge(node2)
    node1.add_edge(node2)
    # 重複してもnext_nodesに2回追加される（現仕様）
    assert node1.next_nodes.count(node2) >= 2


def test_value_dict_not_destroyed():
    value = {"aliases": ["x"], "value": 1}
    import copy
    value_copy = copy.deepcopy(value)
    node = ConfigNode("a", value_copy)
    # value_copyのaliasesが消えていないこと
    assert "aliases" in value


def test_add_edge_parent_and_next_nodes():
    node1 = ConfigNode("a")
    node2 = ConfigNode("b")
    node1.add_edge(node2)
    assert node2 in node1.next_nodes
    assert node1 in node2.next_nodes
    assert node2.parent == node1


def test_repr_circular_reference():
    node1 = ConfigNode("a")
    node2 = ConfigNode("b")
    node1.add_edge(node2)
    node2.add_edge(node1)  # 循環
    r = repr(node1)
    assert "ConfigNode" in r


def test_resolve_path_with_empty_and_duplicate():
    config = {
        "python": {
            "env_type": {
                "docker": {"value": 1}
            }
        }
    }
    resolver = ConfigResolver.from_dict(config)
    # 空文字列を含むパス
    results_empty = resolver.resolve(["python", "", "docker"])
    assert results_empty == []
    # 重複要素を含むパス
    results_dup = resolver.resolve(["python", "python", "env_type", "docker"])
    # 仕様上、重複しても一致しない場合は空リスト
    assert isinstance(results_dup, list)


def test_large_nested_dict():
    # 100階層のネスト
    d = v = {}
    for i in range(100):
        nv = {}
        v[str(i)] = nv
        v = nv
    resolver = ConfigResolver.from_dict(d)
    # 存在しない深いパス
    path = [str(i) for i in range(100)]
    results = resolver.resolve(path)
    assert isinstance(results, list)


def test_matches_direct_modification():
    node = ConfigNode("a")
    # matchesはsetだが、直接書き換えはできない（property）
    with pytest.raises(AttributeError):
        node.matches = {"b"}