import sys
from src.commands import CommandParser

def main():
    args = sys.argv[1:]
    parser = CommandParser()
    parser.parse(args)

if __name__ == "__main__":
    main() 