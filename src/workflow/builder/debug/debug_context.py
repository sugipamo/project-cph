"""デバッグコンテキスト管理（純粋関数版）"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass(frozen=True)
class DebugContext:
    """デバッグコンテキスト（不変データ構造）"""
    enabled: bool
    level: str
    start_time: datetime
    session_id: str
    metadata: Dict[str, Any]
    
    def with_metadata(self, **kwargs) -> 'DebugContext':
        """メタデータを追加した新しいコンテキストを作成（純粋関数）"""
        new_metadata = {**self.metadata, **kwargs}
        return DebugContext(
            enabled=self.enabled,
            level=self.level,
            start_time=self.start_time,
            session_id=self.session_id,
            metadata=new_metadata
        )
    
    def is_level_enabled(self, level: str) -> bool:
        """指定レベルが有効かチェック（純粋関数）"""
        if not self.enabled:
            return False
        
        level_order = {'error': 0, 'warning': 1, 'info': 2, 'debug': 3}
        current_level = level_order.get(self.level, 2)
        check_level = level_order.get(level, 2)
        
        return check_level <= current_level


def create_debug_context(enabled: bool = True, 
                        level: str = "info",
                        metadata: Optional[Dict[str, Any]] = None) -> DebugContext:
    """デバッグコンテキストを作成（純粋関数）
    
    Args:
        enabled: デバッグ有効フラグ
        level: ログレベル
        metadata: 初期メタデータ
        
    Returns:
        デバッグコンテキスト
    """
    import uuid
    
    return DebugContext(
        enabled=enabled,
        level=level,
        start_time=datetime.now(),
        session_id=str(uuid.uuid4())[:8],
        metadata=metadata or {}
    )


@dataclass(frozen=True)
class DebugEvent:
    """デバッグイベント（不変データ構造）"""
    timestamp: datetime
    level: str
    component: str
    event_type: str
    message: str
    data: Dict[str, Any]
    context: DebugContext
    
    def format_message(self) -> str:
        """メッセージをフォーマット（純粋関数）"""
        timestamp_str = self.timestamp.strftime("%H:%M:%S.%f")[:-3]
        prefix = f"[{timestamp_str}] [{self.context.session_id}] {self.level.upper()}"
        return f"{prefix} {self.component}.{self.event_type}: {self.message}"


def create_debug_event(context: DebugContext,
                      level: str,
                      component: str,
                      event_type: str,
                      message: str,
                      **data) -> DebugEvent:
    """デバッグイベントを作成（純粋関数）
    
    Args:
        context: デバッグコンテキスト
        level: ログレベル
        component: コンポーネント名
        event_type: イベントタイプ
        message: メッセージ
        **data: 追加データ
        
    Returns:
        デバッグイベント
    """
    return DebugEvent(
        timestamp=datetime.now(),
        level=level,
        component=component,
        event_type=event_type,
        message=message,
        data=data,
        context=context
    )


def filter_debug_events(events: List[DebugEvent],
                       level: Optional[str] = None,
                       component: Optional[str] = None,
                       event_type: Optional[str] = None) -> List[DebugEvent]:
    """デバッグイベントをフィルタ（純粋関数）
    
    Args:
        events: フィルタ対象のイベントリスト
        level: フィルタするレベル
        component: フィルタするコンポーネント
        event_type: フィルタするイベントタイプ
        
    Returns:
        フィルタされたイベントリスト
    """
    filtered = events
    
    if level:
        filtered = [e for e in filtered if e.level == level]
    
    if component:
        filtered = [e for e in filtered if e.component == component]
        
    if event_type:
        filtered = [e for e in filtered if e.event_type == event_type]
    
    return filtered


def aggregate_debug_statistics(events: List[DebugEvent]) -> Dict[str, Any]:
    """デバッグイベントの統計を集計（純粋関数）
    
    Args:
        events: 集計対象のイベントリスト
        
    Returns:
        統計情報辞書
    """
    if not events:
        return {
            'total_events': 0,
            'by_level': {},
            'by_component': {},
            'by_event_type': {},
            'duration_seconds': 0
        }
    
    level_counts = {}
    component_counts = {}
    event_type_counts = {}
    
    for event in events:
        level_counts[event.level] = level_counts.get(event.level, 0) + 1
        component_counts[event.component] = component_counts.get(event.component, 0) + 1
        event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1
    
    # 期間計算
    start_time = min(e.timestamp for e in events)
    end_time = max(e.timestamp for e in events)
    duration = (end_time - start_time).total_seconds()
    
    return {
        'total_events': len(events),
        'by_level': level_counts,
        'by_component': component_counts,
        'by_event_type': event_type_counts,
        'duration_seconds': duration,
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat()
    }