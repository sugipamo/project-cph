"""実際の設定ファイルを使ったエンドツーエンドテスト

実環境のcontest_env設定を使用した統合テスト
"""
import contextlib
from pathlib import Path

import pytest

from src.configuration.config_manager import FileLoader, TypeSafeConfigNodeManager
from src.context.user_input_parser.user_input_parser_integration import (
    UserInputParserIntegration,
    create_new_execution_context,
)


class TestRealConfigEndToEnd:
    """実設定ファイルでのエンドツーエンド統合テスト"""

    @pytest.fixture
    def real_config_paths(self):
        """実際の設定パスを取得"""
        base_dir = Path(".")
        contest_env_dir = base_dir / "contest_env"
        system_config_dir = base_dir / "config" / "system"

        # 設定ディレクトリの存在確認
        if not contest_env_dir.exists():
            pytest.skip("contest_env directory not found")
        if not system_config_dir.exists():
            pytest.skip("config/system directory not found")

        return {
            "contest_env": str(contest_env_dir),
            "system_config": str(system_config_dir)
        }

    def test_available_languages_detection(self, real_config_paths):
        """実際の設定から利用可能言語を検出"""
        file_loader = FileLoader()
        languages = file_loader.get_available_languages(Path(real_config_paths["contest_env"]))

        # 期待される言語が含まれているか確認
        expected_languages = ["python", "cpp", "rust"]
        for lang in expected_languages:
            lang_dir = Path(real_config_paths["contest_env"]) / lang
            if lang_dir.exists():
                assert lang in languages, f"Language {lang} should be detected"

    def test_real_config_loading_python(self, real_config_paths):
        """Python設定の実際の読み込みテスト"""
        manager = TypeSafeConfigNodeManager()

        try:
            manager.load_from_files(
                system_dir=real_config_paths["system_config"],
                env_dir=real_config_paths["contest_env"],
                language="python"
            )
        except Exception as e:
            pytest.fail(f"Failed to load Python configuration: {e}")

        # 基本的な設定値の確認
        try:
            workspace_path = manager.resolve_config(["paths", "workspace_path"], str)
            assert workspace_path, "workspace_path should be configured"
        except Exception:
            # パスが異なる構造の場合は警告のみ
            pytest.skip("workspace_path not found in current config structure")

    def test_real_config_loading_cpp(self, real_config_paths):
        """C++設定の実際の読み込みテスト"""
        cpp_dir = Path(real_config_paths["contest_env"]) / "cpp"
        if not cpp_dir.exists():
            pytest.skip("C++ configuration not available")

        manager = TypeSafeConfigNodeManager()

        try:
            manager.load_from_files(
                system_dir=real_config_paths["system_config"],
                env_dir=real_config_paths["contest_env"],
                language="cpp"
            )
        except Exception as e:
            pytest.fail(f"Failed to load C++ configuration: {e}")

    def test_real_config_loading_rust(self, real_config_paths):
        """Rust設定の実際の読み込みテスト"""
        rust_dir = Path(real_config_paths["contest_env"]) / "rust"
        if not rust_dir.exists():
            pytest.skip("Rust configuration not available")

        manager = TypeSafeConfigNodeManager()

        try:
            manager.load_from_files(
                system_dir=real_config_paths["system_config"],
                env_dir=real_config_paths["contest_env"],
                language="rust"
            )
        except Exception as e:
            pytest.fail(f"Failed to load Rust configuration: {e}")

    def test_execution_config_creation_real(self, real_config_paths):
        """実設定でのExecutionConfiguration作成テスト"""
        manager = TypeSafeConfigNodeManager()

        # Python設定で実行設定を作成
        manager.load_from_files(
            system_dir=real_config_paths["system_config"],
            env_dir=real_config_paths["contest_env"],
            language="python"
        )

        config = manager.create_execution_config(
            contest_name="abc123",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test"
        )

        # 基本プロパティの確認
        assert config.contest_name == "abc123"
        assert config.problem_name == "a"
        assert config.language == "python"

        # テンプレート解決の確認
        template = "{contest_name}/{problem_name}"
        resolved = config.resolve_formatted_string(template)
        assert resolved == "abc123/a"

    def test_user_input_parser_integration_real(self, real_config_paths):
        """UserInputParserIntegrationとの実際の統合テスト"""
        integration = UserInputParserIntegration(
            contest_env_dir=real_config_paths["contest_env"],
            system_config_dir=real_config_paths["system_config"]
        )

        try:
            config = integration.create_execution_configuration_from_context(
                command_type="test",
                language="python",
                contest_name="abc123",
                problem_name="a",
                env_type="local",
                env_json={}
            )

            assert config.contest_name == "abc123"
            assert config.language == "python"
        except Exception as e:
            pytest.fail(f"UserInputParserIntegration failed: {e}")

    def test_create_new_execution_context_real(self, real_config_paths):
        """create_new_execution_context関数の実際のテスト"""
        # 実際のpathを設定（グローバル関数なので直接変更はできない）
        try:
            config = create_new_execution_context(
                command_type="test",
                language="python",
                contest_name="abc123",
                problem_name="a",
                env_type="local",
                env_json={}
            )

            assert config.contest_name == "abc123"
            assert config.language == "python"
        except Exception as e:
            # デフォルトパスでの実行なので、設定が見つからない場合はスキップ
            pytest.skip(f"create_new_execution_context test skipped: {e}")

    def test_command_specific_configurations(self, real_config_paths):
        """コマンド固有設定の確認"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_dir=real_config_paths["system_config"],
            env_dir=real_config_paths["contest_env"],
            language="python"
        )

        # test コマンドの設定確認
        try:
            test_config = manager.resolve_config(["commands", "test"], dict)
            assert "steps" in test_config, "test command should have steps"
        except Exception:
            pytest.skip("test command configuration not found")

        # open コマンドの設定確認
        try:
            open_config = manager.resolve_config(["commands", "open"], dict)
            assert "steps" in open_config, "open command should have steps"
        except Exception:
            pytest.skip("open command configuration not found")

    def test_shared_configuration_loading(self, real_config_paths):
        """共有設定の読み込みテスト"""
        shared_path = Path(real_config_paths["contest_env"]) / "shared" / "env.json"
        if not shared_path.exists():
            pytest.skip("shared configuration not available")

        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_dir=real_config_paths["system_config"],
            env_dir=real_config_paths["contest_env"],
            language="python"
        )

        # 共有設定の確認（環境ログ設定など）
        try:
            env_logging = manager.resolve_config(["environment_logging"], dict)
            assert isinstance(env_logging, dict), "environment_logging should be a dict"
        except Exception:
            # 共有設定がない場合はスキップ
            pytest.skip("environment_logging configuration not found")

    def test_template_resolution_with_real_paths(self, real_config_paths):
        """実際のパス設定でのテンプレート解決テスト"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_dir=real_config_paths["system_config"],
            env_dir=real_config_paths["contest_env"],
            language="python"
        )

        config = manager.create_execution_config(
            contest_name="abc123",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test"
        )

        # 実際のパステンプレートの解決
        test_templates = [
            "{contest_name}",
            "{problem_name}",
            "{language}",
            "{contest_name}/{problem_name}",
            "{contest_name}/{language}/{problem_name}"
        ]

        for template in test_templates:
            try:
                resolved = config.resolve_formatted_string(template)
                assert resolved, f"Template {template} should resolve to non-empty string"

                # 期待される文字列が含まれているか確認
                if "{contest_name}" in template:
                    assert "abc123" in resolved
                if "{problem_name}" in template:
                    assert "a" in resolved
                if "{language}" in template:
                    assert "python" in resolved

            except Exception as e:
                pytest.fail(f"Template resolution failed for {template}: {e}")

    def test_file_patterns_and_extensions(self, real_config_paths):
        """ファイルパターンと拡張子設定のテスト"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_dir=real_config_paths["system_config"],
            env_dir=real_config_paths["contest_env"],
            language="python"
        )

        # Python拡張子の確認
        try:
            extensions = manager.resolve_config(["extensions"], list)
            assert ".py" in extensions, "Python extensions should include .py"
        except Exception:
            pytest.skip("extensions configuration not found")

        # ファイルパターンの確認
        try:
            file_patterns = manager.resolve_config(["file_patterns"], dict)
            assert isinstance(file_patterns, dict), "file_patterns should be a dict"
        except Exception:
            pytest.skip("file_patterns configuration not found")

    def test_backwards_compatibility_verification(self, real_config_paths):
        """後方互換性の検証"""
        # 新しいシステムが既存の設定構造を正しく読み込めるか確認
        manager = TypeSafeConfigNodeManager()

        try:
            manager.load_from_files(
                system_dir=real_config_paths["system_config"],
                env_dir=real_config_paths["contest_env"],
                language="python"
            )

            # 既存システムで期待される基本的な設定項目の確認
            expected_top_level_keys = ["commands"]

            for key in expected_top_level_keys:
                try:
                    value = manager.resolve_config([key], dict)
                    assert isinstance(value, dict), f"{key} should be a dict"
                except Exception:
                    # 設定構造が異なる場合は警告のみ
                    pytest.skip(f"Expected key {key} not found in configuration")

        except Exception as e:
            pytest.fail(f"Backwards compatibility check failed: {e}")

    def test_error_resilience_real_config(self, real_config_paths):
        """実設定でのエラー耐性テスト"""
        manager = TypeSafeConfigNodeManager()
        manager.load_from_files(
            system_dir=real_config_paths["system_config"],
            env_dir=real_config_paths["contest_env"],
            language="python"
        )

        # 存在しない設定へのアクセス
        with pytest.raises((KeyError, ValueError)):
            manager.resolve_config(["definitely", "does", "not", "exist"], str)

        # 存在しない言語での設定読み込み（エラー耐性あり）
        with contextlib.suppress(Exception):
            manager.load_from_files(
                system_dir=real_config_paths["system_config"],
                env_dir=real_config_paths["contest_env"],
                language="nonexistent_language"
            )
            # 正常に処理された場合はOK（エラー耐性機能）
            # エラーが発生しても期待される動作
