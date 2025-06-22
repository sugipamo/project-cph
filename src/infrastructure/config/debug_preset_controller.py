"""デバッグプリセット制御システム

デバッグモード専用のプリセット制御を行う。
デバッグモード開始時に現在の設定を保存し、終了時に復元する。
"""
from typing import Optional

from src.infrastructure.config.preset_manager import PresetManager


class DebugPresetController:
    """デバッグ専用プリセット制御

    デバッグモードの開始・終了時にプリセットの切り替えを管理。
    元の設定を保存し、デバッグ終了時に自動復元する。
    """

    def __init__(self, preset_manager: PresetManager):
        """DebugPresetControllerの初期化

        Args:
            preset_manager: プリセット管理インスタンス
        """
        self.preset_manager = preset_manager
        self._pre_debug_preset: Optional[str] = None
        self._debug_preset_active = False

    def enable_debug_preset(self) -> None:
        """デバッグプリセットを有効化し、現在の設定を保存

        現在適用中のプリセットを保存してから、デバッグ専用プリセットを適用する。
        既にデバッグプリセットが有効な場合は何もしない。
        """
        if self._debug_preset_active:
            return

        # 現在のプリセットを保存
        self._pre_debug_preset = self.preset_manager.get_current_preset()

        # デバッグプリセットを適用
        debug_preset_applied = self.preset_manager.apply_preset("debug")

        if debug_preset_applied:
            self._debug_preset_active = True
        else:
            # デバッグプリセットが見つからない場合は設定を直接変更
            self._apply_fallback_debug_settings()
            self._debug_preset_active = True

    def disable_debug_preset(self) -> None:
        """デバッグプリセットを無効化し、元の設定を復元

        保存しておいた元のプリセットを復元する。
        元のプリセットがない場合はデフォルト設定に戻す。
        """
        if not self._debug_preset_active:
            return

        if self._pre_debug_preset is not None:
            # 元のプリセットを復元
            self.preset_manager.apply_preset(self._pre_debug_preset)
        else:
            # 元のプリセットがない場合はデフォルト設定に復元
            self.preset_manager.restore_default()

        self._debug_preset_active = False
        self._pre_debug_preset = None

    def is_debug_preset_active(self) -> bool:
        """デバッグプリセットがアクティブかチェック

        Returns:
            デバッグプリセットが有効な場合True
        """
        return self._debug_preset_active

    def _apply_fallback_debug_settings(self) -> None:
        """デバッグプリセットが見つからない場合のフォールバック設定

        デバッグプリセットが設定ファイルに存在しない場合に、
        直接オーバーレイを使用してデバッグ用の設定を適用する。
        """
        overlay = self.preset_manager.overlay

        # 基本的なデバッグ出力設定
        overlay.set_overlay("output.show_workflow_summary", True)
        overlay.set_overlay("output.show_step_details", True)
        overlay.set_overlay("output.show_execution_completion", True)
        overlay.set_overlay("output.show_execution_settings", True)

        # ステップ詳細設定
        overlay.set_overlay("output.step_details.show_type", True)
        overlay.set_overlay("output.step_details.show_command", True)
        overlay.set_overlay("output.step_details.show_path", True)
        overlay.set_overlay("output.step_details.show_execution_time", True)
        overlay.set_overlay("output.step_details.show_stdout", True)
        overlay.set_overlay("output.step_details.show_stderr", True)
        overlay.set_overlay("output.step_details.show_return_code", True)
        overlay.set_overlay("output.step_details.max_command_length", 200)
        overlay.set_overlay("output.step_details.show_debug_context", True)
        overlay.set_overlay("output.step_details.show_logger_levels", True)

        # デバッグ固有設定
        overlay.set_overlay("debug.show_debug_messages", True)
        overlay.set_overlay("debug.show_context_details", True)
        overlay.set_overlay("debug.show_infrastructure_state", True)
        overlay.set_overlay("debug.show_service_registrations", True)
