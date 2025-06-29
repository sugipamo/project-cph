"""Tests for ASTAnalyzer

Testing the AST analysis functionality for Python code
"""
import ast
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.infrastructure.ast_analyzer import ASTAnalyzer, ImportInfo
from src.infrastructure.module_info import ExportedSymbol


class TestASTAnalyzer:
    """Tests for ASTAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        """Create an ASTAnalyzer instance"""
        return ASTAnalyzer()

    def test_parse_source_valid_code(self, analyzer):
        """Test parsing valid Python source code"""
        # Arrange
        source_code = """
import os
from typing import List

def hello():
    pass

class MyClass:
    pass
"""
        # Act
        tree = analyzer.parse_source(source_code, "<test>")

        # Assert
        assert tree is not None
        assert isinstance(tree, ast.AST)
        assert analyzer._source_code == source_code
        assert analyzer._tree == tree

    def test_parse_source_invalid_code(self, analyzer):
        """Test parsing invalid Python source code"""
        # Arrange
        source_code = "def invalid syntax("

        # Act
        tree = analyzer.parse_source(source_code, "<test>")

        # Assert
        assert tree is None

    def test_parse_file_valid(self, analyzer, tmp_path):
        """Test parsing a valid Python file"""
        # Arrange
        file_path = tmp_path / "test.py"
        file_content = "def test_function():\n    return 42"
        file_path.write_text(file_content)

        # Act
        tree = analyzer.parse_file(file_path)

        # Assert
        assert tree is not None
        assert isinstance(tree, ast.AST)
        assert analyzer._source_code == file_content

    def test_parse_file_syntax_error(self, analyzer, tmp_path):
        """Test parsing a file with syntax error"""
        # Arrange
        file_path = tmp_path / "test.py"
        file_path.write_text("invalid python syntax(")

        # Act
        tree = analyzer.parse_file(file_path)

        # Assert
        assert tree is None

    def test_parse_file_unicode_error(self, analyzer, tmp_path):
        """Test parsing a file with unicode error"""
        # Arrange
        file_path = tmp_path / "test.py"
        # Write invalid UTF-8 bytes
        file_path.write_bytes(b'\x80\x81\x82\x83')

        # Act
        tree = analyzer.parse_file(file_path)

        # Assert
        assert tree is None

    def test_extract_imports_no_tree(self, analyzer):
        """Test extracting imports when no tree is parsed"""
        # Act
        imports = analyzer.extract_imports()

        # Assert
        assert imports == []

    def test_extract_imports_regular_imports(self, analyzer):
        """Test extracting regular import statements"""
        # Arrange
        source_code = """
import os
import sys
import json
"""
        analyzer.parse_source(source_code, "<test>")

        # Act
        imports = analyzer.extract_imports()

        # Assert
        assert len(imports) == 3
        assert imports[0].module == 'os'
        assert imports[0].is_from_import is False
        assert imports[0].names == []
        assert imports[0].level == 0
        assert imports[0].line_number == 2

    def test_extract_imports_from_imports(self, analyzer):
        """Test extracting from-import statements"""
        # Arrange
        source_code = """
from typing import List, Dict
from os.path import join, exists
from . import utils
from ..core import base
"""
        analyzer.parse_source(source_code, "<test>")

        # Act
        imports = analyzer.extract_imports()

        # Assert
        assert len(imports) == 4
        
        # Check first import
        assert imports[0].module == 'typing'
        assert imports[0].is_from_import is True
        assert imports[0].names == ['List', 'Dict']
        assert imports[0].level == 0
        
        # Check relative imports
        assert imports[2].module == ''
        assert imports[2].level == 1
        assert imports[3].module == 'core'
        assert imports[3].level == 2

    def test_extract_exported_symbols_no_tree(self, analyzer):
        """Test extracting symbols when no tree is parsed"""
        # Act
        symbols = analyzer.extract_exported_symbols()

        # Assert
        assert symbols == set()

    def test_extract_exported_symbols_classes(self, analyzer):
        """Test extracting class definitions"""
        # Arrange
        source_code = '''
class PublicClass:
    """A public class"""
    pass

class _PrivateClass:
    """A private class"""
    pass
'''
        analyzer.parse_source(source_code, "<test>")

        # Act
        symbols = analyzer.extract_exported_symbols()

        # Assert
        assert len(symbols) == 2
        public_class = next(s for s in symbols if s.name == 'PublicClass')
        assert public_class.symbol_type == 'class'
        assert public_class.is_public is True
        assert public_class.docstring == 'A public class'
        
        private_class = next(s for s in symbols if s.name == '_PrivateClass')
        assert private_class.symbol_type == 'class'
        assert private_class.is_public is False

    def test_extract_exported_symbols_functions(self, analyzer):
        """Test extracting function definitions"""
        # Arrange
        source_code = '''
def public_function():
    """A public function"""
    pass

def _private_function():
    pass

async def async_function():
    """An async function"""
    pass
'''
        analyzer.parse_source(source_code, "<test>")

        # Act
        symbols = analyzer.extract_exported_symbols()

        # Assert
        assert len(symbols) == 3
        
        public_func = next(s for s in symbols if s.name == 'public_function')
        assert public_func.symbol_type == 'function'
        assert public_func.is_public is True
        
        async_func = next(s for s in symbols if s.name == 'async_function')
        assert async_func.symbol_type == 'async_function'
        assert async_func.docstring == 'An async function'

    def test_extract_exported_symbols_variables(self, analyzer):
        """Test extracting module-level variables"""
        # Arrange
        source_code = '''
MODULE_CONSTANT = 42
_private_var = "secret"

def function():
    local_var = 10  # This should not be extracted
'''
        analyzer.parse_source(source_code, "<test>")

        # Act
        symbols = analyzer.extract_exported_symbols()

        # Assert
        variable_symbols = {s for s in symbols if s.symbol_type == 'variable'}
        assert len(variable_symbols) == 2
        
        public_var = next(s for s in variable_symbols if s.name == 'MODULE_CONSTANT')
        assert public_var.is_public is True
        
        private_var = next(s for s in variable_symbols if s.name == '_private_var')
        assert private_var.is_public is False

    def test_extract_exported_symbols_with_all(self, analyzer):
        """Test extracting symbols with __all__ defined"""
        # Arrange
        source_code = '''
__all__ = ['public_function', 'ExportedClass']

def public_function():
    pass

def not_exported():
    pass

class ExportedClass:
    pass

class NotExported:
    pass
'''
        analyzer.parse_source(source_code, "<test>")

        # Act
        symbols = analyzer.extract_exported_symbols()

        # Assert
        # Should include __all__ members and private members
        symbol_names = {s.name for s in symbols}
        assert 'public_function' in symbol_names
        assert 'ExportedClass' in symbol_names
        assert 'not_exported' not in symbol_names
        assert 'NotExported' not in symbol_names

    def test_find_broken_imports_no_broken(self, analyzer):
        """Test finding broken imports when all are available"""
        # Arrange
        source_code = '''
import os
from typing import List
'''
        analyzer.parse_source(source_code, "<test>")
        available_modules = {'os', 'typing'}

        # Act
        broken = analyzer.find_broken_imports(available_modules)

        # Assert
        assert len(broken) == 0

    def test_find_broken_imports_with_broken(self, analyzer):
        """Test finding broken imports"""
        # Arrange
        source_code = '''
import nonexistent_module
from fake_package import something
'''
        analyzer.parse_source(source_code, "<test>")
        available_modules = {'os', 'sys'}

        # Act
        broken = analyzer.find_broken_imports(available_modules)

        # Assert
        assert len(broken) == 2
        assert broken[0][0].module == 'nonexistent_module'
        assert "not found" in broken[0][1]
        assert broken[1][0].module == 'fake_package'

    def test_find_broken_imports_partial_match(self, analyzer):
        """Test finding broken imports with partial module paths"""
        # Arrange
        source_code = '''
from os.path import join
from fake.sub.module import something
'''
        analyzer.parse_source(source_code, "<test>")
        available_modules = {'os', 'os.path', 'fake'}  # fake.sub is not available

        # Act
        broken = analyzer.find_broken_imports(available_modules)

        # Assert
        # Since 'fake' is available, the import is considered valid (partial match)
        assert len(broken) == 0
        
    def test_find_broken_imports_no_partial_match(self, analyzer):
        """Test finding broken imports with no partial matches"""
        # Arrange
        source_code = '''
from totally.fake.module import something
'''
        analyzer.parse_source(source_code, "<test>")
        available_modules = {'os', 'sys'}  # no 'totally' module

        # Act
        broken = analyzer.find_broken_imports(available_modules)

        # Assert
        assert len(broken) == 1
        assert broken[0][0].module == 'totally.fake.module'

    def test_extract_all_names_list(self, analyzer):
        """Test _extract_all_names with list node"""
        # Arrange
        source_code = "__all__ = ['func1', 'func2']"
        tree = ast.parse(source_code)
        list_node = tree.body[0].value

        # Act
        names = analyzer._extract_all_names(list_node)

        # Assert
        assert names == {'func1', 'func2'}

    def test_extract_all_names_non_list(self, analyzer):
        """Test _extract_all_names with non-list node"""
        # Arrange
        source_code = "__all__ = 'not_a_list'"
        tree = ast.parse(source_code)
        str_node = tree.body[0].value

        # Act
        names = analyzer._extract_all_names(str_node)

        # Assert
        assert names is None

    def test_is_module_level_assignment(self, analyzer):
        """Test _is_module_level_assignment"""
        # Arrange
        source_code = '''
x = 1  # module level

def func():
    y = 2  # not module level
'''
        analyzer.parse_source(source_code, "<test>")
        
        # Get the assignment nodes
        module_assign = analyzer._tree.body[0]
        
        # Act & Assert
        assert analyzer._is_module_level_assignment(module_assign) is True
        
        # Test when tree is not set
        analyzer._tree = None
        assert analyzer._is_module_level_assignment(module_assign) is False