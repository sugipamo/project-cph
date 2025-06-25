"""設定関連のバリデーションユーティリティ

from src.core.configuration.config_resolver import resolve_best
ConfigNode/resolverを使用した設定データの検証と取得を行います。
"""


def get_steps_from_resolver(resolver, language: str, command_type: str) -> list:
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
