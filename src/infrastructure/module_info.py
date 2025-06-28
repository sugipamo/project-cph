from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class ExportedSymbol:
    name: str
    symbol_type: str
    line_number: int
    is_public: bool = True
    docstring: Optional[str] = None

    def __hash__(self) -> int:
        return hash((self.name, self.symbol_type))


@dataclass
class ModuleInfo:
    file_path: Path
    module_path: str
    exported_symbols: Set[ExportedSymbol] = field(default_factory=set)
    imported_modules: Set[str] = field(default_factory=set)
    dependencies: Set[Path] = field(default_factory=set)
    last_modified: Optional[datetime] = None
    parse_errors: List[str] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)

    @property
    def is_package(self) -> bool:
        return self.file_path.name == "__init__.py"

    @property
    def package_path(self) -> Optional[Path]:
        if self.is_package:
            return self.file_path.parent
        return None

    @property
    def exported_names(self) -> Set[str]:
        return {symbol.name for symbol in self.exported_symbols}

    def has_symbol(self, name: str) -> bool:
        return name in self.exported_names

    def get_symbol(self, name: str) -> Optional[ExportedSymbol]:
        for symbol in self.exported_symbols:
            if symbol.name == name:
                return symbol
        return None

    def __hash__(self) -> int:
        return hash(str(self.file_path))
