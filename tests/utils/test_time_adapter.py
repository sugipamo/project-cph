import pytest
from unittest.mock import Mock
from src.utils.time_adapter import TimeAdapter


class TestTimeAdapter:
    def test_current_time_returns_float(self):
        """Test that current_time() returns a float timestamp"""
        mock_provider = Mock()
        mock_provider.now.return_value = 1234567890.5
        
        adapter = TimeAdapter(mock_provider)
        result = adapter.current_time()
        
        assert result == 1234567890.5
        mock_provider.now.assert_called_once()
    
    def test_sleep_delegates_to_provider(self):
        """Test that sleep() delegates to the time provider"""
        mock_provider = Mock()
        
        adapter = TimeAdapter(mock_provider)
        adapter.sleep(2.5)
        
        mock_provider.sleep.assert_called_once_with(2.5)
    
    def test_multiple_time_calls(self):
        """Test multiple calls to current_time()"""
        mock_provider = Mock()
        mock_provider.now.side_effect = [100.0, 101.0, 102.0]
        
        adapter = TimeAdapter(mock_provider)
        
        assert adapter.current_time() == 100.0
        assert adapter.current_time() == 101.0
        assert adapter.current_time() == 102.0
        
        assert mock_provider.now.call_count == 3
    
    def test_time_adapter_with_different_providers(self):
        """Test creating adapters with different providers"""
        provider1 = Mock()
        provider1.now.return_value = 100.0
        
        provider2 = Mock()
        provider2.now.return_value = 200.0
        
        adapter1 = TimeAdapter(provider1)
        adapter2 = TimeAdapter(provider2)
        
        assert adapter1.current_time() == 100.0
        assert adapter2.current_time() == 200.0