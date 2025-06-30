"""デバッグサービス - デバッグ機能の統括管理"""

from old_src.infrastructure.config.runtime_config_overlay import DebugConfigProvider, RuntimeConfigOverlay
from old_src.infrastructure.di_container import DIContainer


class DebugService:
    """デバッグ機能の統括サービス

    デバッグモードの管理、ログ設定、出力制御を統括する。
    責務の分離とシングルポイントオブコントロールを実現。
    """

    def __init__(self, infrastructure: DIContainer):
        self.infrastructure = infrastructure
        self.overlay = RuntimeConfigOverlay()
        self.config_provider = DebugConfigProvider(self.overlay)
        self._debug_enabled = False

    def enable_debug_mode(self) -> None:
        """デバッグモードを有効化"""
        if self._debug_enabled:
            return

        # デバッグ設定を有効化
        self.config_provider.enable_debug_mode()

        # ロガーレベルを更新
        self._update_logger_levels()

        # デバッグ状態を記録
        self._debug_enabled = True

        # デバッグ開始メッセージ
        self._show_debug_notification()

    def disable_debug_mode(self) -> None:
        """デバッグモードを無効化"""
        if not self._debug_enabled:
            return

        # デバッグ設定を無効化
        self.config_provider.disable_debug_mode()

        self._debug_enabled = False

    def is_debug_enabled(self) -> bool:
        """デバッグモードが有効かチェック"""
        return self._debug_enabled

    def get_debug_config_provider(self) -> DebugConfigProvider:
        """デバッグ設定プロバイダーを取得"""
        return self.config_provider

    def _update_logger_levels(self) -> None:
        """ロガーレベルを更新

        プライベートメソッドとして実装し、外部からの直接操作を防ぐ
        """
        logger_keys = ["unified_logger", "workflow_logger", "application_logger", "logger"]

        for logger_key in logger_keys:
            try:
                if self.infrastructure.is_registered(logger_key):
                    logger = self.infrastructure.resolve(logger_key)
                    if hasattr(logger, 'set_level'):
                        logger.set_level("DEBUG")
                        # 設定成功をログに記録しない（デバッグモードでのログレベル変更は成功して当然）
                        pass
            except Exception as e:
                # 個別のロガー設定失敗は警告として表示
                # ログサービス設定失敗を另のログサービスに記録
                # 設定失敗はシステムの不具合を意味するため、エラーではなく例外で処理
                raise RuntimeError(f"ログサービス '{logger_key}' の設定に失敗: {e}") from e

    def _show_debug_notification(self) -> None:
        """デバッグ開始通知を表示"""
        # デバッグモード有効化通知をログに記録
        try:
            if self.infrastructure.is_registered("unified_logger"):
                logger = self.infrastructure.resolve("unified_logger")
                logger.info("Debug mode enabled - 詳細ログが出力されます")
        except Exception as e:
            # ログサービスが利用できない場合は例外で処理
            raise RuntimeError(f"デバッグ通知のログ出力に失敗: {e}") from e

    def log_debug_context(self, context: dict) -> None:
        """デバッグコンテキストをログ出力

        Args:
            context: デバッグ用のコンテキスト辞書
        """
        if not self._debug_enabled:
            return

        try:
            # インフラストラクチャからロガーを取得
            if self.infrastructure.is_registered("logger"):
                logger = self.infrastructure.resolve("logger")
                logger.debug("🔍 デバッグモードが有効化されました")
                logger.debug(f"🔍 実行コンテキスト: {context}")
        except Exception as e:
            # ロガーが利用できない場合はフォールバックではなく例外で処理
            raise RuntimeError(f"デバッグコンテキストのログ出力に失敗: {e}") from e



class DebugServiceFactory:
    """DebugServiceのファクトリークラス"""

    @staticmethod
    def create_debug_service(infrastructure: DIContainer) -> DebugService:
        """DebugServiceインスタンスを作成

        Args:
            infrastructure: DIコンテナ

        Returns:
            DebugServiceインスタンス
        """
        return DebugService(infrastructure)
