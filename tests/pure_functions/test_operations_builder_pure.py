"""
純粋関数ベースのoperations構築のテスト
モック不要で実際の動作をテスト
"""
import pytest
from pathlib import Path
from src.pure_functions.operations_builder_pure import (
    OperationsConfig,
    OperationsRegistry,
    create_operations_config_pure,
    build_operations_registry_pure,
    create_driver_factory_pure,
    validate_operations_config_pure,
    get_operations_dependencies_pure,
    build_operations_from_config_pure
)


class TestOperationsConfig:
    """Operations設定のテスト"""
    
    def test_create_default_config(self):
        """デフォルト設定のテスト"""
        config = create_operations_config_pure()
        
        assert config.use_mock is False
        assert config.base_dir == Path('.')
        assert config.shell_driver_type == "local"
        assert config.docker_driver_type == "local"
        assert config.file_driver_type == "local"
    
    def test_create_mock_config(self):
        """モック設定のテスト"""
        config = create_operations_config_pure(use_mock=True)
        
        assert config.use_mock is True
        assert config.shell_driver_type == "mock"
        assert config.docker_driver_type == "mock"
        assert config.file_driver_type == "mock"
    
    def test_create_custom_base_dir(self):
        """カスタムベースディレクトリのテスト"""
        custom_dir = Path("/custom/path")
        config = create_operations_config_pure(base_dir=custom_dir)
        
        assert config.base_dir == custom_dir
    
    def test_config_is_immutable(self):
        """設定の不変性テスト"""
        config = create_operations_config_pure()
        
        with pytest.raises(AttributeError):
            config.use_mock = True


class TestOperationsRegistry:
    """Operations登録情報のテスト"""
    
    def test_build_local_registry(self):
        """ローカルレジストリ構築のテスト"""
        config = create_operations_config_pure(use_mock=False)
        registry = build_operations_registry_pure(config)
        
        assert isinstance(registry, OperationsRegistry)
        assert "shell_driver" in registry.drivers
        assert "docker_driver" in registry.drivers
        assert "file_driver" in registry.drivers
        
        # ローカルドライバーが設定されていることを確認
        assert "local_shell_driver" in registry.drivers["shell_driver"]
        assert "local_file_driver" in registry.drivers["file_driver"]
    
    def test_build_mock_registry(self):
        """モックレジストリ構築のテスト"""
        config = create_operations_config_pure(use_mock=True)
        registry = build_operations_registry_pure(config)
        
        # モックドライバーが設定されていることを確認
        assert "mock_shell_driver" in registry.drivers["shell_driver"]
        assert "mock_docker_driver" in registry.drivers["docker_driver"]
        assert "mock_file_driver" in registry.drivers["file_driver"]
    
    def test_registry_factories(self):
        """ファクトリー設定のテスト"""
        config = create_operations_config_pure()
        registry = build_operations_registry_pure(config)
        
        # 全てのファクトリーがNoneに設定されていることを確認
        expected_factories = [
            'UnifiedCommandRequestFactory',
            'ShellCommandRequestFactory',
            'DockerCommandRequestFactory',
            'CopyCommandRequestFactory',
            'OjCommandRequestFactory',
            'RemoveCommandRequestFactory',
            'BuildCommandRequestFactory',
            'PythonCommandRequestFactory',
            'MkdirCommandRequestFactory',
            'TouchCommandRequestFactory',
            'RmtreeCommandRequestFactory',
            'MoveCommandRequestFactory',
            'MoveTreeCommandRequestFactory'
        ]
        
        for factory_name in expected_factories:
            assert factory_name in registry.factories
            assert registry.factories[factory_name] is None
    
    def test_registry_classes(self):
        """クラス設定のテスト"""
        config = create_operations_config_pure()
        registry = build_operations_registry_pure(config)
        
        assert "DockerRequest" in registry.classes
        assert "DockerOpType" in registry.classes
        assert "docker_request" in registry.classes["DockerRequest"]
    
    def test_registry_is_immutable(self):
        """レジストリの不変性テスト"""
        config = create_operations_config_pure()
        registry = build_operations_registry_pure(config)
        
        # dataclassのfrozenフィールドは辞書の中身は変更可能
        # 代わりにdataclass自体の属性変更を試す
        with pytest.raises(AttributeError):
            registry.drivers = {}


class TestDriverFactory:
    """ドライバーファクトリーのテスト"""
    
    def test_create_shell_driver_factory(self):
        """シェルドライバーファクトリーのテスト"""
        config = create_operations_config_pure(use_mock=True)
        driver_path = "src.operations.mock.mock_shell_driver.MockShellDriver"
        
        factory = create_driver_factory_pure(driver_path, config)
        
        # ファクトリーが関数であることを確認
        assert callable(factory)
        
        # ドライバーインスタンスを作成
        driver = factory()
        
        # 正しいタイプのドライバーが作成されることを確認
        assert driver.__class__.__name__ == "MockShellDriver"
    
    def test_create_file_driver_factory_with_base_dir(self):
        """ベースディレクトリ付きファイルドライバーファクトリーのテスト"""
        custom_dir = Path("/test/path")
        config = create_operations_config_pure(base_dir=custom_dir)
        driver_path = "src.operations.mock.mock_file_driver.MockFileDriver"
        
        factory = create_driver_factory_pure(driver_path, config)
        driver = factory()
        
        # ベースディレクトリが正しく設定されることを確認
        assert driver.base_dir == custom_dir


class TestConfigValidation:
    """設定検証のテスト"""
    
    def test_valid_config(self):
        """有効な設定のテスト"""
        config = create_operations_config_pure()
        errors = validate_operations_config_pure(config)
        
        assert errors == []
    
    def test_invalid_driver_type(self):
        """無効なドライバータイプのテスト"""
        # 無効な設定を直接作成（通常のAPIでは作成できない）
        config = OperationsConfig(
            use_mock=False,
            base_dir=Path('.'),
            shell_driver_type="invalid",
            docker_driver_type="invalid",
            file_driver_type="invalid"
        )
        
        errors = validate_operations_config_pure(config)
        
        assert len(errors) == 3
        assert "Invalid shell_driver_type" in errors[0]
        assert "Invalid docker_driver_type" in errors[1] 
        assert "Invalid file_driver_type" in errors[2]
    
    def test_invalid_base_dir_type(self):
        """無効なベースディレクトリタイプのテスト"""
        config = OperationsConfig(
            use_mock=False,
            base_dir="/invalid/string/path",  # Pathオブジェクトではない
            shell_driver_type="local",
            docker_driver_type="local", 
            file_driver_type="local"
        )
        
        errors = validate_operations_config_pure(config)
        
        assert len(errors) == 1
        assert "base_dir must be a Path object" in errors[0]


class TestDependencyAnalysis:
    """依存関係分析のテスト"""
    
    def test_get_dependencies(self):
        """依存関係取得のテスト"""
        config = create_operations_config_pure()
        registry = build_operations_registry_pure(config)
        
        dependencies = get_operations_dependencies_pure(registry)
        
        # 各ドライバーの依存関係が取得されることを確認
        assert "shell_driver" in dependencies
        assert "docker_driver" in dependencies
        assert "file_driver" in dependencies
        assert "DockerRequest" in dependencies
        assert "DockerOpType" in dependencies
        
        # 依存関係が正しいモジュールパスを含むことを確認
        shell_deps = dependencies["shell_driver"]
        assert len(shell_deps) == 1
        assert "operations.shell" in shell_deps[0]


class TestOperationsBuild:
    """Operations構築の統合テスト"""
    
    def test_build_local_operations(self):
        """ローカルOperations構築のテスト"""
        config = create_operations_config_pure(use_mock=False)
        operations = build_operations_from_config_pure(config)
        
        # DIContainerが返されることを確認
        from src.operations.di_container import DIContainer
        assert isinstance(operations, DIContainer)
        
        # 必要なドライバーが登録されていることを確認
        assert operations.resolve('shell_driver') is not None
        assert operations.resolve('docker_driver') is not None
        assert operations.resolve('file_driver') is not None
    
    def test_build_mock_operations(self):
        """モックOperations構築のテスト"""
        config = create_operations_config_pure(use_mock=True)
        operations = build_operations_from_config_pure(config)
        
        # モックドライバーが登録されていることを確認
        shell_driver = operations.resolve('shell_driver')
        assert shell_driver.__class__.__name__ == "MockShellDriver"
        
        docker_driver = operations.resolve('docker_driver')
        assert docker_driver.__class__.__name__ == "MockDockerDriver"
        
        file_driver = operations.resolve('file_driver')
        assert file_driver.__class__.__name__ == "MockFileDriver"
    
    def test_build_with_invalid_config(self):
        """無効な設定でのOperations構築のテスト"""
        # 無効な設定を作成
        config = OperationsConfig(
            use_mock=False,
            base_dir=Path('.'),
            shell_driver_type="invalid",
            docker_driver_type="local",
            file_driver_type="local"
        )
        
        with pytest.raises(ValueError) as exc_info:
            build_operations_from_config_pure(config)
        
        assert "Invalid operations config" in str(exc_info.value)


class TestRealDriverCreation:
    """実際のドライバー作成のテスト"""
    
    def test_real_mock_drivers_creation(self):
        """実際のモックドライバー作成のテスト"""
        config = create_operations_config_pure(use_mock=True)
        registry = build_operations_registry_pure(config)
        
        # 各ドライバーファクトリーを実際に実行
        for driver_name, driver_path in registry.drivers.items():
            factory = create_driver_factory_pure(driver_path, config)
            driver = factory()
            
            # ドライバーが正常に作成されることを確認
            assert driver is not None
            assert hasattr(driver, '__class__')
            
            # ファイルドライバーの場合、base_dirが設定されることを確認
            if "file_driver" in driver_name:
                assert hasattr(driver, 'base_dir')
                assert driver.base_dir == config.base_dir


class TestPureFunctionProperties:
    """純粋関数の特性テスト"""
    
    def test_deterministic_behavior(self):
        """決定論的動作のテスト"""
        config_input = {"use_mock": True, "base_dir": Path("/test")}
        
        # 同じ入力に対して常に同じ出力を返すことを確認
        config1 = create_operations_config_pure(**config_input)
        config2 = create_operations_config_pure(**config_input)
        
        assert config1 == config2
        
        registry1 = build_operations_registry_pure(config1)
        registry2 = build_operations_registry_pure(config2)
        
        assert registry1 == registry2
    
    def test_no_side_effects(self):
        """副作用なしのテスト"""
        original_config = create_operations_config_pure()
        
        # 関数を実行
        registry = build_operations_registry_pure(original_config)
        dependencies = get_operations_dependencies_pure(registry)
        
        # 元の設定が変更されていないことを確認
        new_config = create_operations_config_pure()
        assert original_config == new_config
        
        # 複数回実行しても同じ結果が得られることを確認
        registry2 = build_operations_registry_pure(original_config)
        dependencies2 = get_operations_dependencies_pure(registry2)
        
        assert registry == registry2
        assert dependencies == dependencies2