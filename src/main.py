if __name__ == "__main__":
    import sys
    from command_registry.user_input_parser import UserInputParser
    from command_registry.command_registry import CommandDefinitionRegistry
    from command_registry.command_executor import CommandExecutor

    args = sys.argv[1:]
    
    try:
        # パーサーとレジストリの初期化
        parser = UserInputParser()
        parse_result = parser.parse(args)  # 最初のパースでenv_jsonを取得
        
        if not parse_result.validate():
            print("エラー: 無効な引数です")
            sys.exit(1)
            
        registry = CommandDefinitionRegistry.from_env_json(parse_result.env_json, parse_result.language)
        
        # コマンド実行
        executor = CommandExecutor(parser, registry)
        executor.execute(args)
    except ValueError as e:
        print(f"エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        sys.exit(1)
