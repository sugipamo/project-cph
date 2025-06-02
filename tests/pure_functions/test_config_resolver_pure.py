"""
設定解決純粋関数のテスト
モック不要で実際の動作をテスト
"""
import pytest
from src.pure_functions.config_resolver_pure import (
    ConfigNodeData,
    ConfigTreeData,
    ResolveResult,
    FormatResult,
    build_config_tree_pure,
    resolve_by_path_pure,
    resolve_best_pure,
    resolve_values_pure,
    format_string_pure,
    format_node_value_pure,
    validate_config_tree_pure,
    calculate_tree_metrics_pure,
    _extract_matches_pure,
    _extract_template_from_node_pure,
    _extract_value_for_formatting_pure
)


class TestConfigNodeData:
    """ConfigNodeDataのテスト"""
    
    def test_create_config_node_data(self):
        """設定ノードデータ作成のテスト"""
        node = ConfigNodeData(
            key="test_key",
            value={"value": "test_value"},
            matches={"test", "alias"},
            parent_id="parent_1",
            children_ids=["child_1", "child_2"]
        )
        
        assert node.key == "test_key"
        assert node.value == {"value": "test_value"}
        assert node.matches == {"test", "alias"}
        assert node.parent_id == "parent_1"
        assert node.children_ids == ["child_1", "child_2"]
    
    def test_config_node_data_immutability(self):
        """設定ノードデータの不変性テスト"""
        node = ConfigNodeData(
            key="test",
            value="test_value",
            matches=set(),
            children_ids=[]
        )
        
        with pytest.raises(AttributeError):
            node.key = "new_key"
    
    def test_config_node_data_defaults(self):
        """設定ノードデータのデフォルト値テスト"""
        node = ConfigNodeData(
            key="test",
            value="test_value",
            matches=set()
        )
        
        assert node.parent_id is None
        assert node.children_ids == []


class TestConfigTreeData:
    """ConfigTreeDataのテスト"""
    
    def test_create_config_tree_data(self):
        """設定ツリーデータ作成のテスト"""
        root_node = ConfigNodeData(
            key="root",
            value={"test": "value"},
            matches={"root"},
            children_ids=["child_1"]
        )
        child_node = ConfigNodeData(
            key="child",
            value="child_value",
            matches={"child"},
            parent_id="root_id"
        )
        
        tree = ConfigTreeData(
            nodes={"root_id": root_node, "child_1": child_node},
            root_id="root_id"
        )
        
        assert tree.root_id == "root_id"
        assert len(tree.nodes) == 2
        assert tree.get_node("root_id") == root_node
        assert tree.get_node("child_1") == child_node
    
    def test_get_children(self):
        """子ノード取得のテスト"""
        parent_node = ConfigNodeData(
            key="parent",
            value="parent_value",
            matches={"parent"},
            children_ids=["child_1", "child_2"]
        )
        child1_node = ConfigNodeData(
            key="child1",
            value="child1_value",
            matches={"child1"},
            parent_id="parent_id"
        )
        child2_node = ConfigNodeData(
            key="child2",
            value="child2_value",
            matches={"child2"},
            parent_id="parent_id"
        )
        
        tree = ConfigTreeData(
            nodes={
                "parent_id": parent_node,
                "child_1": child1_node,
                "child_2": child2_node
            },
            root_id="parent_id"
        )
        
        children = tree.get_children("parent_id")
        assert len(children) == 2
        assert child1_node in children
        assert child2_node in children
    
    def test_get_parent(self):
        """親ノード取得のテスト"""
        parent_node = ConfigNodeData(
            key="parent",
            value="parent_value",
            matches={"parent"},
            children_ids=["child_1"]
        )
        child_node = ConfigNodeData(
            key="child",
            value="child_value",
            matches={"child"},
            parent_id="parent_id"
        )
        
        tree = ConfigTreeData(
            nodes={"parent_id": parent_node, "child_1": child_node},
            root_id="parent_id"
        )
        
        parent = tree.get_parent("child_1")
        assert parent == parent_node


class TestExtractMatchesPure:
    """マッチ抽出関数のテスト"""
    
    def test_extract_matches_from_dict_with_aliases(self):
        """エイリアス付き辞書からのマッチ抽出テスト"""
        value = {
            "aliases": ["alias1", "alias2"],
            "key1": "value1",
            "key2": "value2"
        }
        
        matches = _extract_matches_pure(value)
        
        assert "alias1" in matches
        assert "alias2" in matches
        assert "key1" in matches
        assert "key2" in matches
        assert "aliases" not in matches
    
    def test_extract_matches_from_simple_dict(self):
        """シンプルな辞書からのマッチ抽出テスト"""
        value = {"key1": "value1", "key2": "value2"}
        
        matches = _extract_matches_pure(value)
        
        assert matches == {"key1", "key2"}
    
    def test_extract_matches_from_string(self):
        """文字列からのマッチ抽出テスト"""
        value = "test_string"
        
        matches = _extract_matches_pure(value)
        
        assert matches == {"test_string"}
    
    def test_extract_matches_from_number(self):
        """数値からのマッチ抽出テスト"""
        value = 42
        
        matches = _extract_matches_pure(value)
        
        assert matches == {"42"}
    
    def test_extract_matches_invalid_aliases(self):
        """無効なエイリアスのテスト"""
        value = {"aliases": "not_a_list"}
        
        with pytest.raises(TypeError, match="aliasesはlist型である必要があります"):
            _extract_matches_pure(value)


class TestBuildConfigTreePure:
    """設定ツリー構築関数のテスト"""
    
    def test_build_simple_tree(self):
        """シンプルなツリー構築のテスト"""
        data = {
            "language": "python",
            "commands": {
                "build": ["python", "build.py"],
                "test": ["python", "test.py"]
            }
        }
        
        tree = build_config_tree_pure(data)
        
        assert tree.root_id in tree.nodes
        root_node = tree.get_node(tree.root_id)
        assert root_node.key == "root"
        assert root_node.value == data
        assert len(tree.nodes) >= 3  # root + language + commands + ...
    
    def test_build_tree_with_aliases(self):
        """エイリアス付きツリー構築のテスト"""
        data = {
            "python": {
                "aliases": ["py", "python3"],
                "version": "3.9"
            }
        }
        
        tree = build_config_tree_pure(data)
        
        # pythonノードのマッチ確認
        python_nodes = [node for node in tree.nodes.values() if node.key == "python"]
        assert len(python_nodes) >= 1
        python_node = python_nodes[0]
        assert "py" in python_node.matches
        assert "python3" in python_node.matches
    
    def test_build_tree_with_list(self):
        """リスト含むツリー構築のテスト"""
        data = {
            "steps": [
                {"type": "build", "cmd": ["python", "build.py"]},
                {"type": "test", "cmd": ["python", "test.py"]}
            ]
        }
        
        tree = build_config_tree_pure(data)
        
        # stepsノードが存在し、子ノードを持つ
        steps_nodes = [node for node in tree.nodes.values() if node.key == "steps"]
        assert len(steps_nodes) >= 1
        steps_node = steps_nodes[0]
        
        # インデックスベースの子ノードを持つ
        children = tree.get_children(next(nid for nid, n in tree.nodes.items() if n == steps_node))
        assert len(children) >= 2
    
    def test_build_tree_invalid_input(self):
        """無効な入力のテスト"""
        with pytest.raises(ValueError, match="dict以外は未対応です"):
            build_config_tree_pure("not_a_dict")


class TestResolveByPathPure:
    """パス解決関数のテスト"""
    
    def test_resolve_simple_path(self):
        """シンプルなパス解決のテスト"""
        data = {
            "python": {
                "commands": {
                    "build": "python build.py"
                }
            }
        }
        
        tree = build_config_tree_pure(data)
        result = resolve_by_path_pure(tree, ["python", "commands", "build"])
        
        assert len(result.nodes) >= 1
        assert len(result.errors) == 0
    
    def test_resolve_with_aliases(self):
        """エイリアス付きパス解決のテスト"""
        data = {
            "python": {
                "aliases": ["py"],
                "commands": {
                    "build": "python build.py"
                }
            }
        }
        
        tree = build_config_tree_pure(data)
        result = resolve_by_path_pure(tree, ["py", "commands", "build"])
        
        assert len(result.nodes) >= 1
        assert len(result.errors) == 0
    
    def test_resolve_empty_path(self):
        """空パス解決のテスト"""
        data = {"test": "value"}
        tree = build_config_tree_pure(data)
        
        result = resolve_by_path_pure(tree, [])
        
        assert len(result.nodes) == 0
        assert len(result.errors) == 0
    
    def test_resolve_invalid_path_type(self):
        """無効なパス型のテスト"""
        data = {"test": "value"}
        tree = build_config_tree_pure(data)
        
        result = resolve_by_path_pure(tree, "not_a_list")
        
        assert len(result.nodes) == 0
        assert len(result.errors) == 1
        assert "pathはlistまたはtupleである必要があります" in result.errors[0]


class TestResolveBestPure:
    """最良解決関数のテスト"""
    
    def test_resolve_best_existing_path(self):
        """存在するパスの最良解決テスト"""
        data = {
            "python": {
                "commands": {
                    "build": "python build.py"
                }
            }
        }
        
        tree = build_config_tree_pure(data)
        node = resolve_best_pure(tree, ["python", "commands", "build"])
        
        assert node is not None
        # 解決されたノードが適切な値を持つことを確認（構造に応じて調整）
        assert isinstance(node.value, (str, dict))
        if isinstance(node.value, dict) and "build" in node.value:
            assert node.value["build"] == "python build.py"
        elif isinstance(node.value, str):
            assert node.value == "python build.py"
    
    def test_resolve_best_nonexistent_path(self):
        """存在しないパスの最良解決テスト"""
        data = {"python": {"version": "3.9"}}
        tree = build_config_tree_pure(data)
        
        node = resolve_best_pure(tree, ["java", "commands", "build"])
        
        assert node is None


class TestResolveValuesPure:
    """値解決関数のテスト"""
    
    def test_resolve_values_multiple_matches(self):
        """複数マッチの値解決テスト"""
        data = {
            "python": {
                "version": "3.9",
                "commands": {
                    "build": "python build.py",
                    "test": "python test.py"
                }
            }
        }
        
        tree = build_config_tree_pure(data)
        values = resolve_values_pure(tree, ["python", "commands"])
        
        assert len(values) >= 1


class TestFormatStringPure:
    """文字列フォーマット関数のテスト"""
    
    def test_format_simple_template(self):
        """シンプルなテンプレートフォーマットのテスト"""
        data = {
            "language": "python",
            "version": "3.9"
        }
        
        tree = build_config_tree_pure(data)
        result = format_string_pure("Using {language} version {version}", tree)
        
        assert result.formatted_string == "Using python version 3.9"
        assert len(result.errors) == 0
        assert "language" in result.resolved_keys
        assert "version" in result.resolved_keys
    
    def test_format_with_initial_values(self):
        """初期値付きフォーマットのテスト"""
        data = {"version": "3.9"}
        tree = build_config_tree_pure(data)
        
        result = format_string_pure(
            "Using {language} version {version}", 
            tree, 
            initial_values={"language": "python"}
        )
        
        assert result.formatted_string == "Using python version 3.9"
        assert "language" in result.resolved_keys
        assert "version" in result.resolved_keys
    
    def test_format_with_missing_keys(self):
        """未解決キー付きフォーマットのテスト"""
        data = {"version": "3.9"}
        tree = build_config_tree_pure(data)
        
        result = format_string_pure("Using {language} version {version}", tree)
        
        assert "version" in result.resolved_keys
        assert "language" in result.missing_keys
    
    def test_format_non_string_template(self):
        """非文字列テンプレートのテスト"""
        data = {"test": "value"}
        tree = build_config_tree_pure(data)
        
        result = format_string_pure(123, tree)
        
        assert result.formatted_string == "123"
        assert len(result.errors) == 1
        assert "Template must be a string" in result.errors[0]


class TestFormatNodeValuePure:
    """ノード値フォーマット関数のテスト"""
    
    def test_format_string_node(self):
        """文字列ノードのフォーマットテスト"""
        node = ConfigNodeData(
            key="test",
            value="Hello {name}",
            matches={"test"}
        )
        
        data = {"name": "World"}
        tree = build_config_tree_pure(data)
        
        result = format_node_value_pure(node, tree)
        
        assert result.formatted_string == "Hello World"
        assert "name" in result.resolved_keys
    
    def test_format_dict_value_node(self):
        """辞書値ノードのフォーマットテスト"""
        node = ConfigNodeData(
            key="test",
            value={"value": "Hello {name}"},
            matches={"test"}
        )
        
        data = {"name": "World"}
        tree = build_config_tree_pure(data)
        
        result = format_node_value_pure(node, tree)
        
        assert result.formatted_string == "Hello World"


class TestValidateConfigTreePure:
    """設定ツリー検証関数のテスト"""
    
    def test_validate_valid_tree(self):
        """有効なツリーの検証テスト"""
        data = {"test": {"value": "test_value"}}
        tree = build_config_tree_pure(data)
        
        errors = validate_config_tree_pure(tree)
        
        assert errors == []
    
    def test_validate_missing_root(self):
        """ルートなしツリーの検証テスト"""
        tree = ConfigTreeData(nodes={}, root_id="missing_root")
        
        errors = validate_config_tree_pure(tree)
        
        assert len(errors) >= 1
        assert "Root node not found" in errors[0]
    
    def test_validate_inconsistent_parent_child(self):
        """親子関係不整合ツリーの検証テスト"""
        parent_node = ConfigNodeData(
            key="parent",
            value="parent_value",
            matches={"parent"},
            children_ids=["child_1"]
        )
        child_node = ConfigNodeData(
            key="child",
            value="child_value",
            matches={"child"},
            parent_id="wrong_parent_id"
        )
        
        tree = ConfigTreeData(
            nodes={"parent_id": parent_node, "child_1": child_node},
            root_id="parent_id"
        )
        
        errors = validate_config_tree_pure(tree)
        
        assert len(errors) >= 1
        assert any("relationship inconsistent" in error for error in errors)


class TestCalculateTreeMetricsPure:
    """ツリーメトリクス計算関数のテスト"""
    
    def test_calculate_metrics_simple_tree(self):
        """シンプルなツリーのメトリクス計算テスト"""
        data = {
            "language": "python",
            "commands": {
                "build": "python build.py",
                "test": "python test.py"
            }
        }
        
        tree = build_config_tree_pure(data)
        metrics = calculate_tree_metrics_pure(tree)
        
        assert metrics["node_count"] > 0
        assert metrics["max_depth"] >= 1
        assert metrics["leaf_count"] >= 0
        assert metrics["avg_children"] >= 0
        assert metrics["total_matches"] > 0
    
    def test_calculate_metrics_empty_tree(self):
        """空ツリーのメトリクス計算テスト"""
        tree = ConfigTreeData(nodes={}, root_id="")
        
        metrics = calculate_tree_metrics_pure(tree)
        
        assert metrics["node_count"] == 0
        assert metrics["max_depth"] == 0
        assert metrics["leaf_count"] == 0
        assert metrics["avg_children"] == 0
        assert metrics["total_matches"] == 0


class TestHelperFunctions:
    """ヘルパー関数のテスト"""
    
    def test_extract_template_from_string_node(self):
        """文字列ノードからのテンプレート抽出テスト"""
        node = ConfigNodeData(
            key="test",
            value="Hello {name}",
            matches={"test"}
        )
        
        template = _extract_template_from_node_pure(node)
        
        assert template == "Hello {name}"
    
    def test_extract_template_from_dict_node(self):
        """辞書ノードからのテンプレート抽出テスト"""
        node = ConfigNodeData(
            key="test",
            value={"value": "Hello {name}"},
            matches={"test"}
        )
        
        template = _extract_template_from_node_pure(node)
        
        assert template == "Hello {name}"
    
    def test_extract_value_for_formatting_dict(self):
        """辞書からのフォーマット値抽出テスト"""
        value = {"value": "test_value"}
        
        result = _extract_value_for_formatting_pure(value)
        
        assert result == "test_value"
    
    def test_extract_value_for_formatting_string(self):
        """文字列からのフォーマット値抽出テスト"""
        value = "test_string"
        
        result = _extract_value_for_formatting_pure(value)
        
        assert result == "test_string"
    
    def test_extract_value_for_formatting_none(self):
        """None値のフォーマット値抽出テスト"""
        value = {"not_value": "test"}
        
        result = _extract_value_for_formatting_pure(value)
        
        assert result is None


class TestDataImmutability:
    """データ不変性のテスト"""
    
    def test_resolve_result_immutability(self):
        """ResolveResultの不変性テスト"""
        result = ResolveResult(nodes=[], paths_found=[], errors=[], warnings=[])
        
        with pytest.raises(AttributeError):
            result.nodes = []
    
    def test_format_result_immutability(self):
        """FormatResultの不変性テスト"""
        result = FormatResult(
            formatted_string="test",
            resolved_keys={},
            missing_keys=set(),
            errors=[]
        )
        
        with pytest.raises(AttributeError):
            result.formatted_string = "new_value"


class TestComplexScenarios:
    """複雑なシナリオのテスト"""
    
    def test_nested_resolution_scenario(self):
        """ネストした解決シナリオのテスト"""
        data = {
            "languages": {
                "python": {
                    "aliases": ["py", "python3"],
                    "commands": {
                        "build": {
                            "value": "python -m build",
                            "aliases": ["compile"]
                        },
                        "test": "python -m pytest"
                    }
                }
            }
        }
        
        tree = build_config_tree_pure(data)
        
        # エイリアスでの解決
        result = resolve_by_path_pure(tree, ["py", "commands", "compile"])
        assert len(result.nodes) >= 1
        
        # 値の解決
        values = resolve_values_pure(tree, ["python", "commands", "build"])
        assert len(values) >= 1
    
    def test_complex_formatting_scenario(self):
        """複雑なフォーマットシナリオのテスト"""
        data = {
            "project": {
                "name": "my_project",
                "language": "python",
                "version": "1.0.0"
            },
            "commands": {
                "build": "Building {project.name} v{version} using {language}"
            }
        }
        
        tree = build_config_tree_pure(data)
        
        # 複雑なフォーマット（一部は手動で解決が必要）
        result = format_string_pure(
            "Building {name} v{version} using {language}",
            tree,
            initial_values={"name": "my_project"}
        )
        
        assert "language" in result.resolved_keys
        assert "version" in result.resolved_keys
        assert result.resolved_keys["language"] == "python"
        assert result.resolved_keys["version"] == "1.0.0"