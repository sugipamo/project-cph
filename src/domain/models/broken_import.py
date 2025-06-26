from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, List


class ImportType(Enum):
    ABSOLUTE = "absolute"
    RELATIVE = "relative"
    FROM_IMPORT = "from_import"
    IMPORT = "import"


@dataclass(frozen=True)
class BrokenImport:
    file_path: Path
    line_number: int
    import_statement: str
    import_type: ImportType
    module_path: str
    imported_names: List[str]
    relative_level: int = 0
    error_message: Optional[str] = None
    
    @property
    def is_relative(self) -> bool:
        return self.import_type == ImportType.RELATIVE or self.relative_level > 0
    
    @property
    def estimated_absolute_path(self) -> Optional[str]:
        if not self.is_relative:
            return self.module_path
        
        parent_parts = list(self.file_path.parent.parts)
        
        for _ in range(self.relative_level):
            if parent_parts:
                parent_parts.pop()
        
        if self.module_path:
            parent_parts.extend(self.module_path.split('.'))
        
        return '.'.join(parent_parts) if parent_parts else None
    
    def __str__(self) -> str:
        return f"{self.file_path}:{self.line_number} - {self.import_statement}"