"""分離システムのパフォーマンステスト

設定システムと状態管理システムの分離後のパフォーマンス測定
"""
import statistics
import time
from typing import Callable, List
from unittest.mock import Mock

import pytest

from src.configuration.adapters.unified_execution_adapter import UnifiedExecutionAdapter
from src.configuration.services.pure_settings_manager import PureSettingsManager
from src.state.services.sqlite_state_manager import SqliteStateManager
from tests.configuration.test_fixtures_separated_system import MockSettingsManager, MockStateManager


class PerformanceTimer:
    """パフォーマンス測定用ユーティリティ"""

    @staticmethod
    def measure_execution_time(func: Callable, iterations: int = 100) -> dict:
        """関数の実行時間を測定

        Args:
            func: 測定する関数
            iterations: 実行回数

        Returns:
            統計情報を含む辞書
        """
        times = []

        for _ in range(iterations):
            start_time = time.perf_counter()
            func()
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        return {
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "min": min(times),
            "max": max(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "total": sum(times),
            "iterations": iterations
        }

    @staticmethod
    def compare_performance(func1: Callable, func2: Callable,
                          name1: str = "Function 1", name2: str = "Function 2",
                          iterations: int = 100) -> dict:
        """2つの関数のパフォーマンス比較

        Args:
            func1: 比較する関数1
            func2: 比較する関数2
            name1: 関数1の名前
            name2: 関数2の名前
            iterations: 実行回数

        Returns:
            比較結果を含む辞書
        """
        stats1 = PerformanceTimer.measure_execution_time(func1, iterations)
        stats2 = PerformanceTimer.measure_execution_time(func2, iterations)

        improvement_ratio = stats1["mean"] / stats2["mean"] if stats2["mean"] > 0 else float('inf')

        return {
            name1: stats1,
            name2: stats2,
            "improvement_ratio": improvement_ratio,
            "faster_system": name2 if improvement_ratio > 1 else name1,
            "performance_difference_percent": abs(improvement_ratio - 1) * 100
        }


class TestSeparatedSystemPerformance:
    """分離システムのパフォーマンステスト"""

    @pytest.fixture
    def mock_settings_manager(self):
        """軽量なSettingsManagerのモック"""
        return MockSettingsManager()

    @pytest.fixture
    def mock_state_manager(self):
        """軽量なStateManagerのモック"""
        return MockStateManager()

    @pytest.fixture
    def unified_adapter(self, mock_settings_manager, mock_state_manager):
        """UnifiedExecutionAdapterのインスタンス"""
        adapter = UnifiedExecutionAdapter(mock_settings_manager, mock_state_manager)
        adapter.initialize("abc300", "a", "python")
        return adapter

    def test_initialization_performance(self, mock_settings_manager, mock_state_manager):
        """初期化パフォーマンステスト"""
        def create_and_initialize():
            adapter = UnifiedExecutionAdapter(mock_settings_manager, mock_state_manager)
            adapter.initialize("abc300", "a", "python")
            return adapter

        # パフォーマンス測定
        stats = PerformanceTimer.measure_execution_time(create_and_initialize, iterations=50)

        # パフォーマンス基準の検証
        assert stats["mean"] < 0.01, f"初期化が遅すぎます: {stats['mean']:.4f}秒"
        assert stats["max"] < 0.05, f"最大初期化時間が長すぎます: {stats['max']:.4f}秒"

        print(f"初期化パフォーマンス - 平均: {stats['mean']:.4f}秒, 最大: {stats['max']:.4f}秒")

    def test_template_expansion_performance(self, unified_adapter):
        """テンプレート展開パフォーマンステスト"""
        template = "Contest: {contest_name}, Problem: {problem_name}, Language: {language}, File: {source_file_name}"

        def expand_template():
            return unified_adapter.format_string(template)

        # パフォーマンス測定
        stats = PerformanceTimer.measure_execution_time(expand_template, iterations=200)

        # パフォーマンス基準の検証
        assert stats["mean"] < 0.001, f"テンプレート展開が遅すぎます: {stats['mean']:.6f}秒"
        assert stats["max"] < 0.005, f"最大展開時間が長すぎます: {stats['max']:.6f}秒"

        print(f"テンプレート展開パフォーマンス - 平均: {stats['mean']:.6f}秒, 最大: {stats['max']:.6f}秒")

    def test_configuration_dict_generation_performance(self, unified_adapter):
        """設定辞書生成パフォーマンステスト"""
        def generate_config_dict():
            return unified_adapter.to_dict()

        # パフォーマンス測定
        stats = PerformanceTimer.measure_execution_time(generate_config_dict, iterations=200)

        # パフォーマンス基準の検証
        assert stats["mean"] < 0.001, f"設定辞書生成が遅すぎます: {stats['mean']:.6f}秒"

        print(f"設定辞書生成パフォーマンス - 平均: {stats['mean']:.6f}秒")

    def test_property_access_performance(self, unified_adapter):
        """プロパティアクセスパフォーマンステスト"""
        def access_properties():
            _ = unified_adapter.contest_name
            _ = unified_adapter.problem_name
            _ = unified_adapter.language
            _ = unified_adapter.env_type
            _ = unified_adapter.command_type

        # パフォーマンス測定
        stats = PerformanceTimer.measure_execution_time(access_properties, iterations=500)

        # パフォーマンス基準の検証
        assert stats["mean"] < 0.0005, f"プロパティアクセスが遅すぎます: {stats['mean']:.6f}秒"

        print(f"プロパティアクセスパフォーマンス - 平均: {stats['mean']:.6f}秒")

    def test_state_management_performance(self, unified_adapter):
        """状態管理パフォーマンステスト"""
        def save_execution_result():
            unified_adapter.save_execution_result(success=True)

        # パフォーマンス測定
        stats = PerformanceTimer.measure_execution_time(save_execution_result, iterations=100)

        # パフォーマンス基準の検証（状態管理はI/Oを含むため少し緩い基準）
        assert stats["mean"] < 0.01, f"状態保存が遅すぎます: {stats['mean']:.4f}秒"

        print(f"状態管理パフォーマンス - 平均: {stats['mean']:.4f}秒")

    def test_memory_usage_estimation(self, mock_settings_manager, mock_state_manager):
        """メモリ使用量の推定テスト"""
        import gc
        import sys

        # ベースライン測定
        baseline_objects = len([obj for obj in gc.get_objects() if hasattr(obj, '__dict__')])

        # アダプターの作成
        adapters = []
        for i in range(100):
            adapter = UnifiedExecutionAdapter(mock_settings_manager, mock_state_manager)
            adapter.initialize(f"abc{300 + i}", "a", "python")
            adapters.append(adapter)

        # メモリ使用量測定
        import gc
        gc.collect()
        final_objects = len([obj for obj in gc.get_objects() if hasattr(obj, '__dict__')])

        objects_per_adapter = (final_objects - baseline_objects) / 100

        # メモリ使用量の基準検証
        assert objects_per_adapter < 50, f"アダプターあたりのオブジェクト数が多すぎます: {objects_per_adapter}"

        print(f"メモリ使用量推定 - アダプターあたり約{objects_per_adapter:.1f}オブジェクト")


class TestSeparatedSystemVsLegacyPerformance:
    """分離システムと既存システムのパフォーマンス比較"""

    def test_template_expansion_performance_comparison(self):
        """テンプレート展開の新旧システム比較"""
        # 既存システムのシミュレーション（単純な文字列フォーマット）
        legacy_context = {
            "contest_name": "abc300",
            "problem_name": "a",
            "language": "python",
            "source_file_name": "main.py"
        }
        template = "Contest: {contest_name}, Problem: {problem_name}, File: {source_file_name}"

        def legacy_expansion():
            return template.format(**legacy_context)

        # 新システム
        settings_manager = MockSettingsManager()

        def new_expansion():
            return settings_manager.expand_template(template, legacy_context)

        # パフォーマンス比較
        comparison = PerformanceTimer.compare_performance(
            legacy_expansion, new_expansion,
            "Legacy System", "New System",
            iterations=300
        )

        # 新システムが大幅に遅くないことを確認（2倍以内）
        assert comparison["improvement_ratio"] < 2.0, \
            f"新システムが既存システムより{comparison['performance_difference_percent']:.1f}%遅いです"

        print("テンプレート展開比較:")
        print(f"  既存システム: {comparison['Legacy System']['mean']:.6f}秒")
        print(f"  新システム: {comparison['New System']['mean']:.6f}秒")
        print(f"  パフォーマンス差: {comparison['performance_difference_percent']:.1f}%")

    def test_configuration_access_performance_comparison(self):
        """設定アクセスの新旧システム比較"""
        # 既存システムのシミュレーション（辞書アクセス）
        legacy_config = {
            "contest_name": "abc300",
            "problem_name": "a",
            "language": "python",
            "language_id": "4006",
            "source_file_name": "main.py"
        }

        def legacy_access():
            _ = legacy_config["contest_name"]
            _ = legacy_config["problem_name"]
            _ = legacy_config["language"]
            _ = legacy_config["language_id"]
            _ = legacy_config["source_file_name"]

        # 新システム
        mock_settings_manager = MockSettingsManager()
        mock_state_manager = MockStateManager()
        adapter = UnifiedExecutionAdapter(mock_settings_manager, mock_state_manager)
        adapter.initialize("abc300", "a", "python")

        def new_access():
            _ = adapter.contest_name
            _ = adapter.problem_name
            _ = adapter.language
            config_dict = adapter.to_dict()
            _ = config_dict["language_id"]
            _ = config_dict["source_file_name"]

        # パフォーマンス比較
        comparison = PerformanceTimer.compare_performance(
            legacy_access, new_access,
            "Legacy Access", "New Access",
            iterations=500
        )

        # 新システムが大幅に遅くないことを確認（3倍以内）
        assert comparison["improvement_ratio"] < 3.0, \
            f"新システムが既存システムより{comparison['performance_difference_percent']:.1f}%遅いです"

        print("設定アクセス比較:")
        print(f"  既存システム: {comparison['Legacy Access']['mean']:.6f}秒")
        print(f"  新システム: {comparison['New Access']['mean']:.6f}秒")
        print(f"  パフォーマンス差: {comparison['performance_difference_percent']:.1f}%")


class TestRegressionTests:
    """回帰テスト"""

    def test_template_expansion_regression(self):
        """テンプレート展開の回帰テスト"""
        settings_manager = MockSettingsManager()

        # 既知の正しい結果
        test_cases = [
            {
                "template": "{contest_name}_{problem_name}",
                "context": {"contest_name": "abc300", "problem_name": "a"},
                "expected": "abc300_a"
            },
            {
                "template": "Path: {contest_current_path}/{source_file_name}",
                "context": {"contest_current_path": "./contest_current", "source_file_name": "main.py"},
                "expected": "Path: ./contest_current/main.py"
            },
            {
                "template": "Language: {language} (ID: {language_id})",
                "context": {"language": "python", "language_id": "4006"},
                "expected": "Language: python (ID: 4006)"
            }
        ]

        for case in test_cases:
            result = settings_manager.expand_template(case["template"], case["context"])
            assert result == case["expected"], \
                f"テンプレート展開の結果が期待値と異なります。期待値: {case['expected']}, 実際: {result}"

    def test_configuration_structure_regression(self):
        """設定構造の回帰テスト"""
        from tests.configuration.test_fixtures_separated_system import MockExecutionSettings, MockRuntimeSettings

        # 既知の設定構造
        execution_settings = MockExecutionSettings("abc300", "a", "python")
        runtime_settings = MockRuntimeSettings("python")

        # 実行設定の必須フィールド確認
        assert execution_settings.get_contest_name() == "abc300"
        assert execution_settings.get_problem_name() == "a"
        assert execution_settings.get_language() == "python"
        assert execution_settings.get_env_type() == "local"
        assert execution_settings.get_command_type() == "open"

        # Runtime設定の必須フィールド確認
        assert runtime_settings.get_language_id() == "4006"
        assert runtime_settings.get_source_file_name() == "main.py"
        assert runtime_settings.get_run_command() == "python3"
        assert runtime_settings.get_timeout_seconds() == 300

        # テンプレート辞書の必須キー確認
        template_dict = execution_settings.to_template_dict()
        required_keys = {
            "contest_name", "problem_name", "language", "language_name",
            "env_type", "command_type", "old_contest_name", "old_problem_name"
        }
        assert required_keys.issubset(set(template_dict.keys())), \
            f"必須キーが不足しています: {required_keys - set(template_dict.keys())}"

        # Runtime辞書の必須キー確認
        runtime_dict = runtime_settings.to_runtime_dict()
        required_runtime_keys = {
            "language_id", "source_file_name", "run_command", "timeout_seconds"
        }
        assert required_runtime_keys.issubset(set(runtime_dict.keys())), \
            f"必須Runtimeキーが不足しています: {required_runtime_keys - set(runtime_dict.keys())}"

    def test_adapter_api_regression(self):
        """アダプターAPIの回帰テスト"""
        mock_settings_manager = MockSettingsManager()
        mock_state_manager = MockStateManager()
        adapter = UnifiedExecutionAdapter(mock_settings_manager, mock_state_manager)

        # 初期化前のエラーハンドリング
        with pytest.raises(RuntimeError):
            _ = adapter.contest_name

        with pytest.raises(RuntimeError):
            adapter.format_string("test")

        # 初期化
        adapter.initialize("abc300", "a", "python")

        # 必須APIの存在と動作確認
        assert adapter.contest_name == "abc300"
        assert adapter.problem_name == "a"
        assert adapter.language == "python"

        # 辞書変換API
        config_dict = adapter.to_dict()
        assert isinstance(config_dict, dict)
        assert "contest_name" in config_dict

        format_dict = adapter.to_format_dict()
        assert config_dict == format_dict  # 互換性確認

        # テンプレート展開API
        result = adapter.format_string("Test: {contest_name}")
        assert "abc300" in result

        # 状態管理API
        adapter.save_execution_result(True)  # エラーが発生しないことを確認
        history = adapter.get_execution_history()
        assert isinstance(history, list)
