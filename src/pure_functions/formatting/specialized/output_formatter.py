"""
出力フォーマット特化機能

出力結果の表示制御とフォーマット処理を提供
純粋関数として実装し、副作用を分離
"""
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass(frozen=True)
class OutputFormatData:
    """出力フォーマット用のイミュータブルなデータ構造"""
    stdout: Optional[str] = None
    stderr: Optional[str] = None


def extract_output_data(result) -> OutputFormatData:
    """
    結果オブジェクトから出力データを抽出する純粋関数
    
    Args:
        result: 実行結果オブジェクト
        
    Returns:
        OutputFormatData: 抽出された出力データ
    """
    stdout = getattr(result, 'stdout', None)
    stderr = getattr(result, 'stderr', None)
    return OutputFormatData(stdout=stdout, stderr=stderr)


def should_show_output(request) -> bool:
    """
    リクエストオブジェクトから出力表示フラグを抽出する純粋関数
    
    Args:
        request: リクエストオブジェクト
        
    Returns:
        bool: 出力を表示するかどうか
    """
    return hasattr(request, 'show_output') and bool(request.show_output)


def format_output_content(output_data: OutputFormatData) -> str:
    """
    出力データから実際の出力テキストを生成する純粋関数
    
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


def decide_output_action(show_output: bool, output_data: OutputFormatData) -> Tuple[bool, str]:
    """
    出力アクションを決定する純粋関数
    
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


def format_with_prefix(output_data: OutputFormatData, 
                      stdout_prefix: str = "",
                      stderr_prefix: str = "[ERROR] ") -> str:
    """
    プレフィックス付きで出力をフォーマット
    
    Args:
        output_data: 出力データ
        stdout_prefix: 標準出力のプレフィックス
        stderr_prefix: 標準エラーのプレフィックス
        
    Returns:
        str: プレフィックス付きの出力テキスト
    """
    parts = []
    
    if output_data.stdout:
        if stdout_prefix:
            parts.append(f"{stdout_prefix}{output_data.stdout}")
        else:
            parts.append(output_data.stdout)
    
    if output_data.stderr:
        if stderr_prefix:
            parts.append(f"{stderr_prefix}{output_data.stderr}")
        else:
            parts.append(output_data.stderr)
    
    return "".join(parts)


def filter_output_content(output_data: OutputFormatData,
                         filter_empty: bool = True,
                         filter_whitespace: bool = False) -> OutputFormatData:
    """
    出力内容をフィルタリング
    
    Args:
        output_data: 元の出力データ
        filter_empty: 空文字列をフィルタするか
        filter_whitespace: 空白のみの文字列をフィルタするか
        
    Returns:
        OutputFormatData: フィルタ済みの出力データ
    """
    def should_filter(content: Optional[str]) -> bool:
        if content is None:
            return True
        if filter_empty and not content:
            return True
        if filter_whitespace and not content.strip():
            return True
        return False
    
    stdout = None if should_filter(output_data.stdout) else output_data.stdout
    stderr = None if should_filter(output_data.stderr) else output_data.stderr
    
    return OutputFormatData(stdout=stdout, stderr=stderr)


class OutputFormatter:
    """
    出力フォーマットのカスタマイズ可能なクラス
    
    さまざまな出力形式に対応したフォーマット機能を提供
    """
    
    def __init__(self, 
                 stdout_prefix: str = "",
                 stderr_prefix: str = "[ERROR] ",
                 filter_empty: bool = True,
                 filter_whitespace: bool = False):
        """
        Args:
            stdout_prefix: 標準出力のプレフィックス
            stderr_prefix: 標準エラーのプレフィックス
            filter_empty: 空文字列をフィルタするか
            filter_whitespace: 空白のみの文字列をフィルタするか
        """
        self.stdout_prefix = stdout_prefix
        self.stderr_prefix = stderr_prefix
        self.filter_empty = filter_empty
        self.filter_whitespace = filter_whitespace
    
    def format(self, output_data: OutputFormatData) -> str:
        """
        設定に基づいて出力をフォーマット
        
        Args:
            output_data: 出力データ
            
        Returns:
            str: フォーマット済みの出力テキスト
        """
        # フィルタリング
        filtered_data = filter_output_content(
            output_data, 
            self.filter_empty, 
            self.filter_whitespace
        )
        
        # プレフィックス付きフォーマット
        return format_with_prefix(
            filtered_data,
            self.stdout_prefix,
            self.stderr_prefix
        )
    
    def decide_action(self, show_output: bool, output_data: OutputFormatData) -> Tuple[bool, str]:
        """
        出力アクションを決定（フィルタリング込み）
        
        Args:
            show_output: 出力表示フラグ
            output_data: 出力データ
            
        Returns:
            Tuple[bool, str]: (出力すべきか, フォーマット済み出力内容)
        """
        if not show_output:
            return False, ""
        
        formatted_output = self.format(output_data)
        return bool(formatted_output), formatted_output


# Backward compatibility aliases (既存コードとの互換性)
SimpleOutputData = OutputFormatData