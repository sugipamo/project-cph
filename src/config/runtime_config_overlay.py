"""実行時設定オーバーレイ - 設定の不変性を保ちながら動的変更を実現"""
from typing import Any, Dict


class RuntimeConfigOverlay:
    """実行時の設定オーバーレイ

    元の設定ファイルを変更せずに、実行時のみ設定をオーバーライドする。
    デバッグモードなどの一時的な設定変更に使用。
    """

    def __init__(self):
        self._overlay_config: Dict[str, Any] = {}
        self._active = False

    def set_overlay(self, config_path: str, value: Any) -> None:
        """設定オーバーレイを設定

        Args:
            config_path: 設定パス（例: "logging_config.default_level"）
            value: オーバーレイする値
        """
        path_parts = config_path.split('.')
        current = self._overlay_config

        for part in path_parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[path_parts[-1]] = value
        self._active = True

    def get_overlay(self, config_path: str, default_value: Any = None) -> Any:
        """オーバーレイ設定を取得

        Args:
            config_path: 設定パス
            default_value: デフォルト値

        Returns:
            オーバーレイ設定値またはデフォルト値
        """
        if not self._active:
            return default_value

        path_parts = config_path.split('.')
        current = self._overlay_config

        try:
            for part in path_parts:
                current = current[part]
            return current
        except (KeyError, TypeError):
            return default_value

    def has_overlay(self, config_path: str) -> bool:
        """指定パスにオーバーレイが存在するかチェック

        Args:
            config_path: 設定パス

        Returns:
            オーバーレイが存在する場合True
        """
        return self.get_overlay(config_path) is not None

    def clear_overlay(self) -> None:
        """オーバーレイをクリア"""
        self._overlay_config.clear()
        self._active = False

    def is_active(self) -> bool:
        """オーバーレイがアクティブかチェック"""
        return self._active


class DebugConfigProvider:
    """デバッグ専用設定プロバイダー

    デバッグモード時の設定値を提供する。
    RuntimeConfigOverlayと連携して動作。
    """

    def __init__(self, overlay: RuntimeConfigOverlay):
        self.overlay = overlay

    def enable_debug_mode(self) -> None:
        """デバッグモードを有効化"""
        self.overlay.set_overlay("logging_config.default_level", "DEBUG")
        self.overlay.set_overlay("output.show_step_details", True)
        self.overlay.set_overlay("debug", True)

    def disable_debug_mode(self) -> None:
        """デバッグモードを無効化"""
        self.overlay.clear_overlay()

    def get_log_level(self, default: str = "INFO") -> str:
        """ログレベルを取得（オーバーレイ優先）"""
        return self.overlay.get_overlay("logging_config.default_level", default)

    def is_debug_enabled(self) -> bool:
        """デバッグモードが有効かチェック"""
        return self.overlay.get_overlay("debug", False)

    def should_show_step_details(self) -> bool:
        """ステップ詳細表示が有効かチェック"""
        return self.overlay.get_overlay("output.show_step_details", False)
