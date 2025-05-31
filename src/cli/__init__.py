"""
Command-line interface package
"""

# Input parsing
try:
    from ..context.user_input_parser import UserInputParser
    from ..context.parsers import SystemInfoManager, ValidationService, InputParser
    parser_exports = [
        'UserInputParser', 'SystemInfoManager', 
        'ValidationService', 'InputParser'
    ]
except ImportError:
    parser_exports = []

# Main CLI entry point
try:
    from ..main import main
    main_exports = ['main']
except ImportError:
    main_exports = []

__all__ = parser_exports + main_exports