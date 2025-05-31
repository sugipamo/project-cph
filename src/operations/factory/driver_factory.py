"""
ドライバーファクトリー
設定に基づいて適切なドライバーインスタンスを生成する
"""
import os
from typing import Optional, Dict, Any
from pathlib import Path


class DriverFactory:
    """ドライバー生成のファクトリークラス"""
    
    # デフォルトの設定
    DEFAULT_CONFIG = {
        'file_driver': 'local',
        'shell_driver': 'local',
        'docker_driver': 'local'
    }
    
    @classmethod
    def create_file_driver(cls, driver_type: Optional[str] = None, **kwargs):
        """
        FileDriverのインスタンスを生成する
        
        Args:
            driver_type: ドライバータイプ ('local', 'mock', 'dummy')
            **kwargs: ドライバーの初期化引数
            
        Returns:
            FileDriverのインスタンス
        """
        if driver_type is None:
            driver_type = cls._get_driver_type_from_config('file_driver')
        
        if driver_type == 'local':
            from src.operations.file.local_file_driver import LocalFileDriver
            return LocalFileDriver(**kwargs)
        elif driver_type == 'mock':
            from src.operations.mock.mock_file_driver import MockFileDriver
            return MockFileDriver(**kwargs)
        elif driver_type == 'dummy':
            from src.operations.mock.dummy_file_driver import DummyFileDriver
            return DummyFileDriver(**kwargs)
        else:
            raise ValueError(f"Unknown file driver type: {driver_type}")
    
    @classmethod
    def create_shell_driver(cls, driver_type: Optional[str] = None, **kwargs):
        """
        ShellDriverのインスタンスを生成する
        
        Args:
            driver_type: ドライバータイプ ('local', 'mock', 'dummy')
            **kwargs: ドライバーの初期化引数
            
        Returns:
            ShellDriverのインスタンス
        """
        if driver_type is None:
            driver_type = cls._get_driver_type_from_config('shell_driver')
        
        if driver_type == 'local':
            from src.operations.shell.local_shell_driver import LocalShellDriver
            return LocalShellDriver(**kwargs)
        elif driver_type == 'mock':
            from src.operations.mock.mock_shell_driver import MockShellDriver
            return MockShellDriver(**kwargs)
        elif driver_type == 'dummy':
            from src.operations.mock.dummy_shell_driver import DummyShellDriver
            return DummyShellDriver(**kwargs)
        else:
            raise ValueError(f"Unknown shell driver type: {driver_type}")
    
    @classmethod
    def create_docker_driver(cls, driver_type: Optional[str] = None, **kwargs):
        """
        DockerDriverのインスタンスを生成する
        
        Args:
            driver_type: ドライバータイプ ('local', 'mock', 'dummy')
            **kwargs: ドライバーの初期化引数
            
        Returns:
            DockerDriverのインスタンス
        """
        if driver_type is None:
            driver_type = cls._get_driver_type_from_config('docker_driver')
        
        if driver_type == 'local':
            from src.operations.docker.docker_driver import LocalDockerDriver
            return LocalDockerDriver(**kwargs)
        elif driver_type == 'mock':
            from src.operations.mock.mock_docker_driver import MockDockerDriver
            return MockDockerDriver(**kwargs)
        elif driver_type == 'dummy':
            from src.operations.mock.dummy_docker_driver import DummyDockerDriver
            return DummyDockerDriver(**kwargs)
        else:
            raise ValueError(f"Unknown docker driver type: {driver_type}")
    
    @classmethod
    def create_all_drivers(cls, 
                          file_type: Optional[str] = None,
                          shell_type: Optional[str] = None,
                          docker_type: Optional[str] = None,
                          **kwargs) -> Dict[str, Any]:
        """
        すべてのドライバーを一度に生成する
        
        Args:
            file_type: FileDriverのタイプ
            shell_type: ShellDriverのタイプ
            docker_type: DockerDriverのタイプ
            **kwargs: 各ドライバーの初期化引数
            
        Returns:
            ドライバーの辞書
        """
        return {
            'file': cls.create_file_driver(file_type, **kwargs.get('file_kwargs', {})),
            'shell': cls.create_shell_driver(shell_type, **kwargs.get('shell_kwargs', {})),
            'docker': cls.create_docker_driver(docker_type, **kwargs.get('docker_kwargs', {}))
        }
    
    @classmethod
    def auto_configure_for_testing(cls, **kwargs) -> Dict[str, Any]:
        """
        テスト用にドライバーを自動設定する
        
        Args:
            **kwargs: 各ドライバーの初期化引数
            
        Returns:
            テスト用ドライバーの辞書
        """
        return cls.create_all_drivers(
            file_type='mock',
            shell_type='mock',
            docker_type='mock',
            **kwargs
        )
    
    @classmethod
    def auto_configure_for_ci(cls, **kwargs) -> Dict[str, Any]:
        """
        CI環境用にドライバーを自動設定する
        
        Args:
            **kwargs: 各ドライバーの初期化引数
            
        Returns:
            CI用ドライバーの辞書
        """
        # CI環境ではDockerが使用できない場合があるため、Dummyを使用
        return cls.create_all_drivers(
            file_type='local',
            shell_type='local',
            docker_type='dummy',
            **kwargs
        )
    
    @classmethod
    def _get_driver_type_from_config(cls, driver_name: str) -> str:
        """
        設定からドライバータイプを取得する
        
        Args:
            driver_name: ドライバー名
            
        Returns:
            ドライバータイプ
        """
        # 環境変数から取得
        env_var = f"CPH_{driver_name.upper()}"
        env_value = os.environ.get(env_var)
        if env_value:
            return env_value.lower()
        
        # テスト環境の検出
        if cls._is_test_environment():
            return 'mock'
        
        # CI環境の検出
        if cls._is_ci_environment():
            if driver_name == 'docker_driver':
                return 'dummy'
            return 'local'
        
        # デフォルト設定を使用
        return cls.DEFAULT_CONFIG.get(driver_name, 'local')
    
    @staticmethod
    def _is_test_environment() -> bool:
        """テスト環境かどうかを判定する"""
        # pytest実行中かどうか
        test_indicators = [
            'PYTEST_CURRENT_TEST',
            'CPH_TEST_MODE'
        ]
        return any(os.environ.get(indicator) for indicator in test_indicators)
    
    @staticmethod
    def _is_ci_environment() -> bool:
        """CI環境かどうかを判定する"""
        ci_indicators = [
            'CI',
            'CONTINUOUS_INTEGRATION',
            'GITHUB_ACTIONS',
            'TRAVIS',
            'CIRCLECI',
            'JENKINS_URL'
        ]
        return any(os.environ.get(indicator) for indicator in ci_indicators)
    
    @classmethod
    def load_config_from_file(cls, config_path: str) -> Dict[str, str]:
        """
        設定ファイルからドライバー設定を読み込む
        
        Args:
            config_path: 設定ファイルのパス
            
        Returns:
            設定の辞書
        """
        config_file = Path(config_path)
        if not config_file.exists():
            return cls.DEFAULT_CONFIG.copy()
        
        # JSONまたはYAMLファイルから設定を読み込む
        import json
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix.lower() == '.json':
                    config = json.load(f)
                else:
                    # YAML対応は必要に応じて実装
                    raise NotImplementedError("YAML config not yet supported")
                
                # ドライバー設定のみを抽出
                driver_config = {}
                for key, value in config.get('drivers', {}).items():
                    if key in cls.DEFAULT_CONFIG:
                        driver_config[key] = value
                
                return {**cls.DEFAULT_CONFIG, **driver_config}
        
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
            return cls.DEFAULT_CONFIG.copy()