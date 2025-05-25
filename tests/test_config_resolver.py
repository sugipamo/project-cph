import pytest
import sys
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

def test_deeply_nested_mixed():
    data = {
        'a': [
            {'b': {'c': [1, 2, {'target': 42}]}},
            {'b': {'c': [3, 4]}}
        ]
    }
    resolver = ConfigResolver.from_dict(data)
    results = resolver.resolve(['a', '0', 'b', 'c', '2', 'target'])
    assert len(results) == 1
    assert results[0].node.value == 42

def test_duplicate_attribute_names():
    data = {
        'x': {'target': 1},
        'y': {'target': 2},
        'z': {'target': 3}
    }
    resolver = ConfigResolver.from_dict(data)
    results = resolver.resolve(['target'])
    found = set(r.node.value for r in results)
    assert found == {1, 2, 3}

def test_empty_dict_and_list():
    data = {
        'a': {},
        'b': [],
        'c': {'d': []},
        'e': {'f': {}}
    }
    resolver = ConfigResolver.from_dict(data)
    # 空dict/listノードも返る仕様に修正
    results_a = resolver.resolve(['a'])
    assert len(results_a) == 1
    assert results_a[0].node.value == {}
    results_b = resolver.resolve(['b'])
    assert len(results_b) == 1
    assert results_b[0].node.value == []
    results_d = resolver.resolve(['d'])
    assert len(results_d) == 1
    assert results_d[0].node.value == []
    results_f = resolver.resolve(['f'])
    assert len(results_f) == 1
    assert results_f[0].node.value == {}

def test_list_with_mixed_types():
    data = {
        'arr': [
            {'x': 1},
            [2, 3],
            {'x': 4}
        ]
    }
    resolver = ConfigResolver.from_dict(data)
    results = resolver.resolve(['arr', '0', 'x'])
    assert len(results) == 1
    assert results[0].node.value == 1
    results = resolver.resolve(['arr', '2', 'x'])
    assert len(results) == 1
    assert results[0].node.value == 4
    # listの中のlistはスキップされる（x属性はない）
    results = resolver.resolve(['arr', '1', 'x'])
    assert results == []

def test_parent_reference():
    data = {
        'foo': {
            'bar': {
                'baz': 123
            }
        }
    }
    resolver = ConfigResolver.from_dict(data)
    results = resolver.resolve(['foo', 'bar', 'baz'])
    assert len(results) == 1
    baz_node = results[0].node
    assert baz_node.parent.name == 'bar'
    assert baz_node.parent.parent.name == 'foo'

def test_large_structure():
    sys.setrecursionlimit(3000)
    data = {'root': {}}
    current = data['root']
    for i in range(1000):
        current[f'k{i}'] = {}
        current = current[f'k{i}']
    resolver = ConfigResolver.from_dict(data)
    # 最深部のノードを探索
    path = ['root'] + [f'k{i}' for i in range(1000)]
    results = resolver.resolve(path)
    assert len(results) == 1
    assert results[0].node.name == f'k999'

def test_numeric_string_keys():
    data = {
        '0': {'foo': 1},
        '1': {'foo': 2},
        '2': {'foo': 3}
    }
    resolver = ConfigResolver.from_dict(data)
    results = resolver.resolve(['0', 'foo'])
    assert len(results) == 1
    assert results[0].node.value == 1
    results = resolver.resolve(['1', 'foo'])
    assert len(results) == 1
    assert results[0].node.value == 2
    results = resolver.resolve(['foo'])
    assert len(results) == 3
    found = set(r.node.parent.name for r in results)
    assert found == {'0', '1', '2'}

def test_list_of_dicts_with_same_key():
    data = {
        'arr': [
            {'target': 10},
            {'target': 20},
            {'target': 30}
        ]
    }
    resolver = ConfigResolver.from_dict(data)
    results = resolver.resolve(['arr', 'target'])
    assert len(results) == 3
    found = set(r.node.value for r in results)
    assert found == {10, 20, 30} 