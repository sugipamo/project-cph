"""
純粋関数ベースのoperations構築
DIコンテナの構築を純粋関数として実装
"""
from dataclasses import dataclass
from typing import Dict, Any, Callable, Optional
from pathlib import Path


@dataclass(frozen=True)
class OperationsConfig:
    """Operations構築設定の不変データクラス"""
    use_mock: bool = False
    base_dir: Optional[Path] = None
    shell_driver_type: str = "local"
    docker_driver_type: str = "local"
    file_driver_type: str = "local"


@dataclass(frozen=True)
class OperationsRegistry:
    """Operations登録情報の不変データクラス"""
    drivers: Dict[str, str]
    factories: Dict[str, Optional[str]]
    classes: Dict[str, str]


def create_operations_config_pure(
    use_mock: bool = False,
    base_dir: Optional[Path] = None
) -> OperationsConfig:
    """
    Operations設定を作成する純粋関数
    
    Args:
        use_mock: モックドライバーを使用するか
        base_dir: ファイルドライバーのベースディレクトリ
        
    Returns:
        OperationsConfig: 構築設定
    """
    return OperationsConfig(
        use_mock=use_mock,
        base_dir=base_dir or Path('.'),
        shell_driver_type="mock" if use_mock else "local",
        docker_driver_type="mock" if use_mock else "local", 
        file_driver_type="mock" if use_mock else "local"
    )


def build_operations_registry_pure(config: OperationsConfig) -> OperationsRegistry:
    """
    Operations登録情報を構築する純粋関数
    
    Args:
        config: Operations構築設定
        
    Returns:
        OperationsRegistry: 登録情報
    """
    # ドライバー設定
    if config.use_mock:
        drivers = {
            'shell_driver': 'src.operations.mock.mock_shell_driver.MockShellDriver',
            'docker_driver': 'src.operations.mock.mock_docker_driver.MockDockerDriver',
            'file_driver': 'src.operations.mock.mock_file_driver.MockFileDriver'
        }
    else:
        drivers = {
            'shell_driver': 'src.operations.shell.local_shell_driver.LocalShellDriver',
            'docker_driver': 'src.operations.docker.docker_driver.LocalDockerDriver',
            'file_driver': 'src.operations.file.local_file_driver.LocalFileDriver'
        }
    
    # ファクトリー設定（現在はNone、将来の実装用）
    factories = {
        'UnifiedCommandRequestFactory': None,
        'ShellCommandRequestFactory': None,
        'DockerCommandRequestFactory': None,
        'CopyCommandRequestFactory': None,
        'OjCommandRequestFactory': None,
        'RemoveCommandRequestFactory': None,
        'BuildCommandRequestFactory': None,
        'PythonCommandRequestFactory': None,
        'MkdirCommandRequestFactory': None,
        'TouchCommandRequestFactory': None,
        'RmtreeCommandRequestFactory': None,
        'MoveCommandRequestFactory': None,
        'MoveTreeCommandRequestFactory': None
    }
    
    # クラス設定
    classes = {
        'DockerRequest': 'src.operations.docker.docker_request.DockerRequest',
        'DockerOpType': 'src.operations.docker.docker_request.DockerOpType'
    }
    
    return OperationsRegistry(
        drivers=drivers,
        factories=factories,
        classes=classes
    )


def create_driver_factory_pure(
    driver_class_path: str,
    config: OperationsConfig
) -> Callable[[], Any]:
    """
    ドライバーファクトリーを作成する純粋関数
    
    Args:
        driver_class_path: ドライバークラスのパス
        config: Operations設定
        
    Returns:
        ドライバーインスタンスを生成するファクトリー関数
    """
    def factory():
        # 動的インポート
        module_path, class_name = driver_class_path.rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        driver_class = getattr(module, class_name)
        
        # ファイルドライバーの場合はbase_dirを渡す
        if 'file_driver' in driver_class_path.lower():
            return driver_class(base_dir=config.base_dir)
        else:
            return driver_class()
    
    return factory


def validate_operations_config_pure(config: OperationsConfig) -> list[str]:
    """
    Operations設定を検証する純粋関数
    
    Args:
        config: 検証するOperations設定
        
    Returns:
        エラーメッセージのリスト（空の場合は有効）
    """
    errors = []
    
    # base_dirの検証
    if config.base_dir and not isinstance(config.base_dir, Path):
        errors.append("base_dir must be a Path object")
    
    # driver_typeの検証
    valid_driver_types = {"local", "mock"}
    
    if config.shell_driver_type not in valid_driver_types:
        errors.append(f"Invalid shell_driver_type: {config.shell_driver_type}")
    
    if config.docker_driver_type not in valid_driver_types:
        errors.append(f"Invalid docker_driver_type: {config.docker_driver_type}")
        
    if config.file_driver_type not in valid_driver_types:
        errors.append(f"Invalid file_driver_type: {config.file_driver_type}")
    
    return errors


def get_operations_dependencies_pure(registry: OperationsRegistry) -> Dict[str, list[str]]:
    """
    Operations依存関係を分析する純粋関数
    
    Args:
        registry: Operations登録情報
        
    Returns:
        各コンポーネントの依存関係辞書
    """
    dependencies = {}
    
    # ドライバー依存関係
    for name, class_path in registry.drivers.items():
        module_path = '.'.join(class_path.split('.')[:-1])
        dependencies[name] = [module_path]
    
    # クラス依存関係
    for name, class_path in registry.classes.items():
        module_path = '.'.join(class_path.split('.')[:-1])
        dependencies[name] = [module_path]
    
    return dependencies


# 後方互換性のためのブリッジ関数
def build_operations_from_config_pure(config: OperationsConfig):
    """
    純粋関数ベースのOperations構築
    既存のDIContainerを返すが、純粋関数で構築される
    
    Args:
        config: Operations設定
        
    Returns:
        構築されたDIContainer
    """
    from src.operations.di_container import DIContainer
    
    # 設定検証
    errors = validate_operations_config_pure(config)
    if errors:
        raise ValueError(f"Invalid operations config: {errors}")
    
    # 登録情報構築
    registry = build_operations_registry_pure(config)
    
    # DIコンテナ作成
    operations = DIContainer()
    
    # ドライバー登録
    for name, class_path in registry.drivers.items():
        factory = create_driver_factory_pure(class_path, config)
        operations.register(name, factory)
    
    # ファクトリー登録
    for name, class_path in registry.factories.items():
        if class_path is None:
            operations.register(name, lambda: None)
        else:
            # 将来の実装用
            pass
    
    # クラス登録
    for name, class_path in registry.classes.items():
        module_path, class_name = class_path.rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        class_obj = getattr(module, class_name)
        operations.register(name, lambda: class_obj)
    
    return operations