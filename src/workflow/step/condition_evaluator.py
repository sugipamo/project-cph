"""Step実行条件（when句）の評価を行うモジュール"""
import os
import re
import subprocess
from typing import Dict, Optional


def evaluate_when_condition(when_clause: str, context: Dict[str, str]) -> bool:
    """when条件を評価して実行可否を判定する
    
    Args:
        when_clause: "test -d {path}" 形式の条件文字列
        context: テンプレート変数を展開するためのコンテキスト辞書
        
    Returns:
        bool: 条件が真の場合True、偽の場合False
        
    Raises:
        ValueError: 無効な条件文字列の場合
    """
    if not when_clause:
        return True  # when条件がない場合は常に実行
    
    # テンプレート変数を展開
    expanded_clause = when_clause
    for key, value in context.items():
        placeholder = f'{{{key}}}'
        if placeholder in expanded_clause:
            expanded_clause = expanded_clause.replace(placeholder, str(value))
    
    # セキュリティチェック - 危険な文字を検出
    if any(char in expanded_clause for char in [';', '|', '&', '$', '`', '(', ')', '\n']):
        raise ValueError(f"Unsafe characters detected in when clause: {expanded_clause}")
    
    # "test" で始まることを確認
    if not expanded_clause.startswith("test "):
        raise ValueError(f"when clause must start with 'test': {expanded_clause}")
    
    # testコマンドのパースと実行
    return _execute_test_command(expanded_clause)


def _execute_test_command(test_command: str) -> bool:
    """testコマンドを安全に実行する
    
    Args:
        test_command: "test -d /path/to/dir" 形式のコマンド
        
    Returns:
        bool: testコマンドの結果
    """
    # コマンドを分割
    parts = test_command.split()
    if len(parts) < 2:
        return False
    
    # "test" を除去
    test_args = parts[1:]
    
    # 否定の処理
    negate = False
    if test_args[0] == "!":
        negate = True
        test_args = test_args[1:]
    
    if len(test_args) < 2:
        return False
    
    flag = test_args[0]
    path = test_args[1]
    
    # Pythonで各フラグを評価
    result = False
    
    if flag == "-e":  # exists
        result = os.path.exists(path)
    elif flag == "-f":  # is file
        result = os.path.isfile(path)
    elif flag == "-d":  # is directory
        result = os.path.isdir(path)
    elif flag == "-s":  # exists and not empty
        result = os.path.exists(path) and os.path.getsize(path) > 0
    elif flag == "-r":  # readable
        result = os.access(path, os.R_OK)
    elif flag == "-w":  # writable
        result = os.access(path, os.W_OK)
    elif flag == "-x":  # executable
        result = os.access(path, os.X_OK)
    else:
        # 未対応のフラグはsubprocessで実行（より安全な方法）
        try:
            # testコマンドを直接実行（シェル経由ではない）
            process = subprocess.run(["test"] + test_args, capture_output=True)
            result = process.returncode == 0
        except Exception:
            result = False
    
    # 否定の適用
    return not result if negate else result


def validate_when_clause(when_clause: str) -> Optional[str]:
    """when句の妥当性を検証する
    
    Args:
        when_clause: 検証する条件文字列
        
    Returns:
        Optional[str]: エラーメッセージ（妥当な場合はNone）
    """
    if not when_clause:
        return None
    
    # "test"で始まるかチェック
    if not when_clause.startswith("test "):
        return "when clause must start with 'test'"
    
    # 危険な文字のチェック
    dangerous_chars = [';', '|', '&', '$', '`', '(', ')', '\n']
    for char in dangerous_chars:
        if char in when_clause:
            return f"Unsafe character '{char}' detected in when clause"
    
    # 基本的なパターンマッチング
    # 許可されるパターン: test [-!] -[defrsw] {path}
    pattern = r'^test\s+(!?\s*)?-[defrsw]\s+\{[\w_]+\}$'
    if not re.match(pattern, when_clause):
        return "Invalid when clause format. Expected: 'test -flag {path}' or 'test ! -flag {path}'"
    
    return None