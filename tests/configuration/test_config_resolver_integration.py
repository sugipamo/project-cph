"""ConfigNode解決機能の統合テスト"""
import unittest
from pathlib import Path

from src.configuration import ExecutionConfiguration, ExecutionPaths, OutputConfig, RuntimeConfig
from src.configuration.adapters.execution_context_adapter import ExecutionContextAdapter
from src.configuration.expansion.template_expander import TemplateExpander
from src.configuration.resolvers.config_resolver import ConfigNode, ConfigurationResolver, create_config_resolver


class TestConfigNodeIntegration(unittest.TestCase):
    """ConfigNode機能の統合テスト"""

    def setUp(self):
        """テスト用設定の準備"""
        self.config = ExecutionConfiguration(
            contest_name='abc123',
            problem_name='problem_a',
            language='python',
            env_type='local',
            command_type='test',
            paths=ExecutionPaths(
                workspace=Path('./workspace'),
                contest_current=Path('./contest_current'),
                contest_stock=Path('./contest_stock'),
                contest_template=Path('./contest_template'),
                contest_temp=Path('./contest_temp')
            ),
            file_patterns={},
            runtime_config=RuntimeConfig(
                language_id='3.11.1',
                source_file_name='main.py',
                run_command='python3',
                timeout_seconds=30,
                retry_settings={}
            ),
            output_config=OutputConfig(
                show_workflow_summary=True,
                show_step_details=True,
                show_execution_completion=True,
                format_preset='default'
            )
        )

        # テスト用のenv_json
        self.env_json = {
            "python": {
                "language_id": "python3.11",
                "source_file_name": "main.py",
                "run_command": "python3",
                "aliases": ["py", "python3"]
            },
            "cpp": {
                "language_id": "cpp17",
                "source_file_name": "main.cpp",
                "run_command": "./main",
                "aliases": ["c++"]
            },
            "shared": {
                "timeout": 30,
                "retry_count": 3
            }
        }

    def test_config_node_creation(self):
        """ConfigNode作成のテスト"""
        node = ConfigNode("test", "value")
        self.assertEqual(node.key, "test")
        self.assertEqual(node.value, "value")
        self.assertIn("test", node.matches)
        self.assertIn("*", node.matches)

    def test_config_node_edge_addition(self):
        """ConfigNodeエッジ追加のテスト"""
        parent = ConfigNode("parent")
        child = ConfigNode("child")

        parent.add_edge(child)

        self.assertIn(child, parent.next_nodes)
        self.assertEqual(child.parent, parent)

    def test_config_node_path(self):
        """ConfigNodeパス取得のテスト"""
        root = ConfigNode("root")
        level1 = ConfigNode("level1")
        level2 = ConfigNode("level2")

        root.add_edge(level1)
        level1.add_edge(level2)

        path = level2.path()
        self.assertEqual(path, ["level1", "level2"])

    def test_configuration_resolver_creation(self):
        """ConfigurationResolver作成のテスト"""
        resolver = ConfigurationResolver(self.config)
        root = resolver.create_config_root_from_dict(self.env_json)

        self.assertEqual(root.key, "root")
        self.assertEqual(root.value, self.env_json)

        # 子ノードの確認
        python_nodes = root.next_nodes_with_key("python")
        self.assertEqual(len(python_nodes), 1)
        self.assertEqual(python_nodes[0].key, "python")

    def test_configuration_resolver_path_resolution(self):
        """ConfigurationResolverパス解決のテスト"""
        resolver = ConfigurationResolver(self.config)
        resolver.create_config_root_from_dict(self.env_json)

        # python.language_id の解決
        value = resolver.resolve_value(["python", "language_id"])
        self.assertEqual(value, "python3.11")

        # 存在しないパスの解決
        value = resolver.resolve_value(["nonexistent", "key"], "default")
        self.assertEqual(value, "default")

        # shared.timeout の解決
        value = resolver.resolve_value(["shared", "timeout"])
        self.assertEqual(value, 30)

    def test_configuration_resolver_alias_resolution(self):
        """エイリアス解決のテスト"""
        resolver = ConfigurationResolver(self.config)
        resolver.create_config_root_from_dict(self.env_json)

        # エイリアス 'py' で python の language_id を解決
        value = resolver.resolve_value(["py", "language_id"])
        self.assertEqual(value, "python3.11")

        # エイリアス 'c++' で cpp の source_file_name を解決
        value = resolver.resolve_value(["c++", "source_file_name"])
        self.assertEqual(value, "main.cpp")

    def test_execution_context_adapter_config_resolution(self):
        """ExecutionContextAdapterでのConfig解決テスト"""
        expander = TemplateExpander(self.config)
        adapter = ExecutionContextAdapter(self.config, expander)

        # env_jsonを設定（自動的にconfig_resolverが初期化される）
        adapter.env_json = self.env_json

        # 設定値の解決
        language_id = adapter.resolve_config_value(["python", "language_id"])
        self.assertEqual(language_id, "python3.11")

        # エイリアスでの解決
        source_file = adapter.resolve_config_value(["py", "source_file_name"])
        self.assertEqual(source_file, "main.py")

        # デフォルト値の確認
        nonexistent = adapter.resolve_config_value(["nonexistent"], "default_value")
        self.assertEqual(nonexistent, "default_value")

    def test_execution_context_adapter_multiple_values(self):
        """複数値解決のテスト"""
        expander = TemplateExpander(self.config)
        adapter = ExecutionContextAdapter(self.config, expander)
        adapter.env_json = self.env_json

        # 複数の値を解決
        values = adapter.resolve_config_values(["python", "language_id"])
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0], "python3.11")

    def test_config_resolver_integration_with_template_expander(self):
        """設定解決とテンプレート展開の統合テスト"""
        resolver = ConfigurationResolver(self.config)
        resolver.create_config_root_from_dict(self.env_json)

        # format_with_resolverメソッドのテスト
        template = "Language: {language}, Contest: {contest_name}"
        result = resolver.format_with_resolver(template)
        expected = "Language: python, Contest: abc123"
        self.assertEqual(result, expected)

    def test_create_config_resolver_helper(self):
        """create_config_resolverヘルパー関数のテスト"""
        resolver = create_config_resolver(self.config, self.env_json)

        self.assertIsInstance(resolver, ConfigurationResolver)

        # 解決機能の確認
        value = resolver.resolve_value(["python", "run_command"])
        self.assertEqual(value, "python3")

    def test_config_node_edge_cases(self):
        """ConfigNodeのエッジケーステスト"""
        # 空の辞書
        resolver = ConfigurationResolver(self.config)
        root = resolver.create_config_root_from_dict({})
        self.assertEqual(root.key, "root")
        self.assertEqual(len(root.next_nodes), 0)

        # リスト構造
        test_data = {"items": [{"name": "item1"}, {"name": "item2"}]}
        root = resolver.create_config_root_from_dict(test_data)

        items_nodes = root.next_nodes_with_key("items")
        self.assertEqual(len(items_nodes), 1)

        items_node = items_nodes[0]
        self.assertEqual(len(items_node.next_nodes), 2)  # 2つのアイテム

    def test_performance_with_large_config(self):
        """大規模設定での パフォーマンステスト"""
        import time

        # 大規模な設定を生成
        large_config = {}
        for i in range(100):
            large_config[f"lang_{i}"] = {
                "language_id": f"lang_{i}_id",
                "source_file": f"main_{i}.ext",
                "commands": [f"cmd_{j}" for j in range(10)]
            }

        resolver = ConfigurationResolver(self.config)

        start_time = time.time()
        resolver.create_config_root_from_dict(large_config)

        # 100回の解決を実行
        for i in range(100):
            value = resolver.resolve_value([f"lang_{i}", "language_id"])
            self.assertEqual(value, f"lang_{i}_id")

        end_time = time.time()
        execution_time = end_time - start_time

        # 大規模設定でも1秒以内に完了することを確認
        self.assertLess(execution_time, 1.0,
                       f"Performance test failed: {execution_time:.3f}s for large config")


if __name__ == '__main__':
    unittest.main()
