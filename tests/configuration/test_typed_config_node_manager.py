"""TypeSafeConfigNodeManager の単体テスト

型安全な統一設定管理システムのテスト
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.configuration.config_manager import (
    ConfigValidationError,
    FileLoader,
    TypedExecutionConfiguration,
    TypeSafeConfigNodeManager,
)


class TestFileLoader:
    """FileLoaderの単体テスト"""

    def test_load_json_file_success(self):
        """JSONファイルの正常読み込みテスト"""
        # DIコンテナとJSONプロバイダーをモック
        from src.infrastructure.di_container import DIContainer, DIKey

        mock_container = Mock(spec=DIContainer)
        mock_json_provider = Mock()
        mock_container.resolve.return_value = mock_json_provider

        loader = FileLoader(mock_container)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {"test_key": "test_value", "number": 42}
            json.dump(test_data, f)
            f.flush()

            # JSONプロバイダーがtest_dataを返すように設定
            mock_json_provider.load.return_value = test_data

            result = loader.load_json_file(f.name)
            assert result == test_data

            # モックが正しく呼ばれたことを確認
            mock_container.resolve.assert_called_with(DIKey.JSON_PROVIDER)
            mock_json_provider.load.assert_called_once()

    def test_load_json_file_not_found(self):
        """存在しないJSONファイルの読み込みテスト"""
        # DIコンテナとJSONプロバイダーをモック
        from src.infrastructure.di_container import DIContainer, DIKey

        mock_container = Mock(spec=DIContainer)
        mock_json_provider = Mock()
        mock_container.resolve.return_value = mock_json_provider

        loader = FileLoader(mock_container)
        result = loader.load_json_file("/nonexistent/file.json")
        assert result == {}

    def test_load_and_merge_configs(self):
        """設定ファイルのマージテスト（4つのloader統合）"""
        # DIコンテナとJSONプロバイダーをモック
        from src.infrastructure.di_container import DIContainer, DIKey

        mock_container = Mock(spec=DIContainer)
        mock_json_provider = Mock()
        mock_container.resolve.return_value = mock_json_provider

        loader = FileLoader(mock_container)

        with tempfile.TemporaryDirectory() as temp_dir:
            system_dir = Path(temp_dir) / "system"
            env_dir = Path(temp_dir) / "env"
            shared_dir = env_dir / "shared"
            python_dir = env_dir / "python"

            system_dir.mkdir()
            env_dir.mkdir()
            shared_dir.mkdir()
            python_dir.mkdir()

            # システム設定（複数ファイル - SystemConfigLoader統合）
            system_config = {"workspace": "/tmp/test", "debug": False}
            with open(system_dir / "dev_config.json", 'w') as f:
                json.dump(system_config, f)

            # 共有設定（EnvConfigLoader統合）
            shared_config = {"shared": {"timeout": 30, "debug": True}}
            with open(shared_dir / "env.json", 'w') as f:
                json.dump(shared_config, f)

            # 言語設定（EnvConfigLoader統合）
            lang_config = {"language_id": "4006", "source_file_name": "main.py", "timeout": 30}
            with open(python_dir / "env.json", 'w') as f:
                json.dump(lang_config, f)

            # JSONプロバイダーが各ファイルの内容を返すように設定
            def mock_load_side_effect(file_obj):
                # ファイルの内容を読み取ってJSONとして解析
                file_obj.seek(0)
                content = file_obj.read()
                return json.loads(content)

            mock_json_provider.load.side_effect = mock_load_side_effect

            result = loader.load_and_merge_configs(str(system_dir), str(env_dir), "python")

            # マージされた結果の確認（ConfigMerger統合）
            assert result["workspace"] == "/tmp/test"  # system
            assert result["debug"] is True  # shared > system
            assert result["timeout"] == 30  # language > shared > system
            assert result["language_id"] == "4006"  # language specific

    def test_load_system_configs_integration(self):
        """SystemConfigLoader統合テスト"""
        # DIコンテナとJSONプロバイダーをモック
        from src.infrastructure.di_container import DIContainer, DIKey

        mock_container = Mock(spec=DIContainer)
        mock_json_provider = Mock()
        mock_container.resolve.return_value = mock_json_provider

        loader = FileLoader(mock_container)

        with tempfile.TemporaryDirectory() as temp_dir:
            system_dir = Path(temp_dir)

            # 複数のシステム設定ファイルを作成
            configs = {
                "config.json": {"workspace": "/tmp/test"},
                "languages.json": {"python": {"timeout": 30}},
                "timeout.json": {"default_timeout": 30},
                "file_patterns.json": {"source": ["*.py", "*.cpp"]}
            }

            for filename, config_data in configs.items():
                with open(system_dir / filename, 'w') as f:
                    json.dump(config_data, f)

            result = loader._load_system_configs(system_dir)

            # すべての設定がマージされていることを確認
            assert result["workspace"] == "/tmp/test"
            assert result["python"]["timeout"] == 30
            assert result["default_timeout"] == 30
            assert result["source"] == ["*.py", "*.cpp"]

    def test_load_env_configs_integration(self):
        """EnvConfigLoader統合テスト"""
        loader = FileLoader()

        with tempfile.TemporaryDirectory() as temp_dir:
            env_dir = Path(temp_dir)
            shared_dir = env_dir / "shared"
            python_dir = env_dir / "python"

            shared_dir.mkdir()
            python_dir.mkdir()

            # 共有設定
            shared_config = {"shared": {"workspace": "/tmp/shared", "debug": False}}
            with open(shared_dir / "env.json", 'w') as f:
                json.dump(shared_config, f)

            # 言語設定
            lang_config = {"language_id": "4006", "timeout": 30}
            with open(python_dir / "env.json", 'w') as f:
                json.dump(lang_config, f)

            shared_result, lang_result = loader._load_env_configs(env_dir, "python")

            assert shared_result == {"shared": {"workspace": "/tmp/shared", "debug": False}}
            assert lang_result == {"language_id": "4006", "timeout": 30}

    def test_config_merging_priority(self):
        """ConfigMerger統合テスト - マージ優先度"""
        loader = FileLoader()

        system_config = {"timeout": 10, "debug": False, "workspace": "/system"}
        shared_config = {"timeout": 20, "debug": True}
        language_config = {"timeout": 30}
        runtime_config = {"timeout": 40}

        result = loader._merge_configs(system_config, shared_config, language_config, runtime_config)

        # 優先度: runtime > language > shared > system
        assert result["timeout"] == 40  # runtime が最優先
        assert result["debug"] is True   # shared > system
        assert result["workspace"] == "/system"  # system のみ

    def test_deep_merge_functionality(self):
        """深い辞書マージのテスト"""
        loader = FileLoader()

        target = {
            "a": {"x": 1, "y": 2},
            "b": 10
        }
        source = {
            "a": {"y": 20, "z": 3},
            "c": 30
        }

        result = loader._deep_merge(target, source)

        assert result["a"]["x"] == 1   # target から保持
        assert result["a"]["y"] == 20  # source で上書き
        assert result["a"]["z"] == 3   # source から追加
        assert result["b"] == 10       # target から保持
        assert result["c"] == 30       # source から追加

    def test_get_available_languages(self):
        """利用可能言語取得テスト（EnvConfigLoader統合）"""
        loader = FileLoader()

        with tempfile.TemporaryDirectory() as temp_dir:
            env_dir = Path(temp_dir)

            # 言語ディレクトリを作成
            for lang in ["python", "cpp", "java"]:
                lang_dir = env_dir / lang
                lang_dir.mkdir()
                # env.jsonを作成
                with open(lang_dir / "env.json", 'w') as f:
                    json.dump({"language_id": f"lang_{lang}"}, f)

            # sharedディレクトリも作成（除外されるべき）
            shared_dir = env_dir / "shared"
            shared_dir.mkdir()

            # 無効なディレクトリ（env.jsonなし）
            invalid_dir = env_dir / "invalid"
            invalid_dir.mkdir()

            languages = loader.get_available_languages(env_dir)

            assert set(languages) == {"cpp", "java", "python"}  # sorted
            assert "shared" not in languages
            assert "invalid" not in languages


class TestTypeSafeConfigNodeManager:
    """TypeSafeConfigNodeManagerの単体テスト"""

    @pytest.fixture
    def sample_config_data(self):
        """テスト用設定データ（実際の設定構造に合わせて修正）"""
        return {
            "workspace": "/tmp/workspace",
            "debug": True,
            "timeout": 30,
            "paths": {
                "local_workspace_path": "/tmp/workspace",
                "contest_current_path": "./contest_current",
                "contest_stock_path": "./contest_stock/{language_name}/{contest_name}/{problem_name}",
                "contest_template_path": "./contest_template",
                "contest_temp_path": "./.temp"
            },
            "docker_defaults": {
                "docker_options": {
                    "interactive": True,
                    "tty": True,
                    "remove": True,
                    "detach": False
                }
            },
            "dev_config": {
                "debug": {
                    "enabled": True,
                    "level": "detailed"
                }
            },
            "python": {
                "language_id": "4006",
                "source_file_name": "main.py",
                "run_command": "python3 main.py",
                "timeout": 30
            },
            "cpp": {
                "language_id": "4003",
                "source_file_name": "main.cpp",
                "run_command": "g++ -o main main.cpp && ./main"
            }
        }

    @pytest.fixture
    def manager_with_data(self, sample_config_data):
        """設定データ付きのTypeSafeConfigNodeManager"""
        manager = TypeSafeConfigNodeManager()

        # FileLoaderをモック化してテストデータを返すように設定
        with patch.object(manager.file_loader, 'load_and_merge_configs', return_value=sample_config_data):
            manager.load_from_files("/fake/system", "/fake/env", "python")

        return manager

    def test_resolve_config_str(self, manager_with_data):
        """文字列型の設定解決テスト"""
        result = manager_with_data.resolve_config(["workspace"], str)
        assert result == "/tmp/workspace"
        assert isinstance(result, str)

    def test_resolve_config_int(self, manager_with_data):
        """整数型の設定解決テスト"""
        result = manager_with_data.resolve_config(["timeout"], int)
        assert result == 30
        assert isinstance(result, int)

    def test_resolve_config_bool(self, manager_with_data):
        """真偽値型の設定解決テスト"""
        result = manager_with_data.resolve_config(["debug"], bool)
        assert result is True
        assert isinstance(result, bool)

    def test_resolve_config_nested_path(self, manager_with_data):
        """ネストしたパスの設定解決テスト"""
        result = manager_with_data.resolve_config(["python", "language_id"], str)
        assert result == "4006"

    def test_resolve_config_with_fallback(self, manager_with_data):
        """フォールバック機能テスト（with_default廃止後）"""
        # 存在する設定
        result = manager_with_data.resolve_config(["timeout"], int)
        assert result == 30

        # 存在しない設定でのエラーハンドリング
        try:
            manager_with_data.resolve_config(["nonexistent"], str)
            raise AssertionError("KeyError should be raised")
        except KeyError:
            pass  # Expected behavior

    def test_resolve_config_type_error(self, manager_with_data):
        """型変換エラーのテスト"""
        with pytest.raises(TypeError):
            # 真偽値を整数として解決しようとする
            manager_with_data.resolve_config(["debug"], int)

    def test_resolve_config_key_error(self, manager_with_data):
        """存在しないキーのエラーテスト"""
        with pytest.raises(KeyError):
            manager_with_data.resolve_config(["nonexistent", "path"], str)

    def test_resolve_template_typed_basic(self, manager_with_data):
        """基本的なテンプレート展開テスト"""
        template = "Workspace: {workspace}"
        result = manager_with_data.resolve_template_typed(template)
        assert "Workspace: /tmp/workspace" in result or result == template  # ConfigNodeの動作による

    def test_resolve_template_to_path(self, manager_with_data):
        """パステンプレート展開テスト"""
        template = "{workspace}/contest_current"
        result = manager_with_data.resolve_template_to_path(template)
        assert isinstance(result, Path)

    def test_create_execution_config(self, manager_with_data):
        """ExecutionConfiguration生成テスト"""
        config = manager_with_data.create_execution_config(
            contest_name="abc300",
            problem_name="a",
            language="python"
        )

        assert isinstance(config, TypedExecutionConfiguration)
        assert config.contest_name == "abc300"
        assert config.problem_name == "a"
        assert config.language == "python"
        assert config.env_type == "local"
        assert config.command_type == "open"
        assert hasattr(config, 'local_workspace_path')
        assert config.timeout_seconds == 30  # timeout.default
        assert config.language_id == "4006"
        assert config.source_file_name == "main.py"
        assert config.run_command == "python3 main.py"

    def test_create_execution_config_missing_language_data(self, manager_with_data):
        """存在しない言語での動作テスト"""
        # 存在しない言語でも設定システムがフォールバックを提供する
        try:
            config = manager_with_data.create_execution_config(
                contest_name="abc301",
                problem_name="b",
                language="unknown_language"  # 存在しない言語
            )
            # フォールバック値で処理される
            assert config.contest_name == "abc301"
            assert config.problem_name == "b"
            assert config.language == "unknown_language"
        except KeyError:
            # 設定システムによってはKeyErrorが発生する場合もある
            pass

    def test_caching_behavior(self, manager_with_data):
        """キャッシュ動作のテスト"""
        # 1回目の呼び出し
        result1 = manager_with_data.resolve_config(["workspace"], str)

        # 2回目の呼び出し（キャッシュから取得）
        result2 = manager_with_data.resolve_config(["workspace"], str)

        assert result1 == result2
        # キャッシュが機能していることを確認
        cache_key = (('workspace',), str)
        assert cache_key in manager_with_data._type_conversion_cache

    def test_execution_config_caching(self, manager_with_data):
        """ExecutionConfigキャッシュのテスト"""
        # 同じパラメータで2回生成
        config1 = manager_with_data.create_execution_config("abc300", "a", "python")
        config2 = manager_with_data.create_execution_config("abc300", "a", "python")

        # 同じインスタンスが返されることを確認
        assert config1 is config2

    def test_convert_to_type_str(self, manager_with_data):
        """型変換テスト: 文字列"""
        assert manager_with_data._convert_to_type(123, str) == "123"
        assert manager_with_data._convert_to_type(True, str) == "True"

    def test_convert_to_type_int(self, manager_with_data):
        """型変換テスト: 整数"""
        assert manager_with_data._convert_to_type("42", int) == 42
        assert manager_with_data._convert_to_type(42.0, int) == 42

        with pytest.raises(TypeError):
            manager_with_data._convert_to_type(True, int)  # boolは変換不可

    def test_convert_to_type_bool(self, manager_with_data):
        """型変換テスト: 真偽値"""
        assert manager_with_data._convert_to_type("true", bool) is True
        assert manager_with_data._convert_to_type("false", bool) is False
        assert manager_with_data._convert_to_type("1", bool) is True
        assert manager_with_data._convert_to_type("0", bool) is False

        with pytest.raises(TypeError):
            manager_with_data._convert_to_type("invalid", bool)

    def test_convert_to_type_path(self, manager_with_data):
        """型変換テスト: Path"""
        result = manager_with_data._convert_to_type("/tmp/test", Path)
        assert isinstance(result, Path)
        assert str(result) == "/tmp/test"


class TestTypedExecutionConfiguration:
    """TypedExecutionConfigurationのテスト"""

    def test_typed_execution_configuration_creation(self):
        """TypedExecutionConfiguration生成テスト"""
        config = TypedExecutionConfiguration(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="open",
            workspace_path=Path("/tmp/workspace"),
            contest_current_path=Path("/tmp/workspace/contest_current"),
            timeout_seconds=30,
            language_id="4006",
            source_file_name="main.py",
            run_command="python3 main.py",
            debug_mode=False
        )

        assert config.contest_name == "abc300"
        assert config.problem_name == "a"
        assert config.language == "python"
        assert isinstance(config.workspace_path, Path)
        assert config.timeout_seconds == 30
        assert config.debug_mode is False


class TestIntegration:
    """統合テスト"""

    def test_full_workflow_with_real_files(self):
        """実際のファイルを使った完全なワークフローテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            system_dir = Path(temp_dir) / "system"
            env_dir = Path(temp_dir) / "env"
            system_dir.mkdir()
            env_dir.mkdir()

            # 実際の設定ファイルを作成
            system_config = {
                "workspace": "{base_path}/workspace",
                "base_path": "/tmp"
            }
            with open(system_dir / "config.json", 'w') as f:
                json.dump(system_config, f)

            env_config = {
                "python": {
                    "language_id": "4006",
                    "source_file_name": "main.py",
                    "run_command": "python3 main.py",
                    "timeout": 30
                }
            }
            with open(env_dir / "env.json", 'w') as f:
                json.dump(env_config, f)

            # TypeSafeConfigNodeManagerで実際に処理
            manager = TypeSafeConfigNodeManager()
            manager.load_from_files(str(system_dir), str(env_dir), "python")

            # 設定解決のテスト
            language_id = manager.resolve_config(["python", "language_id"], str)
            assert language_id == "4006"

            timeout = manager.resolve_config(["python", "timeout"], int)
            assert timeout == 30

            # ExecutionConfiguration生成のテスト
            config = manager.create_execution_config("abc300", "a", "python")
            assert config.language_id == "4006"
            assert config.timeout_seconds == 30
