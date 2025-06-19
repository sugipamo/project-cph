"""Main entry point for the CPH application
"""
import sys

from src.cli.cli_app import main

if __name__ == "__main__":
    main(sys.argv[1:], sys.exit)
