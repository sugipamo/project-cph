from typing import Optional


def validate_execution_context_data(
    command_type: str,
    language: str,
    contest_name: str,
    problem_name: str,
    env_json: dict
) -> tuple[bool, Optional[str]]:
    """ExecutionContextの基本的なバリデーションを行う純粋関数

    Args:
        command_type: コマンドタイプ
        language: 言語
        contest_name: コンテスト名
        problem_name: 問題名
        env_json: 環境設定JSON

    Returns:
        Tuple[bool, Optional[str]]: (バリデーション結果, エラーメッセージ)
    """
    # 必須項目の存在チェック
    missing_fields = []
    if not command_type:
        missing_fields.append("コマンド")
    if not language:
        missing_fields.append("言語")
    if not contest_name:
        missing_fields.append("コンテスト名")
    if not problem_name:
        missing_fields.append("問題名")

    if missing_fields:
        return False, f"以下の項目が指定されていません: {', '.join(missing_fields)}"

    # env_jsonの存在チェック
    if not env_json:
        return False, "環境設定ファイル(env.json)が見つかりません"

    # 言語がenv_jsonに存在するかチェック
    if language not in env_json:
        return False, f"指定された言語 '{language}' は環境設定ファイルに存在しません"

    return True, None


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
    from src.context.resolver.config_resolver import resolve_best

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
        raise ValueError(f"stepsの取得に失敗しました: {e}")
