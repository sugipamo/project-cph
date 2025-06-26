"""Time adapter to bridge TimeProvider and TimeInterface."""
from src.infrastructure.time_provider import TimeProvider
from src.operations.interfaces.time_interface import TimeInterface


class TimeAdapter(TimeInterface):
    """Adapter to bridge TimeProvider and TimeInterface."""

    def __init__(self, time_provider: TimeProvider):
        self._time_provider = time_provider

    def current_time(self) -> float:
        """Get current time as timestamp."""
        return self._time_provider.now()

    def sleep(self, seconds: float) -> None:
        """Sleep for specified seconds."""
        self._time_provider.sleep(seconds)
