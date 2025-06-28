"""Tests for DebugService."""
import pytest
from unittest.mock import Mock, MagicMock, call
from src.application.services.debug_service import DebugService, DebugServiceFactory
from src.infrastructure.di_container import DIContainer
from src.configuration.runtime_config_overlay import DebugConfigProvider, RuntimeConfigOverlay


class TestDebugService:
    """Test cases for DebugService."""

    def test_init(self):
        """Test DebugService initialization."""
        infrastructure = Mock(spec=DIContainer)
        
        service = DebugService(infrastructure)
        
        assert service.infrastructure == infrastructure
        assert isinstance(service.overlay, RuntimeConfigOverlay)
        assert isinstance(service.config_provider, DebugConfigProvider)
        assert service._debug_enabled is False

    def test_enable_debug_mode_first_time(self):
        """Test enabling debug mode for the first time."""
        infrastructure = Mock(spec=DIContainer)
        logger = Mock()
        logger.set_level = Mock()
        
        # Mock infrastructure responses
        infrastructure.is_registered.side_effect = lambda key: key == "unified_logger"
        infrastructure.resolve.return_value = logger
        
        service = DebugService(infrastructure)
        service.config_provider = Mock()
        
        service.enable_debug_mode()
        
        # Verify debug mode is enabled
        assert service._debug_enabled is True
        service.config_provider.enable_debug_mode.assert_called_once()
        
        # Verify logger level was set
        logger.set_level.assert_called_with("DEBUG")
        logger.info.assert_called_with("Debug mode enabled - 詳細ログが出力されます")

    def test_enable_debug_mode_already_enabled(self):
        """Test enabling debug mode when already enabled."""
        infrastructure = Mock(spec=DIContainer)
        service = DebugService(infrastructure)
        service._debug_enabled = True
        service.config_provider = Mock()
        
        service.enable_debug_mode()
        
        # Should not call enable again
        service.config_provider.enable_debug_mode.assert_not_called()

    def test_disable_debug_mode(self):
        """Test disabling debug mode."""
        infrastructure = Mock(spec=DIContainer)
        service = DebugService(infrastructure)
        service._debug_enabled = True
        service.config_provider = Mock()
        
        service.disable_debug_mode()
        
        assert service._debug_enabled is False
        service.config_provider.disable_debug_mode.assert_called_once()

    def test_disable_debug_mode_already_disabled(self):
        """Test disabling debug mode when already disabled."""
        infrastructure = Mock(spec=DIContainer)
        service = DebugService(infrastructure)
        service._debug_enabled = False
        service.config_provider = Mock()
        
        service.disable_debug_mode()
        
        # Should not call disable
        service.config_provider.disable_debug_mode.assert_not_called()

    def test_is_debug_enabled(self):
        """Test checking debug status."""
        infrastructure = Mock(spec=DIContainer)
        service = DebugService(infrastructure)
        
        assert service.is_debug_enabled() is False
        
        service._debug_enabled = True
        assert service.is_debug_enabled() is True

    def test_get_debug_config_provider(self):
        """Test getting debug config provider."""
        infrastructure = Mock(spec=DIContainer)
        service = DebugService(infrastructure)
        
        provider = service.get_debug_config_provider()
        
        assert provider == service.config_provider
        assert isinstance(provider, DebugConfigProvider)

    def test_update_logger_levels_all_loggers(self):
        """Test updating all logger levels."""
        infrastructure = Mock(spec=DIContainer)
        loggers = {
            "unified_logger": Mock(),
            "workflow_logger": Mock(),
            "application_logger": Mock(),
            "logger": Mock()
        }
        
        # Mock infrastructure to return different loggers
        infrastructure.is_registered.return_value = True
        infrastructure.resolve.side_effect = lambda key: loggers[key]
        
        service = DebugService(infrastructure)
        service._update_logger_levels()
        
        # Verify all loggers had their level set
        for logger_name, logger in loggers.items():
            logger.set_level.assert_called_once_with("DEBUG")

    def test_update_logger_levels_some_missing(self):
        """Test updating logger levels when some loggers are missing."""
        infrastructure = Mock(spec=DIContainer)
        logger = Mock()
        
        # Only unified_logger is registered
        infrastructure.is_registered.side_effect = lambda key: key == "unified_logger"
        infrastructure.resolve.return_value = logger
        
        service = DebugService(infrastructure)
        service._update_logger_levels()
        
        # Should only try to set level on registered logger
        logger.set_level.assert_called_once_with("DEBUG")

    def test_update_logger_levels_no_set_level_method(self):
        """Test updating logger levels when logger lacks set_level method."""
        infrastructure = Mock(spec=DIContainer)
        logger = Mock(spec=[])  # No set_level method
        
        infrastructure.is_registered.return_value = True
        infrastructure.resolve.return_value = logger
        
        service = DebugService(infrastructure)
        # Should not raise exception if logger doesn't have set_level
        service._update_logger_levels()

    def test_update_logger_levels_exception(self):
        """Test exception handling in logger level update."""
        infrastructure = Mock(spec=DIContainer)
        logger = Mock()
        logger.set_level.side_effect = Exception("Logger error")
        
        infrastructure.is_registered.return_value = True
        infrastructure.resolve.return_value = logger
        
        service = DebugService(infrastructure)
        
        with pytest.raises(RuntimeError, match="ログサービス.*の設定に失敗"):
            service._update_logger_levels()

    def test_show_debug_notification_success(self):
        """Test showing debug notification."""
        infrastructure = Mock(spec=DIContainer)
        logger = Mock()
        
        infrastructure.is_registered.return_value = True
        infrastructure.resolve.return_value = logger
        
        service = DebugService(infrastructure)
        service._show_debug_notification()
        
        logger.info.assert_called_once_with("Debug mode enabled - 詳細ログが出力されます")

    def test_show_debug_notification_no_logger(self):
        """Test showing debug notification when logger is not available."""
        infrastructure = Mock(spec=DIContainer)
        infrastructure.is_registered.return_value = False
        
        service = DebugService(infrastructure)
        
        # Should not raise exception when logger is not registered
        # The method checks is_registered before trying to resolve
        service._show_debug_notification()

    def test_show_debug_notification_exception(self):
        """Test exception handling in debug notification."""
        infrastructure = Mock(spec=DIContainer)
        infrastructure.is_registered.return_value = True
        infrastructure.resolve.side_effect = Exception("Resolution error")
        
        service = DebugService(infrastructure)
        
        with pytest.raises(RuntimeError, match="デバッグ通知のログ出力に失敗"):
            service._show_debug_notification()

    def test_log_debug_context_enabled(self):
        """Test logging debug context when debug is enabled."""
        infrastructure = Mock(spec=DIContainer)
        logger = Mock()
        
        infrastructure.is_registered.return_value = True
        infrastructure.resolve.return_value = logger
        
        service = DebugService(infrastructure)
        service._debug_enabled = True
        
        context = {"user": "test", "action": "debug"}
        service.log_debug_context(context)
        
        # Verify debug messages were logged
        assert logger.debug.call_count == 2
        logger.debug.assert_any_call("🔍 デバッグモードが有効化されました")
        logger.debug.assert_any_call(f"🔍 実行コンテキスト: {context}")

    def test_log_debug_context_disabled(self):
        """Test logging debug context when debug is disabled."""
        infrastructure = Mock(spec=DIContainer)
        
        service = DebugService(infrastructure)
        service._debug_enabled = False
        
        context = {"user": "test"}
        service.log_debug_context(context)
        
        # Should not attempt to log anything
        infrastructure.is_registered.assert_not_called()

    def test_log_debug_context_exception(self):
        """Test exception handling in debug context logging."""
        infrastructure = Mock(spec=DIContainer)
        infrastructure.is_registered.return_value = True
        infrastructure.resolve.side_effect = Exception("Logger error")
        
        service = DebugService(infrastructure)
        service._debug_enabled = True
        
        with pytest.raises(RuntimeError, match="デバッグコンテキストのログ出力に失敗"):
            service.log_debug_context({"test": "data"})


class TestDebugServiceFactory:
    """Test cases for DebugServiceFactory."""

    def test_create_debug_service(self):
        """Test creating DebugService instance."""
        infrastructure = Mock(spec=DIContainer)
        
        service = DebugServiceFactory.create_debug_service(infrastructure)
        
        assert isinstance(service, DebugService)
        assert service.infrastructure == infrastructure
        assert service._debug_enabled is False