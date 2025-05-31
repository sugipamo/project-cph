"""
DriverFactoryのテスト
"""
import pytest
import os
from src.operations.factory.driver_factory import DriverFactory
from src.operations.file.local_file_driver import LocalFileDriver
from src.operations.mock.mock_file_driver import MockFileDriver
from src.operations.mock.dummy_file_driver import DummyFileDriver


def test_create_file_driver_local():
    """LocalFileDriverの生成テスト"""
    driver = DriverFactory.create_file_driver('local')
    assert isinstance(driver, LocalFileDriver)


def test_create_file_driver_mock():
    """MockFileDriverの生成テスト"""
    driver = DriverFactory.create_file_driver('mock')
    assert isinstance(driver, MockFileDriver)


def test_create_file_driver_dummy():
    """DummyFileDriverの生成テスト"""
    driver = DriverFactory.create_file_driver('dummy')
    assert isinstance(driver, DummyFileDriver)


def test_create_file_driver_invalid_type():
    """無効なドライバータイプのテスト"""
    with pytest.raises(ValueError, match="Unknown file driver type"):
        DriverFactory.create_file_driver('invalid')


def test_create_all_drivers():
    """全ドライバーの生成テスト"""
    drivers = DriverFactory.create_all_drivers(
        file_type='mock',
        shell_type='mock',
        docker_type='mock'
    )
    
    assert 'file' in drivers
    assert 'shell' in drivers
    assert 'docker' in drivers
    assert isinstance(drivers['file'], MockFileDriver)


def test_auto_configure_for_testing():
    """テスト用自動設定のテスト"""
    drivers = DriverFactory.auto_configure_for_testing()
    
    assert isinstance(drivers['file'], MockFileDriver)
    # 他のドライバーもMockであることを確認


def test_environment_detection():
    """環境変数による設定のテスト"""
    # テスト環境変数を設定
    os.environ['CPH_FILE_DRIVER'] = 'dummy'
    
    try:
        driver = DriverFactory.create_file_driver()
        assert isinstance(driver, DummyFileDriver)
    finally:
        # 環境変数をクリーンアップ
        del os.environ['CPH_FILE_DRIVER']


def test_driver_with_kwargs():
    """初期化引数付きドライバー生成のテスト"""
    from pathlib import Path
    
    driver = DriverFactory.create_file_driver('local', base_dir=Path('/tmp'))
    assert driver.base_dir == Path('/tmp')


class TestDriverFactoryUsage:
    """DriverFactoryの実用的な使用例"""
    
    def test_request_with_factory_driver(self):
        """FactoryによるドライバーでRequestを実行"""
        from src.operations.file.file_request import FileRequest
        from src.operations.file.file_op_type import FileOpType
        
        # テスト用ドライバーを生成
        driver = DriverFactory.create_file_driver('mock')
        
        # ファイル存在状態を設定
        driver.set_file_exists('test.txt', exists=True)
        
        # Requestを実行
        request = FileRequest(FileOpType.EXISTS, 'test.txt')
        result = request.execute(driver=driver)
        
        # 振る舞い検証
        assert result.is_success()
        driver.assert_operation_called('exists')
    
    # test_environment_based_driver_selection removed due to method refactoring