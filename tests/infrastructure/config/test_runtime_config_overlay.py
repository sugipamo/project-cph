#!/usr/bin/env python3
"""Runtime Config Overlay のテスト"""

import pytest

from src.infrastructure.config.runtime_config_overlay import RuntimeConfigOverlay, DebugConfigProvider


class TestRuntimeConfigOverlay:
    """RuntimeConfigOverlay のテストクラス"""

    def test_初期状態は非アクティブ(self):
        """初期状態でオーバーレイが非アクティブであることを確認"""
        overlay = RuntimeConfigOverlay()
        assert not overlay.is_active()

    def test_オーバーレイ設定後はアクティブ(self):
        """オーバーレイ設定後にアクティブになることを確認"""
        overlay = RuntimeConfigOverlay()
        overlay.set_overlay("test.key", "value")
        assert overlay.is_active()

    def test_単一キーのオーバーレイ(self):
        """単一キーのオーバーレイが正常に動作することを確認"""
        overlay = RuntimeConfigOverlay()
        overlay.set_overlay("simple_key", "test_value")
        
        assert overlay.get_overlay("simple_key") == "test_value"
        assert overlay.has_overlay("simple_key")

    def test_ネストしたキーのオーバーレイ(self):
        """ネストしたキーのオーバーレイが正常に動作することを確認"""
        overlay = RuntimeConfigOverlay()
        overlay.set_overlay("nested.deep.key", "nested_value")
        
        assert overlay.get_overlay("nested.deep.key") == "nested_value"
        assert overlay.has_overlay("nested.deep.key")

    def test_存在しないキーのデフォルト値(self):
        """存在しないキーに対してデフォルト値が返されることを確認"""
        overlay = RuntimeConfigOverlay()
        
        assert overlay.get_overlay("nonexistent", "default") == "default"
        assert not overlay.has_overlay("nonexistent")

    def test_非アクティブ時はデフォルト値を返す(self):
        """非アクティブ時は常にデフォルト値を返すことを確認"""
        overlay = RuntimeConfigOverlay()
        
        # アクティブではない状態
        assert overlay.get_overlay("any.key", "default") == "default"

    def test_オーバーレイクリア(self):
        """オーバーレイをクリアできることを確認"""
        overlay = RuntimeConfigOverlay()
        overlay.set_overlay("test.key", "value")
        
        assert overlay.is_active()
        overlay.clear_overlay()
        
        assert not overlay.is_active()
        assert overlay.get_overlay("test.key", "default") == "default"

    def test_複数のオーバーレイ設定(self):
        """複数のオーバーレイ設定が正常に動作することを確認"""
        overlay = RuntimeConfigOverlay()
        
        overlay.set_overlay("config1.key1", "value1")
        overlay.set_overlay("config2.key2", "value2")
        overlay.set_overlay("config1.nested.key", "nested_value")
        
        assert overlay.get_overlay("config1.key1") == "value1"
        assert overlay.get_overlay("config2.key2") == "value2"
        assert overlay.get_overlay("config1.nested.key") == "nested_value"


class TestDebugConfigProvider:
    """DebugConfigProvider のテストクラス"""

    def test_初期状態はデバッグ無効(self):
        """初期状態でデバッグが無効であることを確認"""
        overlay = RuntimeConfigOverlay()
        provider = DebugConfigProvider(overlay)
        
        assert not provider.is_debug_enabled()
        assert provider.get_log_level() == "INFO"
        assert not provider.should_show_step_details()

    def test_デバッグモード有効化(self):
        """デバッグモードを有効化できることを確認"""
        overlay = RuntimeConfigOverlay()
        provider = DebugConfigProvider(overlay)
        
        provider.enable_debug_mode()
        
        assert provider.is_debug_enabled()
        assert provider.get_log_level() == "DEBUG"
        assert provider.should_show_step_details()

    def test_デバッグモード無効化(self):
        """デバッグモードを無効化できることを確認"""
        overlay = RuntimeConfigOverlay()
        provider = DebugConfigProvider(overlay)
        
        provider.enable_debug_mode()
        assert provider.is_debug_enabled()
        
        provider.disable_debug_mode()
        assert not provider.is_debug_enabled()

    def test_カスタムデフォルトログレベル(self):
        """カスタムデフォルトログレベルが使用されることを確認"""
        overlay = RuntimeConfigOverlay()
        provider = DebugConfigProvider(overlay)
        
        assert provider.get_log_level("WARN") == "WARN"

    def test_オーバーレイ設定の確認(self):
        """デバッグモード有効化時にオーバーレイが正しく設定されることを確認"""
        overlay = RuntimeConfigOverlay()
        provider = DebugConfigProvider(overlay)
        
        provider.enable_debug_mode()
        
        # オーバーレイが正しく設定されていることを確認
        assert overlay.get_overlay("logging_config.default_level") == "DEBUG"
        assert overlay.get_overlay("output.show_step_details") is True
        assert overlay.get_overlay("debug") is True