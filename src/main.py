if __name__ == "__main__":
    import sys
    from command_registry.user_input_parser import UserInputParser

    args = sys.argv[1:]
    parser = UserInputParser()
    parser.parse(args)
