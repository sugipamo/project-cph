"""
ロギング機能
実行過程の詳細記録とデバッグ支援
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import sys

class ReorganizerLogger:
    """依存関係整理ツール専用ロガー"""
    
    def __init__(self, 
                 log_level: str = "INFO",
                 log_file: Optional[Path] = None,
                 enable_console: bool = True):
        """
        Args:
            log_level: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: ログファイルパス（Noneの場合はファイル出力なし）
            enable_console: コンソール出力を有効にするか
        """
        self.logger = logging.getLogger("import_dependency_reorganizer")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # 既存のハンドラをクリア
        self.logger.handlers.clear()
        
        # フォーマッタ
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # コンソールハンドラ
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # ファイルハンドラ
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # 実行ログ記録用
        self.execution_log: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
    
    def debug(self, message: str, **kwargs) -> None:
        """デバッグログ"""
        self.logger.debug(message, extra=kwargs)
        self._record_event("DEBUG", message, kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """情報ログ"""
        self.logger.info(message, extra=kwargs)
        self._record_event("INFO", message, kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """警告ログ"""
        self.logger.warning(message, extra=kwargs)
        self._record_event("WARNING", message, kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """エラーログ"""
        self.logger.error(message, extra=kwargs)
        self._record_event("ERROR", message, kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """クリティカルエラーログ"""
        self.logger.critical(message, extra=kwargs)
        self._record_event("CRITICAL", message, kwargs)
    
    def _record_event(self, level: str, message: str, details: Dict[str, Any]) -> None:
        """イベントを実行ログに記録"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "details": details,
            "elapsed_seconds": (datetime.now() - self.start_time).total_seconds()
        }
        self.execution_log.append(event)
    
    def log_phase_start(self, phase: str, description: str) -> None:
        """フェーズ開始をログ"""
        self.info(f"=== {phase} 開始 ===", phase=phase, description=description)
    
    def log_phase_end(self, phase: str, success: bool, duration: float) -> None:
        """フェーズ終了をログ"""
        status = "成功" if success else "失敗"
        self.info(
            f"=== {phase} {status} ({duration:.2f}秒) ===",
            phase=phase,
            success=success,
            duration=duration
        )
    
    def log_file_operation(self, operation: str, file_path: Path, 
                          success: bool, details: Optional[Dict] = None) -> None:
        """ファイル操作をログ"""
        level = "info" if success else "error"
        message = f"{operation}: {file_path} - {'成功' if success else '失敗'}"
        
        log_details = {
            "operation": operation,
            "file_path": str(file_path),
            "success": success
        }
        if details:
            log_details.update(details)
        
        getattr(self, level)(message, **log_details)
    
    def log_import_analysis(self, file_path: Path, import_count: int, 
                           dependencies: List[str]) -> None:
        """インポート解析結果をログ"""
        self.debug(
            f"インポート解析: {file_path.name}",
            file_path=str(file_path),
            import_count=import_count,
            dependencies=dependencies[:5]  # 最初の5個
        )
    
    def log_dependency_depth(self, module: str, depth: int, 
                            dependencies: List[str]) -> None:
        """依存深度計算結果をログ"""
        self.debug(
            f"依存深度: {module} = {depth}",
            module=module,
            depth=depth,
            direct_dependencies=dependencies
        )
    
    def log_move_plan(self, move_plan: Dict[Path, Path]) -> None:
        """移動計画をログ"""
        self.info(
            f"移動計画作成: {len(move_plan)}ファイル",
            file_count=len(move_plan),
            sample_moves=[
                {"from": str(k), "to": str(v)} 
                for k, v in list(move_plan.items())[:5]
            ]
        )
    
    def log_import_update(self, file_path: Path, original: str, 
                         updated: str, line_number: int) -> None:
        """インポート更新をログ"""
        self.debug(
            f"インポート更新: {file_path.name}:{line_number}",
            file_path=str(file_path),
            line_number=line_number,
            original_import=original,
            updated_import=updated
        )
    
    def save_execution_log(self, output_path: Path) -> None:
        """実行ログをJSONファイルに保存"""
        log_data = {
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_duration": (datetime.now() - self.start_time).total_seconds(),
            "event_count": len(self.execution_log),
            "events": self.execution_log
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        self.info(f"実行ログを保存: {output_path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """ログ統計を取得"""
        level_counts = {}
        for event in self.execution_log:
            level = event["level"]
            level_counts[level] = level_counts.get(level, 0) + 1
        
        return {
            "total_events": len(self.execution_log),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "level_counts": level_counts,
            "error_count": level_counts.get("ERROR", 0) + level_counts.get("CRITICAL", 0),
            "warning_count": level_counts.get("WARNING", 0)
        }


# グローバルロガーインスタンス（遅延初期化）
_logger: Optional[ReorganizerLogger] = None

def get_logger() -> ReorganizerLogger:
    """グローバルロガーを取得（必要に応じて初期化）"""
    global _logger
    if _logger is None:
        _logger = ReorganizerLogger()
    return _logger

def setup_logger(log_level: str = "INFO", 
                log_file: Optional[Path] = None,
                enable_console: bool = True) -> ReorganizerLogger:
    """ロガーを設定"""
    global _logger
    _logger = ReorganizerLogger(log_level, log_file, enable_console)
    return _logger