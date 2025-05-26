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