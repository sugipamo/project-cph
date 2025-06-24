"""設定関連のバリデーションユーティリティ

ConfigNode/resolverを使用した設定データの検証と取得を行います。
"""


def get_steps_from_resolver(resolver: Dict, language: str, command_type: str) -> Optional:
    """resolverから指定された言語とコマンドタイプのstepsを取得する純粋関数

    Args:
        resolver: ConfigResolverインスタンス
        language: 言語
        command_type: コマンドタイプ

    Returns:
        list: ステップのConfigNodeリスト

    Raises:
        ValueError: stepsが見つからない場合
    """
    from src.configuration.resolver.config_resolver import resolve_best

    try:
        steps_node = resolve_best(resolver, [language, "commands", command_type, "steps"])
        if not steps_node:
            raise ValueError("stepsが見つかりません")

        # steps配列の各要素のConfigNodeを返す
        step_nodes = []
        for child in steps_node.next_nodes:
            if isinstance(child.key, int):  # 配列のインデックス
                step_nodes.append(child)

        # インデックス順にソート
        step_nodes.sort(key=lambda n: n.key)
        return step_nodes
    except Exception as e:
        raise ValueError(f"stepsの取得に失敗しました: {e}") from e
