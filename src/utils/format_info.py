import re
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from src.application.color_manager import apply_color
from src.utils.types import LogFormatType
if TYPE_CHECKING:
    from src.utils.types import LogFormatType
else:
    pass

@dataclass
class FormatInfo:
    formattype: 'LogFormatType' = None
    color: Optional[str] = None
    bold: bool = False
    indent: int = 0

    def __post_init__(self):
        if self.formattype is None:
            object.__setattr__(self, 'formattype', LogFormatType.PLAIN)

    def to_dict(self):
        return {'formattype': self.formattype.name, 'color': self.color, 'bold': self.bold}

    @classmethod
    def from_dict(cls, d):
        return cls(formattype=LogFormatType[d['formattype']], color=d['color'], bold=d['bold'])

    def _apply_color(self, text: str) -> str:
        if self.color:
            return apply_color(text, self.color)
        return text

    def _apply_bold(self, text: str) -> str:
        if self.bold:
            return f'\x1b[1m{text}\x1b[0m'
        return text

    def _remove_ansi(self, text: str) -> str:
        ansi_escape = re.compile('\\x1B\\[[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', text)

    def apply(self, text: str) -> str:
        if self.indent > 0:
            text = '    ' * self.indent + text
        if self.formattype == LogFormatType.CUSTOM:
            text = self._apply_color(text)
            text = self._apply_bold(text)
            return text
        if self.formattype == LogFormatType.RAW:
            return text
        return self._remove_ansi(text)