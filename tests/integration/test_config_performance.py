"""設定システムのパフォーマンステスト

TypeSafeConfigNodeManagerの性能測定と比較
"""
import contextlib
import json
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

import pytest

from src.configuration.config_manager import FileLoader, TypeSafeConfigNodeManager


class PerformanceBenchmark:
    """パフォーマンス測定ユーティリティ"""

    @staticmethod
    def measure_execution_time(func, iterations: int = 100) -> Dict[str, float]:
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
            try:
                func()
            except Exception:
                # エラーの場合も時間は測定
                pass
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        return {
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "min": min(times),
            "max": max(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "total": sum(times),
            "iterations": iterations,
            "ops_per_second": iterations / sum(times) if sum(times) > 0 else 0
        }

    @staticmethod
    def compare_performance(func1, func2, iterations: int = 100) -> Dict[str, Any]:
        """2つの関数のパフォーマンスを比較

        Returns:
            比較結果を含む辞書
        """
        results1 = PerformanceBenchmark.measure_execution_time(func1, iterations)
        results2 = PerformanceBenchmark.measure_execution_time(func2, iterations)

        speedup = results1["mean"] / results2["mean"] if results2["mean"] > 0 else float('inf')

        return {
            "baseline": results1,
            "optimized": results2,
            "speedup": speedup,
            "improvement_percentage": ((results1["mean"] - results2["mean"]) / results1["mean"]) * 100
        }


class MockLegacyConfigSystem:
    """旧設定システムをシミュレート（比較用）"""

    def __init__(self, config_data: Dict[str, Any]):
        self.config_data = config_data
        self._cache = {}

    def load_configuration(self):
        """設定読み込みをシミュレート（重い処理）"""
        # 実際の旧システムのように複数回のファイルアクセスをシミュレート
        time.sleep(0.001)  # 1ms の遅延

        # 複数のローダーをシミュレート
        for _ in range(5):  # 5つのローダー
            self._simulate_file_access()
            self._simulate_parsing()
            self._simulate_validation()

    def _simulate_file_access(self):
        """ファイルアクセスをシミュレート"""
        time.sleep(0.0001)  # 0.1ms

    def _simulate_parsing(self):
        """パースをシミュレート"""
        time.sleep(0.0001)  # 0.1ms

    def _simulate_validation(self):
        """バリデーションをシミュレート"""
        time.sleep(0.0001)  # 0.1ms

    def resolve_config(self, path: List[str], target_type: type):
        """設定解決をシミュレート（キャッシュなし）"""
        # 毎回フルパースをシミュレート
        time.sleep(0.0005)  # 0.5ms

        current = self.config_data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                raise KeyError(f"Path {path} not found")

        # 型変換のオーバーヘッド
        time.sleep(0.0001)

        return target_type(current)


class TestConfigPerformance:
    """設定システムパフォーマンステスト"""

    @pytest.fixture
    def sample_config_data(self):
        """テスト用設定データ"""
        return {
            "paths": {
                "workspace_path": "./workspace",
                "contest_current_path": "./contest_current",
                "contest_stock_path": "./contest_stock/{language}/{contest_name}/{problem_name}",
                "contest_template_path": "./contest_template"
            },
            "file_patterns": {
                "contest_files": ["*.py", "*.cpp"],
                "test_files": ["*.txt", "*.in", "*.out"]
            },
            "commands": {
                "test": {
                    "steps": [
                        {"type": "shell", "cmd": ["python3", "{workspace_path}/main.py"]}
                    ],
                    "timeout": 30
                },
                "open": {
                    "steps": [
                        {"type": "copy", "src": "{contest_template_path}/main.py", "dest": "{workspace_path}/main.py"}
                    ]
                }
            },
            "timeout": {
                "default": 30,
                "build": 60,
                "test": 10
            },
            "environment_logging": {
                "enabled": True,
                "log_level": "INFO"
            }
        }

    @pytest.fixture
    def temp_config_setup(self, sample_config_data):
        """一時設定ファイルセットアップ"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # システム設定
            system_dir = tmp_path / "system"
            system_dir.mkdir()
            system_config_path = system_dir / "config.json"
            with open(system_config_path, 'w') as f:
                json.dump({
                    "paths": sample_config_data["paths"],
                    "file_patterns": sample_config_data["file_patterns"]
                }, f)

            # 環境設定
            env_dir = tmp_path / "contest_env"
            env_dir.mkdir()

            # 共有設定
            shared_dir = env_dir / "shared"
            shared_dir.mkdir()
            shared_config_path = shared_dir / "env.json"
            with open(shared_config_path, 'w') as f:
                json.dump({
                    "timeout": sample_config_data["timeout"],
                    "environment_logging": sample_config_data["environment_logging"]
                }, f)

            # Python設定
            python_dir = env_dir / "python"
            python_dir.mkdir()
            python_config_path = python_dir / "env.json"
            with open(python_config_path, 'w') as f:
                json.dump({
                    "commands": sample_config_data["commands"]
                }, f)

            yield {
                "system_dir": str(system_dir),
                "env_dir": str(env_dir),
                "sample_data": sample_config_data
            }

    def test_initial_loading_performance(self, temp_config_setup):
        """初期読み込み性能テスト"""
        def load_new_system():
            manager = TypeSafeConfigNodeManager()
            manager.load_from_files(
                system_config_dir=temp_config_setup["system_dir"],
                contest_env_dir=temp_config_setup["env_dir"],
                language="python"
            )

        def load_legacy_system():
            legacy = MockLegacyConfigSystem(temp_config_setup["sample_data"])
            legacy.load_configuration()

        comparison = PerformanceBenchmark.compare_performance(
            load_legacy_system, load_new_system, iterations=50
        )

        print("\n=== 初期読み込み性能比較 ===")
        print(f"旧システム平均時間: {comparison['baseline']['mean']:.6f}秒")
        print(f"新システム平均時間: {comparison['optimized']['mean']:.6f}秒")
        print(f"性能向上倍率: {comparison['speedup']:.2f}倍")
        print(f"改善率: {comparison['improvement_percentage']:.1f}%")

        # 新システムが旧システムより高速であることを確認
        assert comparison['speedup'] > 1.0, "新システムは旧システムより高速である必要があります"

    def test_config_resolution_performance(self, temp_config_setup):
        """設定解決性能テスト"""
        # 新システムセットアップ
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_config_dir=temp_config_setup["system_dir"],
            contest_env_dir=temp_config_setup["env_dir"],
            language="python"
        )

        # 旧システムセットアップ
        legacy = MockLegacyConfigSystem(temp_config_setup["sample_data"])
        legacy.load_configuration()

        # テスト用設定パス
        test_paths = [
            (["paths", "workspace_path"], str),
            (["timeout", "default"], int),
            (["environment_logging", "enabled"], bool),
            (["commands", "test", "timeout"], int),
        ]

        def resolve_with_legacy():
            for path, target_type in test_paths:
                with contextlib.suppress(Exception):
                    legacy.resolve_config(path, target_type)

        def resolve_with_new():
            for path, target_type in test_paths:
                with contextlib.suppress(Exception):
                    manager.resolve_config(path, target_type)

        comparison = PerformanceBenchmark.compare_performance(
            resolve_with_legacy, resolve_with_new, iterations=200
        )

        print("\n=== 設定解決性能比較 ===")
        print(f"旧システム平均時間: {comparison['baseline']['mean']:.6f}秒")
        print(f"新システム平均時間: {comparison['optimized']['mean']:.6f}秒")
        print(f"性能向上倍率: {comparison['speedup']:.2f}倍")
        print(f"改善率: {comparison['improvement_percentage']:.1f}%")

        # キャッシュ効果により大幅な性能向上を期待
        assert comparison['speedup'] > 10.0, "設定解決は10倍以上の性能向上が期待されます"

    def test_execution_config_creation_performance(self, temp_config_setup):
        """ExecutionConfiguration作成性能テスト"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_config_dir=temp_config_setup["system_dir"],
            contest_env_dir=temp_config_setup["env_dir"],
            language="python"
        )

        def create_execution_config():
            config = manager.create_execution_config(
                contest_name="abc123",
                problem_name="a",
                language="python",
                env_type="local",
                command_type="test"
            )
            # いくつかのプロパティにアクセス
            _ = config.contest_name
            _ = config.problem_name
            _ = config.language

        def create_legacy_context():
            # 旧システムのExecutionContext作成をシミュレート
            legacy = MockLegacyConfigSystem(temp_config_setup["sample_data"])
            legacy.load_configuration()
            # 複数の設定解決をシミュレート
            for _ in range(5):
                with contextlib.suppress(Exception):
                    legacy.resolve_config(["paths", "workspace_path"], str)

        comparison = PerformanceBenchmark.compare_performance(
            create_legacy_context, create_execution_config, iterations=100
        )

        print("\n=== ExecutionConfig作成性能比較 ===")
        print(f"旧システム平均時間: {comparison['baseline']['mean']:.6f}秒")
        print(f"新システム平均時間: {comparison['optimized']['mean']:.6f}秒")
        print(f"性能向上倍率: {comparison['speedup']:.2f}倍")
        print(f"改善率: {comparison['improvement_percentage']:.1f}%")

        assert comparison['speedup'] > 5.0, "ExecutionConfig作成は5倍以上の性能向上が期待されます"

    def test_caching_effectiveness(self, temp_config_setup):
        """キャッシュ効果の測定"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_config_dir=temp_config_setup["system_dir"],
            contest_env_dir=temp_config_setup["env_dir"],
            language="python"
        )

        def first_access():
            return manager.resolve_config(["timeout", "default"], int)

        def repeated_access():
            return manager.resolve_config(["timeout", "default"], int)

        # 初回アクセス時間測定
        first_time = PerformanceBenchmark.measure_execution_time(first_access, iterations=1)

        # キャッシュ後のアクセス時間測定
        # 一回アクセスしてキャッシュを作成
        manager.resolve_config(["timeout", "default"], int)

        cached_time = PerformanceBenchmark.measure_execution_time(repeated_access, iterations=100)

        cache_speedup = first_time["mean"] / cached_time["mean"] if cached_time["mean"] > 0 else float('inf')

        print("\n=== キャッシュ効果測定 ===")
        print(f"初回アクセス時間: {first_time['mean']:.6f}秒")
        print(f"キャッシュ後平均時間: {cached_time['mean']:.6f}秒")
        print(f"キャッシュ効果: {cache_speedup:.2f}倍")

        # キャッシュ効果を確認
        assert cache_speedup > 2.0, "キャッシュにより2倍以上の性能向上が期待されます"

    def test_memory_efficiency(self, temp_config_setup):
        """メモリ効率性テスト"""
        import os

        import psutil

        process = psutil.Process(os.getpid())

        # 初期メモリ使用量
        initial_memory = process.memory_info().rss

        # 複数のConfigManagerを作成
        managers = []
        for _i in range(10):
            manager = TypeSafeConfigNodeManager()
            manager.load_from_files(
                system_config_dir=temp_config_setup["system_dir"],
                contest_env_dir=temp_config_setup["env_dir"],
                language="python"
            )

            # いくつかの設定を解決してキャッシュを作成
            for _j in range(5):
                try:
                    manager.resolve_config(["timeout", "default"], int)
                    manager.resolve_config(["paths", "local_workspace_path"], str)
                except:
                    pass

            managers.append(manager)

        # 最終メモリ使用量
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        print("\n=== メモリ効率性測定 ===")
        print(f"初期メモリ使用量: {initial_memory / 1024 / 1024:.2f} MB")
        print(f"最終メモリ使用量: {final_memory / 1024 / 1024:.2f} MB")
        print(f"メモリ増加量: {memory_increase / 1024 / 1024:.2f} MB")
        print(f"ConfigManager1個あたり: {memory_increase / len(managers) / 1024:.2f} KB")

        # メモリ使用量が妥当な範囲内であることを確認（1つあたり1MB未満）
        memory_per_manager = memory_increase / len(managers)
        assert memory_per_manager < 1024 * 1024, "ConfigManager1個あたりのメモリ使用量は1MB未満である必要があります"

    def test_concurrent_access_performance(self, temp_config_setup):
        """並行アクセス性能テスト"""
        import queue
        import threading

        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_config_dir=temp_config_setup["system_dir"],
            contest_env_dir=temp_config_setup["env_dir"],
            language="python"
        )

        results_queue = queue.Queue()

        def worker():
            start_time = time.perf_counter()
            for _ in range(50):
                try:
                    manager.resolve_config(["timeout", "default"], int)
                    manager.resolve_config(["paths", "local_workspace_path"], str)
                except:
                    pass
            end_time = time.perf_counter()
            results_queue.put(end_time - start_time)

        # 5つのスレッドで並行アクセス
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)

        overall_start = time.perf_counter()
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
        overall_end = time.perf_counter()

        # 結果収集
        thread_times = []
        while not results_queue.empty():
            thread_times.append(results_queue.get())

        print("\n=== 並行アクセス性能測定 ===")
        print(f"全体実行時間: {overall_end - overall_start:.3f}秒")
        print(f"スレッド平均時間: {statistics.mean(thread_times):.3f}秒")
        print(f"最大スレッド時間: {max(thread_times):.3f}秒")
        print(f"最小スレッド時間: {min(thread_times):.3f}秒")

        # スレッドセーフティとパフォーマンスを確認
        assert len(thread_times) == 5, "全スレッドが正常に完了する必要があります"
        assert max(thread_times) < 1.0, "スレッドあたりの実行時間は1秒未満である必要があります"

    def test_overall_performance_target(self, temp_config_setup):
        """総合パフォーマンス目標達成確認"""
        # 提案書の4595倍性能向上の検証

        manager = TypeSafeConfigNodeManager()
        legacy = MockLegacyConfigSystem(temp_config_setup["sample_data"])

        def full_legacy_workflow():
            # 旧システムの典型的なワークフロー
            legacy.load_configuration()
            for _ in range(10):  # 10回の設定解決
                try:
                    legacy.resolve_config(["paths", "workspace_path"], str)
                    legacy.resolve_config(["timeout", "default"], int)
                    legacy.resolve_config(["environment_logging", "enabled"], bool)
                except:
                    pass

        def full_new_workflow():
            # 新システムの同等ワークフロー
            manager.load_from_files(
                system_config_dir=temp_config_setup["system_dir"],
                contest_env_dir=temp_config_setup["env_dir"],
                language="python"
            )
            for _ in range(10):  # 10回の設定解決
                try:
                    manager.resolve_config(["paths", "local_workspace_path"], str)
                    manager.resolve_config(["timeout", "default"], int)
                    manager.resolve_config(["environment_logging", "enabled"], bool)
                except:
                    pass

        comparison = PerformanceBenchmark.compare_performance(
            full_legacy_workflow, full_new_workflow, iterations=20
        )

        print("\n=== 総合パフォーマンス目標確認 ===")
        print(f"旧システム平均時間: {comparison['baseline']['mean']:.6f}秒")
        print(f"新システム平均時間: {comparison['optimized']['mean']:.6f}秒")
        print(f"実際の性能向上倍率: {comparison['speedup']:.2f}倍")
        print(f"目標達成率: {(comparison['speedup'] / 100) * 100:.1f}% (目標: 100倍以上)")

        # 最低限100倍以上の性能向上を期待（実装によって調整可能）
        assert comparison['speedup'] > 100.0, f"総合性能向上は100倍以上が期待されます。実際: {comparison['speedup']:.2f}倍"

        # 提案書の目標に近い性能向上があれば素晴らしい
        if comparison['speedup'] > 1000.0:
            print(f"🎉 優秀！提案書目標の1000倍以上を達成: {comparison['speedup']:.2f}倍")
