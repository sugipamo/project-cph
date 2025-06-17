"""OutputManager のシンプルな出力処理を純粋関数として実装
既存のAPIとの互換性を保つための軽量実装
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OutputData:
    """出力データ構造"""
    stdout: Optional[str] = None
    stderr: Optional[str] = None


def extract_output_data(result) -> OutputData:
    """結果オブジェクトから出力データを抽出する純粋関数

    Args:
        result: 実行結果オブジェクト

    Returns:
        OutputData: 抽出された出力データ
    """
    stdout = getattr(result, 'stdout', None)
    stderr = getattr(result, 'stderr', None)
    return OutputData(stdout=stdout, stderr=stderr)


def should_show_output(request) -> bool:
    """リクエストオブジェクトから出力表示フラグを抽出する純粋関数

    Args:
        request: リクエストオブジェクト

    Returns:
        bool: 出力を表示するかどうか
    """
    return hasattr(request, 'show_output') and bool(request.show_output)


def format_output_content(output_data: OutputData) -> str:
    """出力データから実際の出力テキストを生成する純粋関数

    Args:
        output_data: 出力データ

    Returns:
        str: フォーマットされた出力テキスト
    """
    parts = []

    if output_data.stdout:
        parts.append(output_data.stdout)

    if output_data.stderr:
        parts.append(output_data.stderr)

    return "".join(parts)


def decide_output_action(show_output: bool, output_data: OutputData) -> tuple[bool, str]:
    """出力アクションを決定する純粋関数

    Args:
        show_output: 出力表示フラグ
        output_data: 出力データ

    Returns:
        Tuple[bool, str]: (出力すべきか, 出力内容)
    """
    if not show_output:
        return False, ""

    if not output_data.stdout and not output_data.stderr:
        return False, ""

    output_text = format_output_content(output_data)
    return bool(output_text), output_text
