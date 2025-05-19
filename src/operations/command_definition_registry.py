from typing import Dict, Optional
from .command_definition import CommandDefinition

class CommandDefinitionRegistry:
    """
    コマンド定義を管理するレジストリ
    """
    def __init__(self):
        self._commands: Dict[str, CommandDefinition] = {}

    @classmethod
    def from_env_json(cls, env_json: dict, language: str) -> 'CommandDefinitionRegistry':
        """
        env.jsonからコマンド定義を読み込んでレジストリを生成する
        
        Args:
            env_json: 環境設定JSON
            language: 言語名
            
        Returns:
            CommandDefinitionRegistry
        """
        registry = cls()
        if language not in env_json:
            return registry

        lang_config = env_json[language]
        commands = lang_config.get('commands', {})
        
        for cmd_name, cmd_config in commands.items():
            registry.register_command(
                CommandDefinition(
                    name=cmd_name,
                    description=cmd_config.get('description', ''),
                    run=cmd_config.get('run', []),
                    options=cmd_config.get('options', {})
                )
            )
        
        return registry

    def register_command(self, command: CommandDefinition):
        """
        コマンドを登録する
        
        Args:
            command: 登録するコマンド定義
        """
        self._commands[command.name] = command

    def find_command_definition(self, command_name: str) -> Optional[CommandDefinition]:
        """
        コマンド名からコマンド定義を検索する
        
        Args:
            command_name: コマンド名
            
        Returns:
            Optional[CommandDefinition]: 見つかったコマンド定義。見つからない場合はNone
        """
        return self._commands.get(command_name) 