import pytest
from src.context.config_resolver import ConfigResolver, ConfigResult

def test_resolve_single_dict():
    data = {
        'python': {
            'language_id': 5078,
            'commands': {'open': 'python_open'},
            'docker': {
                'dockerfile': 'Dockerfile',
                'commands': {'build': 'docker_build'}
            },
        },
        'cpp': {
            'language_id': 1003,
            'commands': {'open': 'cpp_open'}
        },
        'docker': {
            'dockerfile': 'Dockerfile',
            'commands': {'build': 'docker_build'}
        },
        'root_key': 'root_value',
    }
    resolver = ConfigResolver.from_dict(data)
    # commands属性を持つノードを探索
    results = resolver.resolve(['python', 'docker', 'commands'])
    assert len(results) == 1
    assert 'build' in results[0].node.value
    # commands属性を持つノードを複数探索
    results = resolver.resolve(['commands'])
    found = set(r.node.name for r in results)
    assert 'commands' in found

def test_resolve_shortcut():
    data = {
        'docker': {
            'dockerfile': 'Dockerfile',
            'commands': {'build': 'docker_build'}
        },
        'cpp': {
            'language_id': 1003,
            'commands': {'open': 'cpp_open'},
            'docker': {
                'dockerfile': 'Dockerfile',
                'commands': {'build': 'docker_build'}
            }
        }
    }
    resolver = ConfigResolver.from_dict(data)
    # rootからdocker.commands
    results = resolver.resolve(['docker', 'commands'])
    assert any('build' in r.node.value for r in results)
    # cppからdocker.commands
    results = resolver.resolve(['cpp', 'docker', 'commands'])
    assert any('build' in r.node.value for r in results)

def test_resolve_list():
    data = {
        'arr': [
            {'name': 'foo', 'commands': {'run': 'foo_run'}},
            {'name': 'bar', 'commands': {'run': 'bar_run'}}
        ]
    }
    resolver = ConfigResolver.from_dict(data)
    # arr.0.commands
    results = resolver.resolve(['arr', '0', 'commands'])
    assert len(results) == 1
    assert 'run' in results[0].node.value
    # arr.1.commands
    results = resolver.resolve(['arr', '1', 'commands'])
    assert len(results) == 1
    assert results[0].node.parent.value['name'] == 'bar'

def test_resolve_not_found():
    data = {
        'python': {'language_id': 5078},
    }
    resolver = ConfigResolver.from_dict(data)
    results = resolver.resolve(['not_exist'])
    assert results == []
    results = resolver.resolve(['python', 'not_exist'])
    assert results == []

def test_resolve_root_value():
    data = {
        'root_key': 'root_value',
        'python': {'language_id': 5078}
    }
    resolver = ConfigResolver.from_dict(data)
    results = resolver.resolve(['root_key'])
    assert len(results) == 1
    assert results[0].node.value == 'root_value'

def test_resolve_level_all():
    data = {
        'python': {'commands': {'open': 'python_open'}},
        'cpp': {'commands': {'open': 'cpp_open'}},
        'docker': {'commands': {'build': 'docker_build'}},
    }
    resolver = ConfigResolver.from_dict(data)
    results = resolver.resolve(['commands'])
    assert len(results) >= 2
    for r in results:
        assert isinstance(r.node.value, dict)

def test_resolve_cycle_protection():
    # dictで循環は起きないが、念のため大きなネストで無限ループしないことを確認
    data = {}
    current = data
    for i in range(100):
        current['nest'] = {}
        current = current['nest']
    resolver = ConfigResolver.from_dict(data)
    results = resolver.resolve(['nest'] * 100)
    # 最深部のnestノードが1つ返る
    assert len(results) == 1

def test_resolve_list_level():
    data = {
        'arr': [
            {'commands': {'run': 'foo_run'}},
            {'commands': {'run': 'bar_run'}},
            {'commands': {'run': 'baz_run'}},
        ]
    }
    resolver = ConfigResolver.from_dict(data)
    results = resolver.resolve(['arr', 'commands'])
    # arrの各要素のcommandsノードが返る
    assert len(results) == 3
    for r in results:
        assert 'run' in r.node.value 