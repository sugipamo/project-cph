"""出力プリセット管理システム

デバッグ機能とoutput_presetsの統合を実現する。
既存のプリセットシステムとデバッグモードを統一的に管理。
"""
from typing import Any, Dict, List, Optional

from src.infrastructure.config.runtime_config_overlay import RuntimeConfigOverlay


class PresetManager:
    """出力プリセットの管理クラス

    設定ファイルのoutput_presetsを読み込み、RuntimeConfigOverlayを使用して
    実行時に出力設定を動的に変更する。
    """

    def __init__(self, config_manager, overlay: RuntimeConfigOverlay):
        """PresetManagerの初期化

        Args:
            config_manager: 設定管理インスタンス
            overlay: 実行時設定オーバーレイ
        """
        self.config_manager = config_manager
        self.overlay = overlay
        self._active_preset: Optional[str] = None
        self._presets_cache: Optional[Dict[str, Dict[str, Any]]] = None

    def apply_preset(self, preset_name: str) -> bool:
        """指定されたプリセットを適用

        Args:
            preset_name: 適用するプリセット名

        Returns:
            適用成功時True、失敗時False
        """
        presets = self._get_available_presets_dict()

        if preset_name not in presets:
            return False

        preset_config = presets[preset_name]
        self._apply_preset_config(preset_config)
        self._active_preset = preset_name

        return True

    def get_available_presets(self) -> List[str]:
        """利用可能なプリセット一覧を取得

        Returns:
            プリセット名のリスト
        """
        presets = self._get_available_presets_dict()
        return list(presets.keys())

    def get_current_preset(self) -> Optional[str]:
        """現在適用中のプリセット名を取得

        Returns:
            アクティブなプリセット名、未設定時はNone
        """
        return self._active_preset

    def restore_default(self) -> None:
        """デフォルト設定に復元

        プリセットの適用を解除し、元の設定に戻す。
        """
        self.overlay.clear_overlay()
        self._active_preset = None

    def _get_available_presets_dict(self) -> Dict[str, Dict[str, Any]]:
        """利用可能なプリセット辞書を取得（キャッシュ付き）

        Returns:
            プリセット設定の辞書
        """
        if self._presets_cache is None:
            self._presets_cache = self._load_presets_from_config()

        return self._presets_cache

    def _load_presets_from_config(self) -> Dict[str, Dict[str, Any]]:
        """設定ファイルからプリセットを読み込み

        Returns:
            プリセット設定の辞書
        """
        try:
            presets = self.config_manager.resolve_config(['output_presets'], dict)
            return presets
        except (KeyError, TypeError):
            return {}

    def _apply_preset_config(self, preset_config: Dict[str, Any]) -> None:
        """プリセット設定をオーバーレイに適用

        Args:
            preset_config: 適用するプリセット設定
        """
        # 基本出力設定の適用
        for key, value in preset_config.items():
            if key in ['show_workflow_summary', 'show_step_details', 'show_execution_completion', 'show_execution_settings']:
                self.overlay.set_overlay(f"output.{key}", value)
            elif key == 'step_details' and isinstance(value, dict):
                # step_details の各項目を個別に設定
                for detail_key, detail_value in value.items():
                    self.overlay.set_overlay(f"output.step_details.{detail_key}", detail_value)
            elif key == 'debug_specific' and isinstance(value, dict):
                # デバッグ固有設定の適用
                for debug_key, debug_value in value.items():
                    self.overlay.set_overlay(f"debug.{debug_key}", debug_value)
