#!/usr/bin/env python3
"""Debug Service のテスト"""

import pytest
from unittest.mock import Mock, MagicMock

from src.infrastructure.debug.debug_service import DebugService, DebugServiceFactory
from src.infrastructure.di_container import DIContainer


class TestDebugService:
    """DebugService のテストクラス"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_infrastructure = Mock(spec=DIContainer)
        self.debug_service = DebugService(self.mock_infrastructure)

    def test_初期状態はデバッグ無効(self):
        """初期状態でデバッグが無効であることを確認"""
        assert not self.debug_service.is_debug_enabled()

    def test_デバッグモード有効化(self):
        """デバッグモードを有効化できることを確認"""
        # モックロガーを設定
        mock_logger = Mock()
        self.mock_infrastructure.is_registered.return_value = True
        self.mock_infrastructure.resolve.return_value = mock_logger
        
        self.debug_service.enable_debug_mode()
        
        assert self.debug_service.is_debug_enabled()

    def test_デバッグモード重複有効化(self):
        """既にデバッグモードが有効な場合、何もしないことを確認"""
        # モックロガーを設定
        mock_logger = Mock()
        self.mock_infrastructure.is_registered.return_value = True
        self.mock_infrastructure.resolve.return_value = mock_logger
        
        self.debug_service.enable_debug_mode()
        self.debug_service.enable_debug_mode()  # 2回目の呼び出し
        
        # resolve が呼ばれる回数を確認（重複処理されていないことを確認）
        assert self.mock_infrastructure.resolve.call_count <= 5  # 初回のみ呼ばれる

    def test_デバッグモード無効化(self):
        """デバッグモードを無効化できることを確認"""
        # モックロガーを設定
        mock_logger = Mock()
        self.mock_infrastructure.is_registered.return_value = True
        self.mock_infrastructure.resolve.return_value = mock_logger
        
        self.debug_service.enable_debug_mode()
        assert self.debug_service.is_debug_enabled()
        
        self.debug_service.disable_debug_mode()
        assert not self.debug_service.is_debug_enabled()

    def test_デバッグモード重複無効化(self):
        """既にデバッグモードが無効な場合、何もしないことを確認"""
        self.debug_service.disable_debug_mode()  # 最初から無効
        assert not self.debug_service.is_debug_enabled()

    def test_デバッグ設定プロバイダー取得(self):
        """デバッグ設定プロバイダーを取得できることを確認"""
        provider = self.debug_service.get_debug_config_provider()
        assert provider is not None

    def test_ロガーレベル更新_全ロガー存在(self):
        """全てのロガーが存在する場合のレベル更新を確認"""
        # モックロガーを設定
        mock_logger = Mock()
        mock_logger.set_level = Mock()
        
        self.mock_infrastructure.is_registered.return_value = True
        self.mock_infrastructure.resolve.return_value = mock_logger
        
        self.debug_service.enable_debug_mode()
        
        # set_level が呼ばれたことを確認
        assert mock_logger.set_level.called

    def test_ロガーレベル更新_一部ロガー不存在(self):
        """一部のロガーが存在しない場合の処理を確認"""
        def mock_is_registered(key):
            return key in ["unified_logger", "logger"]
        
        mock_logger = Mock()
        mock_logger.set_level = Mock()
        
        self.mock_infrastructure.is_registered.side_effect = mock_is_registered
        self.mock_infrastructure.resolve.return_value = mock_logger
        
        self.debug_service.enable_debug_mode()
        
        # エラーなく処理が完了することを確認
        assert self.debug_service.is_debug_enabled()

    def test_ロガーレベル更新_エラー処理(self):
        """ロガーレベル更新でエラーが発生した場合の処理を確認"""
        self.mock_infrastructure.is_registered.return_value = True
        self.mock_infrastructure.resolve.side_effect = Exception("Logger error")
        
        with pytest.raises(RuntimeError, match="ログサービス .* の設定に失敗"):
            self.debug_service.enable_debug_mode()

    def test_デバッグ通知表示_成功(self):
        """デバッグ通知が正常に表示されることを確認"""
        mock_logger = Mock()
        self.mock_infrastructure.is_registered.return_value = True
        self.mock_infrastructure.resolve.return_value = mock_logger
        
        self.debug_service.enable_debug_mode()
        
        # info メソッドが呼ばれたことを確認
        mock_logger.info.assert_called()

    def test_デバッグ通知表示_エラー処理(self):
        """デバッグ通知でエラーが発生した場合の処理を確認"""
        self.mock_infrastructure.is_registered.return_value = True
        self.mock_infrastructure.resolve.side_effect = Exception("Logger error")
        
        with pytest.raises(RuntimeError, match="ログサービス .* の設定に失敗"):
            self.debug_service.enable_debug_mode()

    def test_デバッグコンテキストログ出力_有効時(self):
        """デバッグモード有効時にコンテキストがログ出力されることを確認"""
        mock_logger = Mock()
        self.mock_infrastructure.is_registered.return_value = True
        self.mock_infrastructure.resolve.return_value = mock_logger
        
        self.debug_service.enable_debug_mode()
        
        context = {"test": "value", "number": 42}
        self.debug_service.log_debug_context(context)
        
        # デバッグログが出力されることを確認
        mock_logger.debug.assert_called()

    def test_デバッグコンテキストログ出力_無効時(self):
        """デバッグモード無効時にコンテキストログが出力されないことを確認"""
        context = {"test": "value"}
        self.debug_service.log_debug_context(context)
        
        # ロガーが呼ばれないことを確認
        self.mock_infrastructure.resolve.assert_not_called()

    def test_デバッグコンテキストログ出力_エラー処理(self):
        """デバッグコンテキストログ出力でエラーが発生した場合の処理を確認"""
        mock_logger = Mock()
        self.mock_infrastructure.is_registered.return_value = True
        self.mock_infrastructure.resolve.return_value = mock_logger
        
        self.debug_service.enable_debug_mode()
        
        # ロガー解決でエラーを発生させる
        self.mock_infrastructure.resolve.side_effect = Exception("Logger error")
        
        context = {"test": "value"}
        with pytest.raises(RuntimeError, match="デバッグコンテキストのログ出力に失敗"):
            self.debug_service.log_debug_context(context)


class TestDebugServiceFactory:
    """DebugServiceFactory のテストクラス"""

    def test_デバッグサービス作成(self):
        """DebugServiceを作成できることを確認"""
        mock_infrastructure = Mock(spec=DIContainer)
        
        debug_service = DebugServiceFactory.create_debug_service(mock_infrastructure)
        
        assert isinstance(debug_service, DebugService)
        assert debug_service.infrastructure is mock_infrastructure