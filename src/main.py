if __name__ == "__main__":
    import sys
    from command_registry.user_input_parser import UserInputParser
    from command_registry.command_registry import CommandDefinitionRegistry
    from command_registry.command_executor import CommandExecutor

    args = sys.argv[1:]
    
    # パーサーとレジストリの初期化
    parser = UserInputParser()
    parse_result = parser.parse(args)  # 最初のパースでenv_jsonを取得
    
    print("=== Parse Result ===")
    print(f"command: {parse_result.command}")
    print(f"language: {parse_result.language}")
    print(f"env_type: {parse_result.env_type}")
    print(f"contest_name: {parse_result.contest_name}")
    print(f"problem_name: {parse_result.problem_name}")
    print(f"env_json exists: {parse_result.env_json is not None}")
    print("==================")
    
    if not parse_result.validate():
        print("エラー: 無効な引数です")
        sys.exit(1)
        
    registry = CommandDefinitionRegistry.from_env_json(parse_result.env_json, parse_result.language)
    
    # コマンド実行
    executor = CommandExecutor(parser, registry)
    executor.execute(args)
