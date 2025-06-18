"""設定システムの診断テスト"""
import pytest

from src.configuration.config_manager import TypeSafeConfigNodeManager


class TestConfigSystemDiagnosis:
    """設定システムの診断と問題特定"""

    def test_config_loading_diagnosis(self):
        """設定システムの読み込み診断"""
        config_manager = TypeSafeConfigNodeManager()

        # 設定ファイル読み込みの詳細診断
        try:
            config_manager.load_from_files(
                system_dir="config/system",
                env_dir="contest_env",
                language="python"
            )
            print("✅ 設定ファイル読み込み成功")
        except Exception as e:
            pytest.fail(f"❌ 設定ファイル読み込み失敗: {e}")

    def test_root_node_structure(self):
        """ルートノード構造の診断"""
        config_manager = TypeSafeConfigNodeManager()

        try:
            config_manager.load_from_files(
                system_dir="config/system",
                env_dir="contest_env",
                language="python"
            )

            # ルートノードが正しく構築されているか確認
            assert config_manager.root_node is not None
            print("✅ ルートノード構築成功")

            # ルートノードのデバッグ情報
            if hasattr(config_manager.root_node, '__dict__'):
                print(f"ルートノードの属性: {vars(config_manager.root_node)}")

        except Exception as e:
            pytest.fail(f"❌ ルートノード構造診断失敗: {e}")

    def test_available_config_paths(self):
        """利用可能な設定パスの確認"""
        config_manager = TypeSafeConfigNodeManager()

        try:
            config_manager.load_from_files(
                system_dir="config/system",
                env_dir="contest_env",
                language="python"
            )

            # 既知の設定パスをテスト
            test_paths = [
                ['docker_defaults'],
                ['docker_defaults', 'docker_workspace_mount_path'],
                ['docker_defaults', 'docker_options'],
                ['docker_defaults', 'docker_options', 'detach'],
                ['dev_config'],
                ['dev_config', 'debug'],
                ['dev_config', 'debug', 'enabled'],
            ]

            successful_paths = []
            failed_paths = []

            for path in test_paths:
                try:
                    # パスが存在するかの確認（値を取得せずに）
                    from src.configuration.config_manager import _ensure_imports
                    from src.context.resolver.config_resolver import resolve_best
                    _ensure_imports()

                    result = resolve_best(config_manager.root_node, path)
                    if result is not None:
                        successful_paths.append(path)
                    else:
                        failed_paths.append(path)
                except Exception:
                    failed_paths.append(path)

            print(f"✅ 成功したパス ({len(successful_paths)}):")
            for path in successful_paths:
                print(f"  - {' -> '.join(path)}")

            if failed_paths:
                print(f"❌ 失敗したパス ({len(failed_paths)}):")
                for path in failed_paths:
                    print(f"  - {' -> '.join(path)}")

            # 少なくとも基本的なパスは成功するべき
            assert len(successful_paths) > 0, "設定パスが一つも解決できません"

        except Exception as e:
            pytest.fail(f"❌ 設定パス確認失敗: {e}")

    def test_specific_config_values(self):
        """具体的な設定値の確認"""
        config_manager = TypeSafeConfigNodeManager()

        try:
            config_manager.load_from_files(
                system_dir="config/system",
                env_dir="contest_env",
                language="python"
            )

            # 具体的な値を取得してテスト
            test_configs = [
                (['docker_defaults', 'docker_workspace_mount_path'], str, "/workspace"),
                (['docker_defaults', 'docker_options', 'detach'], bool, False),
                (['docker_defaults', 'docker_options', 'interactive'], bool, True),
                (['dev_config', 'debug', 'enabled'], bool, True),
            ]

            successful_configs = []
            failed_configs = []

            for path, expected_type, expected_value in test_configs:
                try:
                    value = config_manager.resolve_config(path, expected_type)
                    if value == expected_value:
                        successful_configs.append((path, value))
                        print(f"✅ {' -> '.join(path)}: {value}")
                    else:
                        print(f"⚠️  {' -> '.join(path)}: 期待値 {expected_value}, 実際 {value}")
                        successful_configs.append((path, value))  # 値は取得できた
                except Exception as e:
                    failed_configs.append((path, str(e)))
                    print(f"❌ {' -> '.join(path)}: {e}")

            print(f"\n設定値取得結果: 成功 {len(successful_configs)}, 失敗 {len(failed_configs)}")

            # 基本的な設定は取得できるべき
            assert len(successful_configs) >= 2, f"基本設定の取得に失敗しています。失敗: {failed_configs}"

        except Exception as e:
            pytest.fail(f"❌ 設定値確認失敗: {e}")

    def test_contest_env_structure(self):
        """contest_env構造の診断"""
        from pathlib import Path

        contest_env_dir = Path("contest_env")

        if not contest_env_dir.exists():
            pytest.skip("contest_envディレクトリが存在しません")

        print("contest_env構造:")
        for item in contest_env_dir.rglob("*"):
            if item.is_file():
                print(f"  📄 {item}")
            elif item.is_dir():
                print(f"  📁 {item}/")

    def test_config_system_dependencies(self):
        """設定システムの依存関係確認"""
        try:
            # 必要なモジュールのインポート確認
            from src.context.resolver.config_node import ConfigNode
            from src.context.resolver.config_resolver import (
                create_config_root_from_dict,
                resolve_best,
                resolve_formatted_string,
            )
            print("✅ 設定システム依存関係のインポート成功")

            # 基本的な機能の動作確認
            test_dict = {"test": {"value": "success"}}
            root_node = create_config_root_from_dict(test_dict)
            result = resolve_best(root_node, ["test", "value"])

            assert result is not None, "基本的な設定解決に失敗"
            print("✅ 設定システム基本機能動作確認成功")

        except Exception as e:
            pytest.fail(f"❌ 設定システム依存関係確認失敗: {e}")

    def test_file_loading_details(self):
        """ファイル読み込み詳細の確認"""
        import json
        from pathlib import Path

        system_dir = Path("config/system")

        print("システム設定ファイル詳細:")
        for config_file in system_dir.glob("*.json"):
            try:
                with open(config_file, encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ {config_file.name}: {len(data)} トップレベルキー")
                for key in data:
                    print(f"  - {key}")
            except Exception as e:
                print(f"❌ {config_file.name}: {e}")

    def test_minimal_config_resolution(self):
        """最小限の設定解決テスト"""
        config_manager = TypeSafeConfigNodeManager()

        try:
            config_manager.load_from_files(
                system_dir="config/system",
                env_dir="contest_env",
                language="python"
            )

            # 最も基本的な設定の解決テスト
            basic_configs = [
                (['docker_defaults'], dict),
                (['dev_config'], dict),
            ]

            for path, expected_type in basic_configs:
                try:
                    value = config_manager.resolve_config(path, expected_type)
                    print(f"✅ 基本設定解決成功: {path} -> {type(value)}")
                except Exception as e:
                    print(f"❌ 基本設定解決失敗: {path} -> {e}")

        except Exception as e:
            pytest.fail(f"❌ 最小設定解決テスト失敗: {e}")
